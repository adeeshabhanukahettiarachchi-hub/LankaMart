from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["Electronics", "Fashion", "Home and Kitchen", "Beauty", "Sports"]
Region = Literal["Western", "Central", "Southern", "Northern", "Eastern", "North Western"]


class OrderFeatures(BaseModel):
    category: Category
    region: Region
    quantity: int = Field(ge=1, le=20)
    unit_price: float = Field(gt=0, le=1_000_000)
    discount_rate: float = Field(ge=0, le=0.5)
    returned: int = Field(default=0, ge=0, le=1)


class OrderCreate(OrderFeatures):
    order_date: date
    delivery_days: int = Field(ge=0, le=60)
