"""LangGraph agent state definition for nutrition analysis."""

from __future__ import annotations

from typing import Any, Optional, TypedDict

from src.agent.schema import NutritionReport


class AgentState(TypedDict):
    """State machine for the nutrition analysis agent."""

    # Set once at entry
    image_base64: str
    image_mime_type: str

    # Populated by identify_food_node
    identified_foods: Optional[list[str]]
    cuisine_type: Optional[str]
    image_quality: Optional[str]  # "good" | "medium" | "poor"

    # Populated by estimate_calories_node
    raw_nutrition_estimate: Optional[dict[str, Any]]

    # Populated by critique_node
    nutrition_report: Optional[NutritionReport]

    # Set by any node on failure
    error: Optional[str]
