"""Pluggable multi-LLM query engine for product recommendations."""

from __future__ import annotations

import argparse
import json
from typing import Callable

import requests

from config import (
    DEBUG_MODE,
    GEMINI_MODEL,
    GOOGLE_API_KEY,
    MULTI_LLM_PROVIDERS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    PERPLEXITY_API_KEY,
    PERPLEXITY_MODEL,
)
from core.product_schema import Product

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - optional dependency
    genai = None

try:
    import openai
except ImportError:  # pragma: no cover - optional dependency
    openai = None

class LLMProvider:
    """Base class for pluggable LLM providers."""

    name = "provider"

    def is_available(self) -> bool:
        """Return whether the provider is configured and usable."""
        raise NotImplementedError

    def query(self, prompt: str) -> str:
        """Send a prompt to the provider and return its response."""
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI-backed provider."""

    name = "openai"

    def __init__(self):
        self._client = None
        if OPENAI_API_KEY and openai is not None:
            self._client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def is_available(self) -> bool:
        return DEBUG_MODE or self._client is not None

    def query(self, prompt: str) -> str:
        if DEBUG_MODE:
            return f"OpenAI Debug: {prompt[:50]}..."
        if not self._client:
            return "OpenAI provider unavailable"

        try:
            response = self._client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.7,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:  # pragma: no cover - network/API failure
            return f"OpenAI Error: {exc}"


class GeminiProvider(LLMProvider):
    """Google Gemini-backed provider."""

    name = "gemini"

    def __init__(self):
        self._model = None
        if GOOGLE_API_KEY and genai is not None:
            genai.configure(api_key=GOOGLE_API_KEY)
            self._model = genai.GenerativeModel(GEMINI_MODEL)

    def is_available(self) -> bool:
        return DEBUG_MODE or self._model is not None

    def query(self, prompt: str) -> str:
        if DEBUG_MODE:
            return f"Gemini Debug: {prompt[:50]}..."
        if not self._model:
            return "Gemini provider unavailable"

        try:
            response = self._model.generate_content(prompt)
            return response.text
        except Exception as exc:  # pragma: no cover - network/API failure
            return f"Gemini Error: {exc}"


class PerplexityProvider(LLMProvider):
    """Perplexity-backed provider."""

    name = "perplexity"

    def is_available(self) -> bool:
        return DEBUG_MODE or bool(PERPLEXITY_API_KEY)

    def query(self, prompt: str) -> str:
        if DEBUG_MODE:
            return f"Perplexity Debug: {prompt[:50]}..."
        if not PERPLEXITY_API_KEY:
            return "Perplexity provider unavailable"

        try:
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": PERPLEXITY_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                    "temperature": 0.7,
                },
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as exc:  # pragma: no cover - network/API failure
            return f"Perplexity Error: {exc}"


ProviderFactory = Callable[[], LLMProvider]

PROVIDER_REGISTRY: dict[str, ProviderFactory] = {
    "openai": OpenAIProvider,
    "chatgpt": OpenAIProvider,
    "gemini": GeminiProvider,
    "perplexity": PerplexityProvider,
}


class MultiLLMQueryEngine:
    """Engine for querying a configurable set of LLM providers."""

    def __init__(self, enabled_providers: list[str] | None = None):
        provider_names = enabled_providers or MULTI_LLM_PROVIDERS
        self.providers = self._build_providers(provider_names)

    def _build_providers(self, provider_names: list[str]) -> dict[str, LLMProvider]:
        providers: dict[str, LLMProvider] = {}
        for provider_name in provider_names:
            factory = PROVIDER_REGISTRY.get(provider_name)
            if not factory:
                continue

            provider = factory()
            providers[provider.name] = provider

        return providers

    def available_provider_names(self) -> list[str]:
        """Return configured providers that are ready to run."""
        return [
            name
            for name, provider in self.providers.items()
            if provider.is_available()
        ]

    def query_all_llms(self, prompt: str) -> dict[str, str]:
        """Query all configured and available providers."""
        responses = {}
        for name, provider in self.providers.items():
            if provider.is_available():
                responses[name] = provider.query(prompt)

        return responses

    def query_product_recommendations(self, product: Product) -> dict[str, dict[str, str]]:
        """Query all configured providers for recommendations based on product queries."""
        from core.query_engine import build_queries  # Import here to avoid circular import

        queries = build_queries(product)
        return {query: self.query_all_llms(query) for query in queries}


def main():
    """Command-line interface for testing the multi-LLM query engine."""
    import sys

    parser = argparse.ArgumentParser(description="Query multiple LLMs for product recommendations")
    parser.add_argument("query", nargs="?", help="Direct query to send to LLMs")
    parser.add_argument("--providers", help="Comma-separated provider list")
    parser.add_argument("--product", help="Product name")
    parser.add_argument("--brand", help="Product brand")
    parser.add_argument("--category", help="Product category")
    parser.add_argument("--price", type=float, help="Product price")
    parser.add_argument("--features", help="Key features (comma-separated)")
    parser.add_argument("--description", help="Product description")
    parser.add_argument("--availability", choices=["in stock", "out of stock"], default="in stock")

    args = parser.parse_args()
    enabled_providers = None
    if args.providers:
        enabled_providers = [provider.strip().lower() for provider in args.providers.split(",") if provider.strip()]

    engine = MultiLLMQueryEngine(enabled_providers=enabled_providers)

    if args.query:
        responses = engine.query_all_llms(args.query)
        print(json.dumps(responses, indent=2))
    elif args.product and args.brand and args.category and args.price is not None:
        product = Product(
            name=args.product,
            brand=args.brand,
            category=args.category,
            price=args.price,
            key_features=args.features.split(",") if args.features else [],
            description=args.description or "",
            availability=args.availability,
        )
        responses = engine.query_product_recommendations(product)
        print(json.dumps(responses, indent=2))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
