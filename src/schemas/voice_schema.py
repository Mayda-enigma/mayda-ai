"""
Pydantic schemas for Voice service APIs.
"""

from pydantic import BaseModel, Field

# ── Chef Command Parse Schemas ──

class ChefParseRequest(BaseModel):
    """Request schema for parsing French chef vocal commands."""
    text: str = Field(..., description="Transcription of the chef command, e.g., 'Commande 12 prête'")


class ChefParseResponse(BaseModel):
    """Response schema representing the parsed French chef command."""
    type: str | None = Field(None, description="Action type: 'lance', 'prete', or null")
    order_number: str | None = Field(None, description="Extracted order numeric identifier")
    confidence: int | None = Field(None, description="Matching confidence score (0-100)")
    matched_phrase: str | None = Field(None, description="Target phrase that yielded the best match")
    message: str | None = Field(None, description="Formatted response narrative message")


# ── Customer Menu Order Parse Schemas ──

class MenuItem(BaseModel):
    """Represents a product item in the restaurant catalog."""
    id: int = Field(..., description="Unique product ID")
    name: str = Field(..., description="Product name, e.g., 'Cheeseburger'")


class OrderParseRequest(BaseModel):
    """Request schema for parsing fuzzy verbal menu orders."""
    text: str = Field(..., description="Spoken/transcribed order text, e.g., 'two burgers and a cola'")
    menu_items: list[MenuItem] = Field(..., description="Available catalog of items to match against")


class OrderParseItem(BaseModel):
    """Result details of a successfully parsed menu order item."""
    menu_item_id: int = Field(..., description="Matched menu item ID")
    menu_item_name: str | None = Field(None, description="Matched menu item name")
    quantity: int = Field(1, description="Quantity ordered")
    confidence: int = Field(..., description="Matching similarity confidence score (0-100)")


class OrderParseResponse(BaseModel):
    """Response schema for order parsing."""
    items: list[OrderParseItem] = Field(..., description="List of matched catalog items and quantities")
