"""Gmail API client for email operations."""
import base64
from datetime import datetime
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import app.database as db
import app.config as config
import logging

logger = logging.getLogger(__name__)


async def get_gmail_service(user_email: str):
    """Create Gmail API service with user's OAuth credentials."""
    token_data = await db.get_oauth_token(user_email)
    if not token_data:
        raise Exception("No OAuth token found for user. User needs to re-authenticate.")

    creds = Credentials(
        token=token_data['access_token'],
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET
    )

    service = build('gmail', 'v1', credentials=creds)
    return service


async def list_emails(user_email: str, max_results: int = 10, query: str = "") -> List[Dict]:
    """
    List emails from user's Gmail inbox.

    Args:
        user_email: User's email address
        max_results: Maximum number of emails to return (default 10)
        query: Gmail search query (e.g., "from:example@gmail.com", "subject:meeting", "is:unread")

    Returns:
        List of email metadata dictionaries
    """
    try:
        service = await get_gmail_service(user_email)

        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=query
        ).execute()

        messages = results.get('messages', [])

        email_list = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()

            headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}

            email_list.append({
                'id': msg_data['id'],
                'thread_id': msg_data['threadId'],
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'subject': headers.get('Subject', ''),
                'date': headers.get('Date', ''),
                'snippet': msg_data.get('snippet', '')
            })

        return email_list

    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        raise Exception(f"Failed to list emails: {str(error)}")


async def read_email(user_email: str, message_id: str) -> Dict:
    """
    Read full email content by message ID.

    Args:
        user_email: User's email address
        message_id: Gmail message ID

    Returns:
        Dictionary with email details including body
    """
    try:
        service = await get_gmail_service(user_email)

        msg_data = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}

        # Extract email body
        body = ""
        if 'parts' in msg_data['payload']:
            for part in msg_data['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
        elif 'body' in msg_data['payload'] and 'data' in msg_data['payload']['body']:
            body = base64.urlsafe_b64decode(msg_data['payload']['body']['data']).decode('utf-8')

        return {
            'id': msg_data['id'],
            'thread_id': msg_data['threadId'],
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'subject': headers.get('Subject', ''),
            'date': headers.get('Date', ''),
            'body': body,
            'snippet': msg_data.get('snippet', '')
        }

    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        raise Exception(f"Failed to read email: {str(error)}")


async def search_emails(user_email: str, query: str, max_results: int = 10) -> List[Dict]:
    """
    Search emails using Gmail search syntax.

    Args:
        user_email: User's email address
        query: Gmail search query
        max_results: Maximum number of results

    Returns:
        List of matching emails

    Example queries:
        - "from:example@gmail.com"
        - "subject:meeting after:2024/1/1"
        - "is:unread"
        - "has:attachment"
        - "newer_than:7d"
    """
    return await list_emails(user_email, max_results, query)


async def get_recent_unread_emails(user_email: str, max_results: int = 5) -> List[Dict]:
    """
    Get recent unread emails.

    Args:
        user_email: User's email address
        max_results: Maximum number of emails to return

    Returns:
        List of unread emails
    """
    return await list_emails(user_email, max_results, "is:unread")
