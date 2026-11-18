from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="client")  # client, mechanic, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    parent_id = Column(Integer, ForeignKey("service_categories.id", ondelete="SET NULL"), nullable=True, index=True)

    parent = relationship("ServiceCategory", remote_side=[id], backref="subcategories")
    services = relationship("ServiceItem", back_populates="category")


class ServiceItem(Base):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint("base_price > 0", name="check_service_price_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("service_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    base_price = Column(Float, nullable=False)

    category = relationship("ServiceCategory", back_populates="services")


class Part(Base):
    __tablename__ = "parts"
    __table_args__ = (
        CheckConstraint("price > 0", name="check_part_price_positive"),
        CheckConstraint("stock_quantity >= 0", name="check_part_stock_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    part_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint("year >= 1900 AND year <= 2030", name="check_vehicle_year_valid"),
    )

    id = Column(Integer, primary_key=True, index=True)
    vin = Column(String(17), unique=True, index=True, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    owner = relationship("User", back_populates="vehicles")
    work_orders = relationship("WorkOrder", back_populates="vehicle", cascade="all, delete-orphan")


class WorkOrder(Base):
    __tablename__ = "work_orders"
    __table_args__ = (
        CheckConstraint("total_cost >= 0", name="check_order_cost_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mechanic_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String, nullable=False, default="Pending")  # Pending, In Progress, Completed
    notes = Column(String, nullable=True)
    total_cost = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="work_orders")
    order_services = relationship("OrderService", back_populates="work_order", cascade="all, delete-orphan")
    order_parts = relationship("OrderPart", back_populates="work_order", cascade="all, delete-orphan")


class OrderService(Base):
    __tablename__ = "order_services"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_order_service_qty_positive"),
    )

    order_id = Column(Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="RESTRICT"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)

    work_order = relationship("WorkOrder", back_populates="order_services")
    service = relationship("ServiceItem")


class OrderPart(Base):
    __tablename__ = "order_parts"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_order_part_qty_positive"),
    )

    order_id = Column(Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), primary_key=True)
    part_id = Column(Integer, ForeignKey("parts.id", ondelete="RESTRICT"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)

    work_order = relationship("WorkOrder", back_populates="order_parts")
    part = relationship("Part")