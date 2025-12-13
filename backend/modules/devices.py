from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from typing import Optional
from sqlmodel import select, SQLModel, Field
from database_sql import SessionDep

router = APIRouter()

class DeviceBase(SQLModel):
    device_id: str = Field(unique=True, index=True)
    patient_id: str 
    model: str
    vital_type: str
    last_active: datetime|None = Field(default=None)

class Device(DeviceBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

class DeviceUpdate(SQLModel):
    model: str | None = None
    patient_id: str | None = None

def update_ts(device_id:str, last_ts: datetime,  session:SessionDep):
    device_old = session.exec(select(Device).where(Device.device_id == device_id)).first()
    if not device_old:
        raise HTTPException(status_code=404, detail="Device not found")
    device_old.last_active=last_ts
    session.add(device_old)
    session.commit()
    session.refresh(device_old)

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

@router.get("/")
def read_device(session: SessionDep):
    devices = session.exec(select(Device)).all()
    if not devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    response = []

    for d in devices:
        if d.last_active is not None:
           d.last_active = d.last_active.replace(tzinfo=timezone.utc)
           diff_minutes = (datetime.now(timezone.utc) - d.last_active).total_seconds() / 60
           status = "active" if diff_minutes <= 5 else "inactive"
        else:
            status = "Unknown"
        response.append({
            "device_id": d.device_id,
            "model": d.model,
            "patient_id": d.patient_id,
            "vital_type": d.vital_type,
            "last_active": d.last_active,
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