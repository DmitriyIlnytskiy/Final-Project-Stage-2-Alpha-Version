from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal, List

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)
    full_name: str = Field(min_length=2)
    role: Literal["client", "mechanic", "admin"] = "client"

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
    role: str
    full_name: str
    user_id: int

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryResponse(CategoryCreate):
    id: int
    class Config:
        from_attributes = True

class ServiceCreate(BaseModel):
    title: str
    category_id: int
    base_price: float = Field(gt=0)

class ServiceResponse(ServiceCreate):
    id: int
    class Config:
        from_attributes = True

class PartCreate(BaseModel):
    part_code: str
    name: str
    price: float = Field(gt=0)
    stock_quantity: int = Field(ge=0)

class PartResponse(PartCreate):
    id: int
    class Config:
        from_attributes = True

class VehicleCreate(BaseModel):
    vin: str = Field(min_length=5, max_length=17)
    model: str
    year: int = Field(ge=1900, le=2030)

class VehicleResponse(VehicleCreate):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

class WorkOrderCreate(BaseModel):
    vehicle_id: int
    notes: Optional[str] = "Routine diagnostics and maintenance"

class WorkOrderAssign(BaseModel):
    mechanic_id: int

class WorkOrderStatusUpdate(BaseModel):
    status: Literal["Pending", "In Progress", "Completed"]

class AddOrderService(BaseModel):
    service_id: int
    quantity: int = Field(default=1, gt=0)

class AddOrderPart(BaseModel):
    part_id: int
    quantity: int = Field(default=1, gt=0)

class WorkOrderResponse(BaseModel):
    id: int
    vehicle_id: int
    client_id: int
    mechanic_id: Optional[int]
    status: str
    notes: Optional[str]
    total_cost: float

    class Config:
        from_attributes = True