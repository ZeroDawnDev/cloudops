"""
llm_client.py
-------------
Thin wrapper around the LLM provider so agents never talk to an SDK
directly. Swap the implementation and every agent keeps working unchanged.

Default provider: Anthropic Claude. Set LLM_PROVIDER=openai in .env to
switch (an OpenAI implementation is included for convenience).
"""

import os
import json
import logging

logger = logging.getLogger("cloudops.llm")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()


class LLMError(RuntimeError):
    """Raised when the LLM call fails or returns unusable output."""


def _call_anthropic(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
    import anthropic  # lazy import so the app can boot without the package/key set

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMError("ANTHROPIC_API_KEY is not set in the environment (.env)")

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:  # noqa: BLE001 - surface as a domain error
        raise LLMError(f"Anthropic API call failed: {exc}") from exc

    text_parts = [block.text for block in response.content if block.type == "text"]
    if not text_parts:
        raise LLMError("Anthropic response contained no text content")
    return "".join(text_parts)


def _call_openai(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
    from openai import OpenAI  # lazy import

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMError("OPENAI_API_KEY is not set in the environment (.env)")

    # OPENAI_BASE_URL lets this same code path hit any OpenAI-compatible
    # endpoint -- e.g. Groq (https://api.groq.com/openai/v1) or OpenRouter
    # (https://openrouter.ai/api/v1) -- so you can run this whole project
    # on a free tier without touching any agent code.
    base_url = os.getenv("OPENAI_BASE_URL") or None
    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:  # noqa: BLE001
        raise LLMError(f"OpenAI-compatible API call failed: {exc}") from exc

    return response.choices[0].message.content or ""


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
    """Route to the configured provider. Returns raw text from the model."""
    if LLM_PROVIDER == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, max_tokens)
    if LLM_PROVIDER == "openai":
        return _call_openai(system_prompt, user_prompt, max_tokens)
    raise LLMError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def call_llm_json(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> dict:
    """
    Calls the LLM and parses strict JSON from the response.
    Every agent uses this exclusively so results are structured, not prose.
    """
    raw = call_llm(system_prompt, user_prompt, max_tokens)
    cleaned = raw.strip()
    # Defensive cleanup in case the model wraps output in markdown fences
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse LLM JSON output: %s\nRaw: %s", exc, raw)
        raise LLMError(f"Model did not return valid JSON: {exc}") from exc
