"""
Pydantic schemas for the Inventory Forecasting Service.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Single Forecast Request/Response ──

class ForecastRequest(BaseModel):
    """Request schema for predicting daily consumption of a food item."""
    item: str = Field(..., description="Name of the food item, e.g., 'Chicken Breast'")
    date: datetime = Field(..., description="Target date for forecasting (ISO 8601 format)")
    weather: Optional[str] = Field("sunny", description="Predicted weather condition ('sunny', 'rainy', 'cloudy')")
    special_event: Optional[int] = Field(0, description="Whether there is a special event (0 = No, 1 = Yes)")


class ForecastResponse(BaseModel):
    """Response schema for food item consumption forecast."""
    item: str = Field(..., description="Name of the food item")
    date: str = Field(..., description="Target date formatted as YYYY-MM-DD")
    units: float = Field(..., description="Predicted consumption units")
    model_version: str = Field(..., description="Version of the model that generated the prediction")
    generated_at: str = Field(..., description="Timestamp of prediction generation")


# ── Bulk Forecast Request/Response ──

class BulkForecastRequest(BaseModel):
    """Request schema for bulk forecasting."""
    items: List[ForecastRequest] = Field(..., description="List of individual forecast queries")


class BulkForecastResponse(BaseModel):
    """Response schema for bulk forecasting."""
    forecasts: List[ForecastResponse] = Field(..., description="List of predictions")


# ── Consumption Logging Schemas ──

class ConsumptionLogInput(BaseModel):
    """Request schema for recording daily consumption usage."""
    food_item: str = Field(..., description="Name of the food item used")
    consumption: float = Field(..., ge=0.0, description="Total units consumed today")
    weather: Optional[str] = Field("sunny", description="Weather condition today ('sunny', 'rainy', 'cloudy')")
    special_event: Optional[bool] = Field(False, description="Whether today was a holiday/busy day")
    notes: Optional[str] = Field(None, description="Optional annotations or context")


class ConsumptionLogResponse(BaseModel):
    """Response schema for consumption logging."""
    status: str = Field("ok", description="Status of the logging operation")
    message: str = Field(..., description="Brief success message")
