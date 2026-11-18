from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "client"

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class VehicleCreate(BaseModel):
    vin: str
    model: str
    year: int

class VehicleResponse(VehicleCreate):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class WorkOrderCreate(BaseModel):
    vehicle_id: int

class WorkOrderResponse(BaseModel):
    id: int
    vehicle_id: int
    client_id: int
    status: str
    total_cost: float

    class Config:
        from_attributes = True