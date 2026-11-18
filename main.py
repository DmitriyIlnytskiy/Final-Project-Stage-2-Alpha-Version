from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pathlib import Path
from typing import List
from sqlalchemy.orm import Session
from database import engine, Base, get_db, SessionLocal
from models import User, ServiceCategory, ServiceItem, Part, Vehicle, WorkOrder, OrderService, OrderPart
from schemas import (
    UserCreate, UserResponse, Token, CategoryCreate, CategoryResponse,
    ServiceCreate, ServiceResponse, PartCreate, PartResponse,
    VehicleCreate, VehicleResponse, WorkOrderCreate, WorkOrderAssign,
    WorkOrderStatusUpdate, AddOrderService, AddOrderPart, WorkOrderResponse
)
from auth import get_password_hash, verify_password, create_access_token, get_current_user, require_role

# Recreate or ensure all Beta tables exist in PostgreSQL
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vehicle Fleet & Service Hub API — Beta v1.0", version="1.0.0")

# Seed default hierarchical categories, services, and parts if empty
def seed_initial_catalog():
    db = SessionLocal()
    try:
        if db.query(ServiceCategory).count() == 0:
            root_cat = ServiceCategory(name="Maintenance & Diagnostics", description="Scheduled vehicle maintenance")
            db.add(root_cat)
            db.commit()
            db.refresh(root_cat)

            sub_cat = ServiceCategory(name="Engine & Fluids", description="Oil, filters, and engine tune-ups", parent_id=root_cat.id)
            db.add(sub_cat)
            db.commit()
            db.refresh(sub_cat)

            db.add_all([
                ServiceItem(title="Full Synthetic Oil & Filter Change", category_id=sub_cat.id, base_price=45.0),
                ServiceItem(title="OBD-II Computer Diagnostics", category_id=root_cat.id, base_price=30.0),
            ])
            db.add_all([
                Part(part_code="FLT-OIL-01", name="OEM Oil Filter", price=12.5, stock_quantity=25),
                Part(part_code="OIL-5W40-4L", name="Synthetic Motor Oil 5W-40 (4L)", price=38.0, stock_quantity=15),
            ])
            db.commit()
    finally:
        db.close()

seed_initial_catalog()

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    html_path = Path(__file__).parent / "templates" / "index.html"
    return html_path.read_text(encoding="utf-8")

# --- AUTHENTICATION ---
@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
        "user_id": user.id
    }

@app.get("/users/mechanics", response_model=List[UserResponse])
def list_mechanics(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == "mechanic").all()

