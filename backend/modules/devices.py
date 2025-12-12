from fastapi import APIRouter, HTTPException, Query,Depends
from typing import Annotated, List
from sqlmodel import select, SQLModel, Field
from database_sql import SessionDep
from .time_series import query_last_timestamp_influx
from influx_dependencies import get_query_api

router = APIRouter()

class DeviceBase(SQLModel):
    device_id: str = Field(unique=True, index=True)
    location: str 
    name: str
    quantity_measured: str
    status: str = Field(default="inactive")

class Device(DeviceBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

class DeviceUpdate(SQLModel):
    name: str | None = None
    location: str | None = None
    status: str | None = None

@router.post("/", response_model=DeviceBase)
def create_device(device: DeviceBase, session: SessionDep):
    device_exist = session.exec(select(Device).where(Device.device_id == device.device_id)).first()
    if device_exist:
           raise HTTPException(status_code=400, detail="Device already exists")
           
    db_device = Device.model_validate(device)
    session.add(db_device)
    session.commit()
    session.refresh(db_device)
    return db_device

@router.get("/", response_model=List[DeviceBase])
def read_device(
    session: SessionDep,
    query_api=Depends(get_query_api)):
    devices = session.exec(select(Device)).all()
    if not devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    response = []

    for d in devices:
        status = query_last_timestamp_influx(d.device_id, query_api)
        response.append({
            "device_id": d.device_id,
            "name": d.name,
            "location": d.location,
            "quantity_measured": d.quantity_measured,
            "status": status
        })

    return response
        
@router.delete("/{device_id}")
def delete_device(device_id: str, session: SessionDep):
    device = session.exec(select(Device).where(Device.device_id == device_id)).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    session.delete(device)
    session.commit()
    return {"ok": True}

@router.put("/{device_id}", response_model=DeviceBase)
def update_device(device_id: str, device: DeviceUpdate, session: SessionDep):
    device_old = session.exec(select(Device).where(Device.device_id == device_id)).first()
    if not device_old:
        raise HTTPException(status_code=404, detail="Device not found")
    device_dict = device.model_dump(exclude_unset=True)
    device_old.sqlmodel_update(device_dict)
    session.add(device_old)
    session.commit()
    session.refresh(device_old)
    return device_old