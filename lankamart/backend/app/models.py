from sqlalchemy import String, Integer, Float, Date
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    order_date: Mapped[object] = mapped_column(Date, index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    region: Mapped[str] = mapped_column(String(40), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    discount_rate: Mapped[float] = mapped_column(Float)
    sales_amount: Mapped[float] = mapped_column(Float)
    profit: Mapped[float] = mapped_column(Float)
    delivery_days: Mapped[int] = mapped_column(Integer)
    returned: Mapped[int] = mapped_column(Integer)
    late_delivery: Mapped[int] = mapped_column(Integer)
