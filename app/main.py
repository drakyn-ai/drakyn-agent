"""Main FastAPI application."""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
import json
from datetime import timedelta

import app.config as config
import app.database as db
import app.auth as auth
from app.claude_client import stream_claude_response

# Initialize FastAPI app
app = FastAPI(title="Drakyn Agent")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# OAuth setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    server_metadata_url=config.GOOGLE_DISCOVERY_URL,
    client_kwargs={'scope': 'openid email profile'}
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await db.init_db()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - shows login or redirects to chat."""
    user = auth.get_user_from_cookie(request)
    if user:
        return RedirectResponse(url="/chat")
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login")
async def login(request: Request):
    """Initiate Google OAuth login."""
    redirect_uri = config.REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    """Handle OAuth callback from Google."""
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')

        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        email = user_info.get('email')
        name = user_info.get('name')

        # Check if user is allowed
        if config.ALLOWED_EMAIL and email != config.ALLOWED_EMAIL:
            return HTMLResponse(
                "<h1>Access Denied</h1><p>You are not authorized to access this application.</p>",
                status_code=403
            )

        # Create access token
        access_token = auth.create_access_token(
            data={"email": email, "name": name},
            expires_delta=timedelta(days=7)
        )

        # Redirect to chat with token in cookie
        response = RedirectResponse(url="/chat")
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        return response

    except Exception as e:
        return HTMLResponse(f"<h1>Authentication Error</h1><p>{str(e)}</p>", status_code=400)

@app.get("/logout")
async def logout():
    """Logout user."""
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Chat interface (requires authentication)."""
    user = auth.get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})

@app.get("/api/conversations")
async def get_conversations(request: Request):
    """Get all conversations for the current user."""
    user = auth.get_user_from_cookie(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conversations = await db.get_user_conversations(user["email"])
    return {"conversations": conversations}

@app.post("/api/conversations")
async def create_conversation(request: Request):
    """Create a new conversation."""
    user = auth.get_user_from_cookie(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    data = await request.json()
    title = data.get("title", "New Conversation")
    conversation_id = await db.create_conversation(user["email"], title)
    return {"conversation_id": conversation_id}

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: int, request: Request):
    """Get messages from a specific conversation."""
    user = auth.get_user_from_cookie(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    messages = await db.get_conversation_messages(conversation_id)
    return {"messages": messages}

@app.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: int):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()

    try:
        # Get user from initial message (client sends token)
        initial_data = await websocket.receive_json()
        token = initial_data.get("token")

        if not token:
            await websocket.close(code=1008)
            return

        try:
            user_payload = auth.verify_token(token)
            user_email = user_payload.get("email")
        except:
            await websocket.close(code=1008)
            return

        # Load conversation history
        history = await db.get_conversation_messages(conversation_id)
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]

        # Chat loop
        while True:
            # Receive message from user
            data = await websocket.receive_json()
            user_message = data.get("message")

            if not user_message:
                continue

            # Save user message
            await db.add_message(conversation_id, "user", user_message)
            messages.append({"role": "user", "content": user_message})

            # Send acknowledgment
            await websocket.send_json({"type": "user_message", "content": user_message})

            # Stream Claude's response
            assistant_response = ""
            await websocket.send_json({"type": "start"})

            async for chunk in stream_claude_response(messages):
                assistant_response += chunk
                await websocket.send_json({"type": "chunk", "content": chunk})

            await websocket.send_json({"type": "end"})

            # Save assistant message
            await db.add_message(conversation_id, "assistant", assistant_response)
            messages.append({"role": "assistant", "content": assistant_response})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=1011)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
