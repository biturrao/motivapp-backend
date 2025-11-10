from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta

from app.models.metamotivation_energy import MetamotivationEnergy
from app.schemas.wellness import MetamotivationEnergyCreate


def create_energy_record(
    db: Session,
    user_id: int,
    energy_data: MetamotivationEnergyCreate
) -> MetamotivationEnergy:
    """Crear un nuevo registro de energía metamotivacional"""
    db_energy = MetamotivationEnergy(
        user_id=user_id,
        **energy_data.model_dump()
    )
    db.add(db_energy)
    db.commit()
    db.refresh(db_energy)
    return db_energy


def get_energy_records(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[MetamotivationEnergy]:
    """Obtener registros de energía de un usuario"""
    return db.query(MetamotivationEnergy).filter(
        MetamotivationEnergy.user_id == user_id
    ).order_by(
        MetamotivationEnergy.created_at.desc()
    ).offset(skip).limit(limit).all()


def get_energy_record_by_id(
    db: Session,
    energy_id: int
) -> Optional[MetamotivationEnergy]:
    """Obtener un registro de energía por ID"""
    return db.query(MetamotivationEnergy).filter(
        MetamotivationEnergy.id == energy_id
    ).first()


def get_todays_energy_records(
    db: Session,
    user_id: int
) -> List[MetamotivationEnergy]:
    """Obtener registros de energía de hoy para un usuario"""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    return db.query(MetamotivationEnergy).filter(
        and_(
            MetamotivationEnergy.user_id == user_id,
            MetamotivationEnergy.created_at >= today_start
        )
    ).order_by(MetamotivationEnergy.created_at.desc()).all()


def get_energy_stats(
    db: Session,
    user_id: int,
    days: int = 30
) -> dict:
    """
    Obtener estadísticas de energía del usuario en los últimos N días
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    records = db.query(MetamotivationEnergy).filter(
        and_(
            MetamotivationEnergy.user_id == user_id,
            MetamotivationEnergy.created_at >= since
        )
    ).all()
    
    total_records = len(records)
    
    # Contar por estado
    by_state = {}
    for r in records:
        by_state[r.energy_state] = by_state.get(r.energy_state, 0) + 1
    
    # Calcular porcentajes
    percentages = {
        state: round((count / total_records) * 100, 1) if total_records > 0 else 0
        for state, count in by_state.items()
    }
    
    # Estado más frecuente
    most_frequent = max(by_state, key=by_state.get) if by_state else None
    
    return {
        "total_records": total_records,
        "by_state": by_state,
        "percentages": percentages,
        "most_frequent_state": most_frequent,
        "days_analyzed": days
    }


def get_latest_energy_record(
    db: Session,
    user_id: int
) -> Optional[MetamotivationEnergy]:
    """Obtener el último registro de energía del usuario"""
    return db.query(MetamotivationEnergy).filter(
        MetamotivationEnergy.user_id == user_id
    ).order_by(
        MetamotivationEnergy.created_at.desc()
    ).first()
