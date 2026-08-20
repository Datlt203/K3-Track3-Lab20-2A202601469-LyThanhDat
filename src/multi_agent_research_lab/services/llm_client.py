"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass

from multi_agent_research_lab.core.config import get_settings


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic client with an offline-safe fallback."""

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Call OpenAI when configured; keep local demos deterministic otherwise.
        """
        settings = get_settings()
        if settings.openai_api_key:
            try:
                from openai import OpenAI
                client = OpenAI(
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url,
                    timeout=settings.timeout_seconds,
                )
                response = client.chat.completions.create(
                    model=settings.openai_model, temperature=0,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                usage = response.usage
                input_tokens = getattr(usage, "prompt_tokens", None) if usage else None
                output_tokens = getattr(usage, "completion_tokens", None) if usage else None
                cost = None
                if input_tokens is not None and output_tokens is not None:
                    cost = input_tokens * 0.15 / 1_000_000 + output_tokens * 0.60 / 1_000_000
                return LLMResponse(
                    response.choices[0].message.content or "",
                    input_tokens,
                    output_tokens,
                    cost,
                )
            except Exception:
                pass
        content = (
            "Offline fallback: synthesize evidence, cite source IDs, and state limitations.\n\n"
            + user_prompt[:2000]
        )
        return LLMResponse(content, len(user_prompt.split()), len(content.split()), 0.0)
