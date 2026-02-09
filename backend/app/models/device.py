"""Device database model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base


class Device(Base):
    """Device model for SmsForwarder devices."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    ip = Column(String(45), index=True, nullable=False)  # Support IPv6
    port = Column(Integer, default=5000, nullable=False)
    remark = Column(Text, nullable=True)
    api_version = Column(String(10), default="v3")  # v2 or v3
    api_key = Column(String(255), nullable=True)
    last_seen = Column(DateTime, nullable=True)
    battery_level = Column(Integer, nullable=True)  # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, name='{self.name}', ip='{self.ip}')>"
