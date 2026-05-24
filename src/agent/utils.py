"""Utility functions for the nutrition analysis agent."""

import os

from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm() -> ChatGoogleGenerativeAI:
    """Initialize and return a Gemini LLM instance."""
    return ChatGoogleGenerativeAI(
        model=os.getenv("NUTRITION_GEMINI_MODEL", "gemini-2.5-flash"),
        temperature=float(os.getenv("NUTRITION_GEMINI_TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("NUTRITION_GEMINI_MAX_TOKENS", "4096")),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
