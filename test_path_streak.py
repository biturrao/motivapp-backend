"""
Script de prueba para verificar el cálculo de path streak.
Simula datos de progreso del usuario en el path.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.crud.crud_dashboard import get_path_streak
from app.models.user_progress import UserContentProgress, UserLessonProgress

def test_path_streak(user_id: int = 1):
    """
    Prueba el cálculo de racha del path.
    """
    db: Session = SessionLocal()
    
    try:
        # Calcular racha actual
        streak = get_path_streak(db=db, user_id=user_id)
        print(f"🔥 Path Streak para usuario {user_id}: {streak} días")
        
        # Mostrar últimos accesos
        print("\n📊 Últimos accesos a contenidos:")
        recent_content = (
            db.query(UserContentProgress)
            .filter(UserContentProgress.user_id == user_id)
            .order_by(UserContentProgress.last_accessed.desc())
            .limit(10)
            .all()
        )
        for progress in recent_content:
            print(f"  - Content ID {progress.content_id}: {progress.last_accessed}")
        
        print("\n📚 Últimos accesos a lecciones:")
        recent_lessons = (
            db.query(UserLessonProgress)
            .filter(UserLessonProgress.user_id == user_id)
            .order_by(UserLessonProgress.last_accessed.desc())
            .limit(10)
            .all()
        )
        for progress in recent_lessons:
            print(f"  - Lesson ID {progress.lesson_id}: {progress.last_accessed}")
        
    finally:
        db.close()


def simulate_streak_data(user_id: int = 1, days: int = 5):
    """
    Simula datos de progreso para crear una racha.
    """
    db: Session = SessionLocal()
    
    try:
        today = datetime.now()
        
        print(f"\n🎯 Simulando {days} días de racha para usuario {user_id}...")
        
        # Crear accesos consecutivos
        for i in range(days):
            access_date = today - timedelta(days=i)
            
            # Crear progreso de contenido
            content_progress = UserContentProgress(
                user_id=user_id,
                content_id=1,  # Usar contenido existente
                completed=False,
                last_accessed=access_date
            )
            db.add(content_progress)
            
            print(f"  ✅ Día {i+1}: {access_date.date()}")
        
        db.commit()
        print("\n✨ Datos simulados exitosamente!")
        
        # Verificar racha
        test_path_streak(user_id)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "simulate":
            user_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            simulate_streak_data(user_id, days)
        else:
            user_id = int(sys.argv[1])
            test_path_streak(user_id)
    else:
        test_path_streak()
