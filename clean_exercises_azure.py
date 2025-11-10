"""
Script para conectarse a Azure PostgreSQL y limpiar ejercicios antiguos
Ejecutar: python clean_exercises_azure.py
"""
import os
import psycopg2
from psycopg2 import sql
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CONFIGURACIÓN - Obtener de variables de entorno o configurar aquí
DB_HOST = os.getenv("DB_HOST", "motivapp-backend-server.postgres.database.azure.com")
DB_NAME = os.getenv("DB_NAME", "motivapp-backend-database")
DB_USER = os.getenv("DB_USER", "motivappadmin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # Configurar con variable de entorno
DB_PORT = os.getenv("DB_PORT", "5432")

# Lista de ejercicios que queremos mantener (los 3 nuevos)
EXERCISES_TO_KEEP = [
    "Pasos que Exhalan",
    "Anclaje Corazón-Respira",
    "Escaneo Amable 60"
]


def connect_to_azure():
    """Conectar a Azure PostgreSQL"""
    try:
        logger.info(f"🔄 Conectando a {DB_HOST}...")
        
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            sslmode='require'
        )
        
        logger.info("✅ Conexión exitosa a Azure PostgreSQL")
        return conn
    
    except Exception as e:
        logger.error(f"❌ Error conectando a Azure PostgreSQL: {e}")
        return None


def clean_exercises(conn, delete_all=False):
    """
    Limpiar ejercicios de la base de datos
    
    Args:
        conn: Conexión a PostgreSQL
        delete_all: Si es True, elimina TODO. Si es False, solo elimina ejercicios antiguos
    """
    cursor = conn.cursor()
    
    try:
        # 1. Verificar ejercicios actuales
        logger.info("📊 Verificando ejercicios actuales...")
        cursor.execute("SELECT id, name, recommended_state FROM wellness_exercises ORDER BY id;")
        exercises = cursor.fetchall()
        
        logger.info(f"Total de ejercicios encontrados: {len(exercises)}")
        for ex_id, name, state in exercises:
            logger.info(f"  - [{ex_id}] {name} ({state})")
        
        if delete_all:
            # Eliminar TODO
            logger.info("\n🗑️ ELIMINANDO TODOS los ejercicios...")
            
            cursor.execute("DELETE FROM exercise_completions;")
            deleted_completions = cursor.rowcount
            logger.info(f"  ✅ Eliminadas {deleted_completions} completaciones")
            
            cursor.execute("DELETE FROM wellness_exercises;")
            deleted_exercises = cursor.rowcount
            logger.info(f"  ✅ Eliminados {deleted_exercises} ejercicios")
            
        else:
            # Eliminar solo ejercicios antiguos
            logger.info("\n🗑️ Eliminando ejercicios antiguos...")
            
            # Primero, eliminar completaciones de ejercicios antiguos
            cursor.execute("""
                DELETE FROM exercise_completions 
                WHERE exercise_id NOT IN (
                    SELECT id FROM wellness_exercises 
                    WHERE name = ANY(%s)
                );
            """, (EXERCISES_TO_KEEP,))
            deleted_completions = cursor.rowcount
            logger.info(f"  ✅ Eliminadas {deleted_completions} completaciones antiguas")
            
            # Luego, eliminar ejercicios antiguos
            cursor.execute("""
                DELETE FROM wellness_exercises 
                WHERE name != ALL(%s);
            """, (EXERCISES_TO_KEEP,))
            deleted_exercises = cursor.rowcount
            logger.info(f"  ✅ Eliminados {deleted_exercises} ejercicios antiguos")
        
        # Commit cambios
        conn.commit()
        
        # Verificar resultado
        logger.info("\n✅ Verificando resultado...")
        cursor.execute("SELECT COUNT(*) FROM wellness_exercises;")
        total_exercises = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM exercise_completions;")
        total_completions = cursor.fetchone()[0]
        
        logger.info(f"  📊 Ejercicios restantes: {total_exercises}")
        logger.info(f"  📊 Completaciones restantes: {total_completions}")
        
        if total_exercises == 0:
            logger.info("\n🎉 Base de datos limpiada exitosamente!")
            logger.info("⚠️  IMPORTANTE: Reinicia la aplicación en Azure para que se carguen los 3 nuevos ejercicios.")
            logger.info("   Comando: az webapp restart --name motivapp-backend --resource-group MetaMindApp")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Error limpiando ejercicios: {e}")
        conn.rollback()
        return False
    
    finally:
        cursor.close()


def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("🧹 Script de Limpieza de Ejercicios - Azure PostgreSQL")
    logger.info("=" * 60)
    
    # Verificar que tenemos el password
    if not DB_PASSWORD:
        logger.error("❌ Error: DB_PASSWORD no configurado")
        logger.info("Configura la variable de entorno DB_PASSWORD o edita el script")
        logger.info("Ejemplo: set DB_PASSWORD=tu_password_aqui")
        return
    
    # Conectar
    conn = connect_to_azure()
    if not conn:
        return
    
    try:
        # Preguntar al usuario (si estás ejecutando interactivamente)
        logger.info("\n⚠️  OPCIONES DE LIMPIEZA:")
        logger.info("1. Eliminar TODOS los ejercicios (recomendado)")
        logger.info("2. Eliminar solo ejercicios antiguos (mantener los 3 nuevos si existen)")
        
        # Por defecto, eliminar TODO
        delete_all = True  # Cambiar a False si quieres mantener ejercicios existentes
        
        # Ejecutar limpieza
        success = clean_exercises(conn, delete_all=delete_all)
        
        if success:
            logger.info("\n✅ ¡Proceso completado exitosamente!")
        else:
            logger.error("\n❌ Hubo errores durante el proceso")
    
    finally:
        conn.close()
        logger.info("\n🔒 Conexión cerrada")


if __name__ == "__main__":
    main()
