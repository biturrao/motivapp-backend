"""
Script para verificar la conexión a Azure PostgreSQL
Ejecuta este script para confirmar que las variables de entorno están correctas
"""

import os
import sys
from sqlalchemy import create_engine, text

def test_database_connection():
    """Prueba la conexión a la base de datos Azure PostgreSQL"""
    
    print("🔍 Verificando variables de entorno...")
    
    # Intentar obtener DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    # Si no existe, intentar construir desde variables individuales
    if not database_url:
        db_host = os.getenv("DB_HOST")
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_pass = os.getenv("DB_PASS")
        
        if all([db_host, db_name, db_user, db_pass]):
            database_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}?sslmode=require"
            print(f"✅ DATABASE_URL construida desde variables individuales")
        else:
            print("❌ ERROR: No se encontraron las variables de entorno necesarias")
            print("\nVariables faltantes:")
            if not db_host: print("  - DB_HOST")
            if not db_name: print("  - DB_NAME")
            if not db_user: print("  - DB_USER")
            if not db_pass: print("  - DB_PASS")
            return False
    else:
        print(f"✅ DATABASE_URL encontrada")
    
    # Verificar otras variables requeridas
    required_vars = {
        "SECRET_KEY": os.getenv("SECRET_KEY"),
        "ALGORITHM": os.getenv("ALGORITHM"),
        "ACCESS_TOKEN_EXPIRE_MINUTES": os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"),
        "PSYCHOLOGIST_INVITE_KEY": os.getenv("PSYCHOLOGIST_INVITE_KEY"),
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        print(f"\n⚠️ ADVERTENCIA: Faltan las siguientes variables:")
        for var in missing_vars:
            print(f"  - {var}")
    else:
        print("✅ Todas las variables de entorno requeridas están presentes")
    
    # Intentar conectar a la base de datos
    print(f"\n🔌 Intentando conectar a la base de datos...")
    print(f"   Host: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'No detectado'}")
    
    try:
        # Crear engine con configuración para Azure
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={
                "sslmode": "require",
                "connect_timeout": 10,
            }
        )
        
        # Intentar una consulta simple
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Conexión exitosa!")
            print(f"   Versión de PostgreSQL: {version}")
            
        # Verificar tablas existentes
        with engine.connect() as connection:
            result = connection.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
            ))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"\n📋 Tablas encontradas ({len(tables)}):")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("\n⚠️ No se encontraron tablas. Puede que necesites ejecutar las migraciones.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos:")
        print(f"   {str(e)}")
        print("\n💡 Posibles soluciones:")
        print("   1. Verifica que la contraseña sea correcta")
        print("   2. Confirma que el firewall de Azure PostgreSQL permite tu conexión")
        print("   3. Asegúrate de que el servidor de base de datos esté activo")
        print("   4. Verifica que la URL de conexión tenga el formato correcto")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST DE CONEXIÓN A AZURE POSTGRESQL")
    print("=" * 60)
    print()
    
    success = test_database_connection()
    
    print()
    print("=" * 60)
    if success:
        print("✅ RESULTADO: Todo está configurado correctamente!")
        sys.exit(0)
    else:
        print("❌ RESULTADO: Hay problemas de configuración")
        print("\nRevisa la documentación en AZURE_ENV_VARIABLES.md")
        sys.exit(1)
