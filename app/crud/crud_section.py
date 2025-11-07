from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.section import Section
from app.schemas.section import SectionCreate, SectionUpdate


def get_section(db: Session, section_id: int) -> Optional[Section]:
    """Get a single section by ID"""
    return db.query(Section).filter(Section.id == section_id).first()


def get_all_sections(db: Session) -> List[Section]:
    """Get all sections, ordered by order field"""
    return db.query(Section).order_by(Section.order).all()


def create_section(db: Session, section: SectionCreate) -> Section:
    """Create a new section"""
    db_section = Section(**section.dict())
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section


def update_section(db: Session, section_id: int, section: SectionUpdate) -> Optional[Section]:
    """Update a section"""
    db_section = get_section(db, section_id)
    if db_section:
        update_data = section.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_section, field, value)
        db.commit()
        db.refresh(db_section)
    return db_section


def delete_section(db: Session, section_id: int) -> bool:
    """Delete a section"""
    db_section = get_section(db, section_id)
    if db_section:
        db.delete(db_section)
        db.commit()
        return True
    return False