# --- CATALOG & INVENTORY (Public Read / Admin Write) ---
@app.get("/catalog/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(ServiceCategory).all()

@app.get("/catalog/services", response_model=List[ServiceResponse])
def get_services(db: Session = Depends(get_db)):
    return db.query(ServiceItem).all()

@app.post("/catalog/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(item: ServiceCreate, current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    srv = ServiceItem(**item.model_dump())
    db.add(srv)
    db.commit()
    db.refresh(srv)
    return srv

@app.get("/catalog/parts", response_model=List[PartResponse])
def get_parts(db: Session = Depends(get_db)):
    return db.query(Part).all()

@app.post("/catalog/parts", response_model=PartResponse, status_code=status.HTTP_201_CREATED)
def create_part(part: PartCreate, current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    if db.query(Part).filter(Part.part_code == part.part_code).first():
        raise HTTPException(status_code=400, detail="Part code already exists")
    new_part = Part(**part.model_dump())
    db.add(new_part)
    db.commit()
    db.refresh(new_part)
    return new_part

# --- VEHICLES (Client Role) ---
@app.get("/vehicles/my", response_model=List[VehicleResponse])
def get_my_vehicles(current_user: User = Depends(require_role(["client"])), db: Session = Depends(get_db)):
    return db.query(Vehicle).filter(Vehicle.owner_id == current_user.id).all()

@app.post("/vehicles/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(vehicle_data: VehicleCreate, current_user: User = Depends(require_role(["client"])), db: Session = Depends(get_db)):
    if db.query(Vehicle).filter(Vehicle.vin == vehicle_data.vin).first():
        raise HTTPException(status_code=400, detail="Vehicle with this VIN already exists")
    new_vehicle = Vehicle(**vehicle_data.model_dump(), owner_id=current_user.id)
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle

# --- WORK ORDERS (Role-Specific Access) ---
@app.post("/orders/", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
def create_work_order(order_data: WorkOrderCreate, current_user: User = Depends(require_role(["client"])), db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == order_data.vehicle_id, Vehicle.owner_id == current_user.id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or does not belong to you")
    new_order = WorkOrder(vehicle_id=vehicle.id, client_id=current_user.id, notes=order_data.notes, status="Pending")
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@app.get("/orders/", response_model=List[WorkOrderResponse])
def list_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "admin":
        return db.query(WorkOrder).all()
    elif current_user.role == "mechanic":
        return db.query(WorkOrder).filter(WorkOrder.mechanic_id == current_user.id).all()
    else:
        return db.query(WorkOrder).filter(WorkOrder.client_id == current_user.id).all()

@app.patch("/orders/{order_id}/assign", response_model=WorkOrderResponse)
def assign_mechanic(order_id: int, payload: WorkOrderAssign, current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Work order not found")
    mechanic = db.query(User).filter(User.id == payload.mechanic_id, User.role == "mechanic").first()
    if not mechanic:
        raise HTTPException(status_code=400, detail="Target user is not a valid mechanic")
    order.mechanic_id = mechanic.id
    order.status = "In Progress"
    db.commit()
    db.refresh(order)
    return order

@app.patch("/orders/{order_id}/status", response_model=WorkOrderResponse)
def update_order_status(order_id: int, payload: WorkOrderStatusUpdate, current_user: User = Depends(require_role(["mechanic", "admin"])), db: Session = Depends(get_db)):
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Work order not found")
    if current_user.role == "mechanic" and order.mechanic_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not assigned to this work order")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order

@app.post("/orders/{order_id}/services", response_model=WorkOrderResponse)
def attach_service_to_order(order_id: int, payload: AddOrderService, current_user: User = Depends(require_role(["mechanic", "admin"])), db: Session = Depends(get_db)):
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    service = db.query(ServiceItem).filter(ServiceItem.id == payload.service_id).first()
    if not order or not service:
        raise HTTPException(status_code=404, detail="Order or Service not found")
    if current_user.role == "mechanic" and order.mechanic_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not assigned to this work order")

    link = db.query(OrderService).filter_by(order_id=order.id, service_id=service.id).first()
    if link:
        link.quantity += payload.quantity
    else:
        db.add(OrderService(order_id=order.id, service_id=service.id, quantity=payload.quantity))

    order.total_cost += service.base_price * payload.quantity
    db.commit()
    db.refresh(order)
    return order

@app.post("/orders/{order_id}/parts", response_model=WorkOrderResponse)
def attach_part_to_order(order_id: int, payload: AddOrderPart, current_user: User = Depends(require_role(["mechanic", "admin"])), db: Session = Depends(get_db)):
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    part = db.query(Part).filter(Part.id == payload.part_id).first()
    if not order or not part:
        raise HTTPException(status_code=404, detail="Order or Part not found")
    if current_user.role == "mechanic" and order.mechanic_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not assigned to this work order")
    if part.stock_quantity < payload.quantity:
        raise HTTPException(status_code=400, detail="Insufficient part stock")

    part.stock_quantity -= payload.quantity
    link = db.query(OrderPart).filter_by(order_id=order.id, part_id=part.id).first()
    if link:
        link.quantity += payload.quantity
    else:
        db.add(OrderPart(order_id=order.id, part_id=part.id, quantity=payload.quantity))

    order.total_cost += part.price * payload.quantity
    db.commit()
    db.refresh(order)
    return order