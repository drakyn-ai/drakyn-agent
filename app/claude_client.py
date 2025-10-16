"""Claude API client with streaming support."""
from anthropic import AsyncAnthropic
from typing import List, Dict, AsyncGenerator, Optional
import app.config as config
import logging

logger = logging.getLogger(__name__)
client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

def get_gmail_tools() -> List[Dict]:
    """Define Gmail tools for Claude API."""
    return [
        {
            "name": "list_emails",
            "description": "List emails from the user's Gmail inbox. Returns a list of recent emails with metadata like sender, subject, date, and snippet. Useful for getting an overview of recent emails.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to return (default 10, max 50)",
                        "default": 10
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional Gmail search query. Examples: 'is:unread', 'from:example@gmail.com', 'subject:meeting', 'newer_than:7d'",
                        "default": ""
                    }
                },
                "required": []
            }
        },
        {
            "name": "read_email",
            "description": "Read the full content of a specific email by its ID. Returns the complete email including body text, sender, subject, and other details.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "The Gmail message ID (obtained from list_emails)"
                    }
                },
                "required": ["message_id"]
            }
        },
        {
            "name": "search_emails",
            "description": "Search emails using Gmail search syntax. More powerful than list_emails for specific queries.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail search query. Examples: 'from:boss@company.com', 'subject:project after:2024/1/1', 'has:attachment', 'is:starred'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default 10, max 50)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_recent_unread_emails",
            "description": "Get recent unread emails. Quick shortcut for checking new messages.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of unread emails to return (default 5, max 20)",
                        "default": 5
                    }
                },
                "required": []
            }
        }
    ]


async def stream_claude_response(
    messages: List[Dict[str, str]],
    system_prompt: str = "You are a helpful AI assistant with access to the user's Gmail inbox. You can help them search, read, and manage their emails.",
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 4096,
    tools: Optional[List[Dict]] = None,
    user_email: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Stream responses from Claude API with tool use support.

    Args:
        messages: List of message dicts with 'role' and 'content'
        system_prompt: System prompt for the assistant
        model: Claude model to use
        max_tokens: Maximum tokens in response
        tools: List of tool definitions (if None, uses Gmail tools by default)
        user_email: User's email for tool execution context

    Yields:
        Text chunks from Claude's response
    """
    from app.gmail_client import list_emails, read_email, search_emails, get_recent_unread_emails

    # Use Gmail tools by default
    if tools is None:
        tools = get_gmail_tools()

    async with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
        tools=tools if tools else None
    ) as stream:
        async for text in stream.text_stream:
            yield text

        # Handle tool use
        message = await stream.get_final_message()

        # Check if Claude wants to use tools
        while message.stop_reason == "tool_use":
            tool_uses = [block for block in message.content if block.type == "tool_use"]

            # Execute tools
            tool_results = []
            for tool_use in tool_uses:
                logger.info(f"Executing tool: {tool_use.name} with input: {tool_use.input}")

                try:
                    if tool_use.name == "list_emails":
                        result = await list_emails(
                            user_email,
                            max_results=tool_use.input.get("max_results", 10),
                            query=tool_use.input.get("query", "")
                        )
                    elif tool_use.name == "read_email":
                        result = await read_email(
                            user_email,
                            message_id=tool_use.input["message_id"]
                        )
                    elif tool_use.name == "search_emails":
                        result = await search_emails(
                            user_email,
                            query=tool_use.input["query"],
                            max_results=tool_use.input.get("max_results", 10)
                        )
                    elif tool_use.name == "get_recent_unread_emails":
                        result = await get_recent_unread_emails(
                            user_email,
                            max_results=tool_use.input.get("max_results", 5)
                        )
                    else:
                        result = {"error": f"Unknown tool: {tool_use.name}"}

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(result)
                    })
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": f"Error: {str(e)}",
                        "is_error": True
                    })

            # Add tool results to messages and continue conversation
            messages.append({"role": "assistant", "content": message.content})
            messages.append({"role": "user", "content": tool_results})

            # Continue streaming with tool results
            async with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=messages,
                tools=tools if tools else None
            ) as stream:
                async for text in stream.text_stream:
                    yield text

                message = await stream.get_final_message()

async def get_claude_response(
    messages: List[Dict[str, str]],
    system_prompt: str = "You are a helpful AI assistant.",
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 4096
) -> str:
    """
    Get a complete response from Claude API.

    Args:
        messages: List of message dicts with 'role' and 'content'
        system_prompt: System prompt for the assistant
        model: Claude model to use
        max_tokens: Maximum tokens in response

    Returns:
        Complete response text
    """
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text
