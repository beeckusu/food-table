import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    pass


def generate_text(system_prompt: str, user_content: str, model: str = None) -> str:
    """
    Call Claude API and return the text response.
    Raises AIServiceError on any failure.
    """
    try:
        import anthropic
    except ImportError:
        raise AIServiceError("anthropic package is not installed")

    api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
    if not api_key:
        raise AIServiceError("ANTHROPIC_API_KEY is not configured")

    if model is None:
        model = getattr(settings, "ANTHROPIC_DEFAULT_MODEL", "claude-sonnet-4-6")

    client = anthropic.Anthropic(api_key=api_key)

    try:
        import time
        start = time.monotonic()
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        elapsed = time.monotonic() - start
        response_text = message.content[0].text
        logger.info(
            "AI call complete: model=%s input_chars=%d output_chars=%d latency=%.2fs",
            model,
            len(user_content),
            len(response_text),
            elapsed,
        )
        return response_text
    except anthropic.AuthenticationError as e:
        logger.error("Anthropic auth error: %s", e)
        raise AIServiceError("Invalid Anthropic API key") from e
    except anthropic.RateLimitError as e:
        logger.error("Anthropic rate limit: %s", e)
        raise AIServiceError("Anthropic rate limit exceeded") from e
    except anthropic.APITimeoutError as e:
        logger.error("Anthropic timeout: %s", e)
        raise AIServiceError("Anthropic API request timed out") from e
    except Exception as e:
        logger.error("Anthropic API error: %s", e)
        raise AIServiceError(f"Anthropic API error: {e}") from e
