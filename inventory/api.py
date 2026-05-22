from fastapi import FastAPI, HTTPException
from forecaster_db import get_predictions, add_consumption
from pydantic import BaseModel

app = FastAPI(title="Mayda Inventory Prediction Service")

class ConsumptionInput(BaseModel):
    restaurant_id: int
    ingredient_id: int
    quantity: float

@app.post("/predict")
def predict(data: ConsumptionInput):
    try:
        result = get_predictions(data.restaurant_id, data.ingredient_id, data.quantity)
        return {"predictions": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/consumption")
def consumption(data: ConsumptionInput):
    try:
        add_consumption(data.restaurant_id, data.ingredient_id, data.quantity)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
