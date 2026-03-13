"""Multi-LLM Query Engine for product recommendations.

This module allows querying multiple LLMs (OpenAI ChatGPT, Google Gemini, Perplexity)
for product recommendations and data queries, orchestrated by Claude.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional

import google.generativeai as genai
import openai
import requests

from config import DEBUG_MODE, GOOGLE_API_KEY, OPENAI_API_KEY, PERPLEXITY_API_KEY
from core.debug_mode import mock_query_response
from core.product_schema import Product


class MultiLLMQueryEngine:
    """Engine for querying multiple LLMs for product recommendations."""

    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None

    def query_chatgpt(self, prompt: str) -> str:
        """Query OpenAI ChatGPT."""
        if not self.openai_client:
            return "OpenAI API key not configured"

        if DEBUG_MODE:
            return f"ChatGPT Debug: {prompt[:50]}..."

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"ChatGPT Error: {str(e)}"

    def query_gemini(self, prompt: str) -> str:
        """Query Google Gemini."""
        if not self.gemini_model:
            return "Google API key not configured"

        if DEBUG_MODE:
            return f"Gemini Debug: {prompt[:50]}..."

        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Gemini Error: {str(e)}"

    def query_perplexity(self, prompt: str) -> str:
        """Query Perplexity AI."""
        if not PERPLEXITY_API_KEY:
            return "Perplexity API key not configured"

        if DEBUG_MODE:
            return f"Perplexity Debug: {prompt[:50]}..."

        try:
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
                "temperature": 0.7
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Perplexity Error: {str(e)}"

    def query_all_llms(self, prompt: str) -> Dict[str, str]:
        """Query all available LLMs and return their responses."""
        responses = {}

        if self.openai_client or DEBUG_MODE:
            responses["chatgpt"] = self.query_chatgpt(prompt)

        if self.gemini_model or DEBUG_MODE:
            responses["gemini"] = self.query_gemini(prompt)

        if PERPLEXITY_API_KEY or DEBUG_MODE:
            responses["perplexity"] = self.query_perplexity(prompt)

        return responses

    def query_product_recommendations(self, product: Product) -> Dict[str, Dict[str, str]]:
        """Query all LLMs for recommendations based on product queries."""
        from core.query_engine import build_queries  # Import here to avoid circular import

        queries = build_queries(product)
        all_responses = {}

        for query in queries:
            all_responses[query] = self.query_all_llms(query)

        return all_responses


def main():
    """Command-line interface for testing the multi-LLM query engine."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Query multiple LLMs for product recommendations")
    parser.add_argument("query", nargs="?", help="Direct query to send to LLMs")
    parser.add_argument("--product", help="Product name")
    parser.add_argument("--brand", help="Product brand")
    parser.add_argument("--category", help="Product category")
    parser.add_argument("--price", type=float, help="Product price")
    parser.add_argument("--features", help="Key features (comma-separated)")
    parser.add_argument("--description", help="Product description")
    parser.add_argument("--availability", choices=["in stock", "out of stock"], default="in stock")

    args = parser.parse_args()

    engine = MultiLLMQueryEngine()

    if args.query:
        # Direct query
        responses = engine.query_all_llms(args.query)
        print(json.dumps(responses, indent=2))
    elif args.product and args.brand and args.category and args.price is not None:
        # Product-based queries
        from core.product_schema import Product
        product = Product(
            name=args.product,
            brand=args.brand,
            category=args.category,
            price=args.price,
            key_features=args.features.split(",") if args.features else [],
            description=args.description or "",
            availability=args.availability
        )
        responses = engine.query_product_recommendations(product)
        print(json.dumps(responses, indent=2))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()