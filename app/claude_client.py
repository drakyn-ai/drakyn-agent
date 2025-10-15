"""Claude API client with streaming support."""
from anthropic import AsyncAnthropic
from typing import List, Dict, AsyncGenerator
import app.config as config

client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

async def stream_claude_response(
    messages: List[Dict[str, str]],
    system_prompt: str = "You are a helpful AI assistant.",
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 4096
) -> AsyncGenerator[str, None]:
    """
    Stream responses from Claude API.

    Args:
        messages: List of message dicts with 'role' and 'content'
        system_prompt: System prompt for the assistant
        model: Claude model to use
        max_tokens: Maximum tokens in response

    Yields:
        Text chunks from Claude's response
    """
    async with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text

async def get_claude_response(
    messages: List[Dict[str, str]],
    system_prompt: str = "You are a helpful AI assistant.",
    model: str = "claude-3-5-sonnet-20241022",
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
