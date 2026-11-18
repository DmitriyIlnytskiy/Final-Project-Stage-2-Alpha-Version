from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import User, Vehicle, WorkOrder
from schemas import UserCreate, UserResponse, Token, VehicleCreate, VehicleResponse, WorkOrderCreate, WorkOrderResponse
from auth import get_password_hash, verify_password, create_access_token, get_current_user, require_role


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vehicle Fleet & Service Hub API", version="1.0.0")

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
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
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/vehicles/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(vehicle_data: VehicleCreate, current_user: User = Depends(require_role(["client"])), db: Session = Depends(get_db)):
    new_vehicle = Vehicle(
        vin=vehicle_data.vin,
        model=vehicle_data.model,
        year=vehicle_data.year,
        owner_id=current_user.id
    )
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle

@app.post("/orders/", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
def create_work_order(order_data: WorkOrderCreate, current_user: User = Depends(require_role(["client"])), db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == order_data.vehicle_id, Vehicle.owner_id == current_user.id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or does not belong to you")
    
    new_order = WorkOrder(
        vehicle_id=vehicle.id,
        client_id=current_user.id,
        status="Pending"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@app.get("/orders/admin-all", dependencies=[Depends(require_role(["admin", "mechanic"]))])
def get_all_orders(db: Session = Depends(get_db)):
    
    orders = db.query(WorkOrder).all()
    return orders