from sqlalchemy.orm import Session
from core.models import Incident


def get_incident_by_url(db: Session, url: str) -> Incident | None:
    """Шукає інцидент за унікальним посиланням."""
    return db.query(Incident).filter(Incident.source_url == url).first()


def create_incident(db: Session, incident_data: dict) -> Incident:
    """Створює новий запис інциденту в базі даних."""
    new_incident = Incident(
        category_id=incident_data["category_id"],
        title=incident_data["title"],
        address_text=incident_data["address_text"],
        geom=incident_data["geom"],
        incident_date=incident_data["incident_date"],
        source_url=incident_data["source_url"],
        source=incident_data["source"],
    )
    db.add(new_incident)
    db.commit()
    return new_incident