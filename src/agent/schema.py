"""Pydantic response schema for nutrition analysis report."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence level for nutritional estimates."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MacroNutrients(BaseModel):
    """Macronutrient breakdown."""

    protein_g: float = Field(..., ge=0, description="Protein in grams")
    carbohydrates_g: float = Field(..., ge=0, description="Carbohydrates in grams")
    fat_g: float = Field(..., ge=0, description="Total fat in grams")
    fiber_g: float = Field(..., ge=0, description="Dietary fiber in grams")
    sugar_g: float = Field(..., ge=0, description="Total sugars in grams")
    sodium_mg: float = Field(..., ge=0, description="Sodium in milligrams")


class FoodComponent(BaseModel):
    """A single food item or ingredient in the meal."""

    name: str = Field(..., description="Name of the food item or ingredient")
    estimated_portion_g: float = Field(..., ge=0, description="Estimated weight in grams")
    calories_kcal: float = Field(..., ge=0, description="Estimated calories for this component")
    macros: MacroNutrients
    preparation_method: Optional[str] = Field(
        None, description="Visible preparation method (fried, steamed, raw, grilled)"
    )
    confidence: ConfidenceLevel
    notes: Optional[str] = Field(
        None, description="Allergens, high-sodium warning, or unusual ingredient notes"
    )


class NutritionReport(BaseModel):
    """Complete nutrition analysis report for a food image."""

    dish_name: str = Field(..., description="Overall name or description of the meal")
    cuisine_type: Optional[str] = Field(None, description="Identified cuisine type")
    components: list[FoodComponent] = Field(..., min_length=1)
    total_calories_kcal: float = Field(..., ge=0)
    total_macros: MacroNutrients
    overall_confidence: ConfidenceLevel
    health_flags: list[str] = Field(
        default_factory=list,
        description="e.g. ['high sodium', 'high fat', 'contains gluten', 'fried food']",
    )
    estimation_disclaimer: str = Field(
        default=(
            "Calorie and nutrient estimates are approximations based on visual analysis. "
            "Actual values may vary depending on exact ingredients, portion sizes, and "
            "preparation methods. For precise nutrition information, consult a registered "
            "dietitian or use a food weight scale with a nutrition database."
        )
    )
