from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.content import Content
from app.schemas.content import ContentCreate, ContentUpdate


def get_content(db: Session, content_id: int) -> Optional[Content]:
    """Get a single content by ID"""
    return db.query(Content).filter(Content.id == content_id).first()


def get_contents_by_section(db: Session, section_id: int) -> List[Content]:
    """Get all contents for a specific section, ordered by order field"""
    return db.query(Content).filter(
        Content.section_id == section_id
    ).order_by(Content.order).all()


def create_content(db: Session, content: ContentCreate) -> Content:
    """Create a new content"""
    db_content = Content(**content.dict())
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content


def update_content(db: Session, content_id: int, content: ContentUpdate) -> Optional[Content]:
    """Update a content"""
    db_content = get_content(db, content_id)
    if db_content:
        update_data = content.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_content, field, value)
        db.commit()
        db.refresh(db_content)
    return db_content


def delete_content(db: Session, content_id: int) -> bool:
    """Delete a content"""
    db_content = get_content(db, content_id)
    if db_content:
        db.delete(db_content)
        db.commit()
        return True
    return False
