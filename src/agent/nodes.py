"""LangGraph node implementations for nutrition analysis."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage

from src.agent.prompts import CRITIQUE_PROMPT, FOOD_IDENTIFICATION_PROMPT, NUTRITION_ESTIMATION_PROMPT
from src.agent.schema import NutritionReport
from src.agent.state import AgentState
from src.agent.utils import get_llm

logger = logging.getLogger(__name__)


def _image_content_block(state: AgentState) -> dict:
    """Build the LangChain image content block from state."""
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{state['image_mime_type']};base64,{state['image_base64']}"},
    }


def input_node(state: AgentState) -> AgentState:
    """Validate that image bytes are present."""
    if not state.get("image_base64") or not state.get("image_mime_type"):
        return {**state, "error": "No image data provided to agent."}
    return {**state, "error": None}


def identify_food_node(state: AgentState) -> AgentState:
    """Identify all food items visible in the image."""
    if state.get("error"):
        return state

    llm = get_llm()
    message = HumanMessage(
        content=[
            _image_content_block(state),
            {"type": "text", "text": FOOD_IDENTIFICATION_PROMPT},
        ]
    )

    try:
        response = llm.invoke([message])
        raw = response.content.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(raw)
        return {
            **state,
            "identified_foods": data.get("identified_foods", []),
            "cuisine_type": data.get("cuisine_guess"),
            "image_quality": data.get("image_quality", "medium"),
        }
    except Exception as e:
        logger.error(f"[identify_food_node] failed: {e}")
        return {**state, "error": f"Food identification failed: {str(e)}"}


def estimate_calories_node(state: AgentState) -> AgentState:
    """Estimate calories and macros using Gemini structured output."""
    if state.get("error"):
        return state

    llm = get_llm()
    structured_llm = llm.with_structured_output(NutritionReport)

    prompt = NUTRITION_ESTIMATION_PROMPT.format(
        identified_foods="\n".join(f"- {food}" for food in (state.get("identified_foods") or [])),
        cuisine_type=state.get("cuisine_type") or "Unknown",
    )

    message = HumanMessage(
        content=[
            _image_content_block(state),
            {"type": "text", "text": prompt},
        ]
    )

    try:
        report: NutritionReport = structured_llm.invoke([message])
        return {**state, "raw_nutrition_estimate": report.model_dump()}
    except Exception as e:
        logger.error(f"[estimate_calories_node] failed: {e}")
        return {**state, "error": f"Calorie estimation failed: {str(e)}"}


def critique_node(state: AgentState) -> AgentState:
    """Self-validate the nutrition estimate; correct math errors and omissions."""
    if state.get("error"):
        return state

    llm = get_llm()
    structured_llm = llm.with_structured_output(NutritionReport)

    prompt = CRITIQUE_PROMPT.format(
        original_estimate=json.dumps(state["raw_nutrition_estimate"], indent=2)
    )

    message = HumanMessage(
        content=[
            _image_content_block(state),
            {"type": "text", "text": prompt},
        ]
    )

    try:
        refined: NutritionReport = structured_llm.invoke([message])
        return {**state, "nutrition_report": refined}
    except Exception as e:
        # Non-fatal: fall back to the original estimate
        logger.warning(f"[critique_node] failed, using original estimate: {e}")
        return {
            **state,
            "nutrition_report": NutritionReport(**state["raw_nutrition_estimate"]),
        }
