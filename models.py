from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from database import Base
import datetime

class IncidentCategory(Base):
    __tablename__ = "incident_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    danger_weight = Column(Float, default=1.0)

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    category_id = Column(Integer, ForeignKey("incident_categories.id"))
    title = Column(String)
    address_text = Column(String)
    geom = Column(Geometry('POINT', srid=4326))
    incident_date = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    source_url = Column(String, unique=True)
    source = Column(String(50)) 