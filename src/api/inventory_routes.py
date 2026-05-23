"""
API routes for the Restaurant Inventory Forecasting Service.
"""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.core.config import settings
from src.middleware.service_auth import require_service_token
from src.schemas.inventory_schema import (
    BulkForecastRequest,
    BulkForecastResponse,
    ConsumptionLogInput,
    ConsumptionLogResponse,
    ForecastRequest,
    ForecastResponse,
)
from src.services.inventory_db_service import FoodItem, get_inventory_db
from src.services.inventory_forecaster import DatabaseIntegratedForecaster

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_forecaster(request: Request) -> DatabaseIntegratedForecaster:
    """Retrieve the global DatabaseIntegratedForecaster stored in app.state."""
    return request.app.state.forecaster


# ── Inventory Endpoints ──

@router.post(
    "/forecast",
    response_model=ForecastResponse,
    dependencies=[Depends(require_service_token)],
)
async def forecast_item(
    body: ForecastRequest,
    forecaster: DatabaseIntegratedForecaster = Depends(_get_forecaster),
    db: Session = Depends(get_inventory_db),
):
    """
    Generate consumption forecast for a single food item.
    """
    prediction = forecaster.predict_consumption(
        food_item=body.item,
        date=body.date,
        db=db,
        weather=body.weather or "sunny",
        special_event=body.special_event or 0,
    )

    if prediction is None:
        raise HTTPException(
            status_code=400,
            detail=f"Item '{body.item}' is either not indexed or has insufficient historical records to forecast."
        )

    return ForecastResponse(
        item=body.item,
        date=body.date.strftime("%Y-%m-%d"),
        units=prediction,
        model_version="RandomForest_v1.0",
        generated_at=datetime.now(UTC).isoformat(),
    )


@router.post(
    "/forecast/bulk",
    response_model=BulkForecastResponse,
    dependencies=[Depends(require_service_token)],
)
async def forecast_bulk(
    body: BulkForecastRequest,
    forecaster: DatabaseIntegratedForecaster = Depends(_get_forecaster),
    db: Session = Depends(get_inventory_db),
):
    """
    Generate bulk forecasts for multiple food items (avoiding redundant request round-trips).
    """
    forecasts = []
    for item_req in body.items:
        prediction = forecaster.predict_consumption(
            food_item=item_req.item,
            date=item_req.date,
            db=db,
            weather=item_req.weather or "sunny",
            special_event=item_req.special_event or 0,
        )
        if prediction is not None:
            forecasts.append(
                ForecastResponse(
                    item=item_req.item,
                    date=item_req.date.strftime("%Y-%m-%d"),
                    units=prediction,
                    model_version="RandomForest_v1.0",
                    generated_at=datetime.now(UTC).isoformat(),
                )
            )

    return BulkForecastResponse(forecasts=forecasts)


@router.get(
    "/recommendations/restock",
    dependencies=[Depends(require_service_token)],
)
async def restock_recommendations(
    days_ahead: int = 7,
    safety_margin: float = 0.2,
    forecaster: DatabaseIntegratedForecaster = Depends(_get_forecaster),
    db: Session = Depends(get_inventory_db),
):
    """
    Get weekly restocking recommendations based on future predictions, minimum stock rules, and safety buffers.
    """
    recommendations = forecaster.generate_restock_recommendations(
        db=db, days_ahead=days_ahead, safety_margin=safety_margin
    )
    return recommendations


@router.get(
    "/items",
    dependencies=[Depends(require_service_token)],
)
async def list_food_items(
    db: Session = Depends(get_inventory_db),
):
    """
    List all known food items in the inventory database (for autocomplete or catalog checks).
    """
    items = db.query(FoodItem).all()
    return {"items": [item.name for item in items], "count": len(items)}


@router.post(
    "/consumption",
    response_model=ConsumptionLogResponse,
    dependencies=[Depends(require_service_token)],
)
async def log_consumption(
    body: ConsumptionLogInput,
    forecaster: DatabaseIntegratedForecaster = Depends(_get_forecaster),
    db: Session = Depends(get_inventory_db),
):
    """
    Record daily consumption value for a food item and decrement stock levels accordingly.
    """
    try:
        forecaster.add_consumption_record(
            food_item=body.food_item,
            date=datetime.now(UTC),
            consumption=body.consumption,
            db=db,
            weather=body.weather or "sunny",
            special_event=body.special_event or False,
            notes=body.notes,
        )
        return ConsumptionLogResponse(
            message=f"Consumption of {body.consumption} units logged successfully for '{body.food_item}'."
        )
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as exc:
        logger.error("Error logging consumption: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to record consumption: {str(exc)}")


@router.post(
    "/admin/retrain",
    dependencies=[Depends(require_service_token)],
)
async def retrain_forecaster_models(
    forecaster: DatabaseIntegratedForecaster = Depends(_get_forecaster),
    db: Session = Depends(get_inventory_db),
):
    """
    Trigger retraining of all models using database history and write them to serialized disk storage.
    """
    try:
        logger.info("Admin triggered retraining of forecasting models...")
        forecaster.train_models(db=db, use_database=True)
        forecaster.save_models(settings.INVENTORY_MODEL_PATH)
        return {
            "status": "success",
            "message": f"Successfully retrained models for {len(forecaster.models)} items and persisted to storage.",
        }
    except Exception as exc:
        logger.error("Failed to retrain models: %s", exc)
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(exc)}")
