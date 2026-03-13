from __future__ import annotations

import math
import threading
import time
from collections import deque
from collections.abc import Iterable, Sequence
from typing import Any

from config import (
    ANTHROPIC_INPUT_TOKEN_BUDGET_RATIO,
    ANTHROPIC_INPUT_TOKENS_PER_MINUTE,
)

REQUEST_TOKEN_OVERHEAD = 64
MESSAGE_TOKEN_OVERHEAD = 12
EFFECTIVE_INPUT_TOKEN_BUDGET = max(
    1,
    math.floor(
        ANTHROPIC_INPUT_TOKENS_PER_MINUTE * ANTHROPIC_INPUT_TOKEN_BUDGET_RATIO
    ),
)


def _stringify_content_block(block: Any) -> str:
    if isinstance(block, str):
        return block
    if isinstance(block, dict):
        if isinstance(block.get("text"), str):
            return block["text"]
        if isinstance(block.get("content"), str):
            return block["content"]
        return ""
    text = getattr(block, "text", None)
    if isinstance(text, str):
        return text
    content = getattr(block, "content", None)
    if isinstance(content, str):
        return content
    return ""


def extract_message_text(messages: Sequence[dict[str, Any]] | None) -> str:
    """Flatten Anthropic-style message payloads into plain text."""
    if not messages:
        return ""

    chunks: list[str] = []
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            chunks.append(content)
            continue
        if isinstance(content, Iterable):
            chunks.extend(
                text
                for item in content
                if (text := _stringify_content_block(item))
            )
    return "\n".join(chunks)


def estimate_input_tokens(messages: Sequence[dict[str, Any]] | None) -> int:
    """Strictly estimate prompt tokens from text length and message overhead."""
    if not messages:
        return 0

    text = extract_message_text(messages)
    text_tokens = math.ceil(len(text) / 2)
    overhead_tokens = REQUEST_TOKEN_OVERHEAD + (len(messages) * MESSAGE_TOKEN_OVERHEAD)
    return max(1, text_tokens + overhead_tokens)


class InputTokenRateLimiter:
    """Sliding-window limiter for input token throughput."""

    def __init__(
        self,
        max_tokens_per_minute: int,
        *,
        window_seconds: float = 60.0,
        time_fn: Any = None,
        sleep_fn: Any = None,
    ) -> None:
        self.max_tokens_per_minute = max_tokens_per_minute
        self.window_seconds = window_seconds
        self.time_fn = time_fn or time.monotonic
        self.sleep_fn = sleep_fn or time.sleep
        self._events: deque[tuple[float, int]] = deque()
        self._tokens_in_window = 0
        self._lock = threading.Lock()

    def acquire(self, tokens: int) -> None:
        if tokens <= 0:
            return
        if tokens > self.max_tokens_per_minute:
            raise ValueError(
                "Prompt exceeds the configured Anthropic input token budget for a single minute."
            )

        while True:
            wait_for = 0.0
            with self._lock:
                now = self.time_fn()
                self._prune(now)
                if self._tokens_in_window + tokens <= self.max_tokens_per_minute:
                    self._events.append((now, tokens))
                    self._tokens_in_window += tokens
                    return
                oldest_timestamp, _ = self._events[0]
                wait_for = max(self.window_seconds - (now - oldest_timestamp), 0.01)
            self.sleep_fn(wait_for)

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._events and self._events[0][0] <= cutoff:
            _, tokens = self._events.popleft()
            self._tokens_in_window -= tokens


anthropic_input_rate_limiter = InputTokenRateLimiter(
    EFFECTIVE_INPUT_TOKEN_BUDGET
)


def create_rate_limited_message(client: Any, **kwargs: Any) -> Any:
    """Throttle Anthropic requests by estimated input tokens before sending."""
    anthropic_input_rate_limiter.acquire(
        estimate_input_tokens(kwargs.get("messages"))
    )
    return client.messages.create(**kwargs)
