#!/usr/bin/env python3
"""
Script de setup inicial para Fitness Tracker
"""

import sys
import os
import subprocess


def print_header(text):
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60 + "\n")


def check_python_version():
    """Verifica que Python sea >= 3.7"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Se requiere Python 3.7 o superior")
        print(f"   Tu versión: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor} detectado")
    return True


def install_dependencies():
    """Instala las dependencias de requirements.txt"""
    print_header("Instalando dependencias")
    
    try:
        subprocess.check_call([
            sys.executable, 
            "-m", 
            "pip", 
            "install", 
            "-r", 
            "requirements.txt",
            "--break-system-packages"
        ])
        print("\n✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ Error instalando dependencias")
        print("   Intenta manualmente: pip install -r requirements.txt --break-system-packages")
        return False


def check_config():
    """Verifica que config.py esté configurado"""
    print_header("Verificando configuración")
    
    from config import GARMIN_CONFIG, EXCEL_FILE
    
    warnings = []
    
    # Verificar Garmin
    if not GARMIN_CONFIG.get('email') or not GARMIN_CONFIG.get('password'):
        warnings.append("⚠️  Garmin: Email o password no configurados en config.py")
    else:
        print("✅ Credenciales Garmin configuradas")
    
    # Verificar ruta Excel
    if not os.path.exists(EXCEL_FILE):
        warnings.append(f"⚠️  Excel no encontrado en: {EXCEL_FILE}")
        warnings.append("   Actualiza EXCEL_FILE en config.py")
    else:
        print(f"✅ Excel encontrado: {EXCEL_FILE}")
    
    if warnings:
        print("\n" + "\n".join(warnings))
        return False
    
    return True


def setup_whoop():
    """Configura autenticación WHOOP"""
    print_header("Configuración WHOOP")
    
    print("Para usar WHOOP necesitas autenticarte una vez.")
    print("Esto abrirá tu navegador y guardará los tokens automáticamente.")
    print("\n¿Deseas autenticarte con WHOOP ahora? (s/n): ", end='')
    
    if input().lower() == 's':
        try:
            from whoop_client import test_whoop_connection
            test_whoop_connection()
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    else:
        print("⏭️  Saltando autenticación WHOOP")
        print("   Puedes hacerlo después con: python whoop_client.py")
        return True


def test_garmin():
    """Prueba conexión con Garmin"""
    print_header("Prueba Garmin Connect")
    
    from config import GARMIN_CONFIG
    
    if not GARMIN_CONFIG.get('email') or not GARMIN_CONFIG.get('password'):
        print("⏭️  Saltando - configura Garmin en config.py primero")
        return True
    
    print("¿Deseas probar la conexión con Garmin? (s/n): ", end='')
    
    if input().lower() == 's':
        try:
            from garmin_client import test_garmin_connection
            return test_garmin_connection()
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    else:
        print("⏭️  Saltando prueba Garmin")
        return True


def main():
    print_header("🏃‍♂️ SETUP FITNESS TRACKER")
    
    # 1. Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # 2. Instalar dependencias
    if not install_dependencies():
        sys.exit(1)
    
    # 3. Verificar config
    config_ok = check_config()
    
    # 4. Setup WHOOP
    setup_whoop()
    
    # 5. Test Garmin
    if config_ok:
        test_garmin()
    
    # Resumen final
    print_header("✅ SETUP COMPLETADO")
    
    print("Próximos pasos:\n")
    print("1. Si no configuraste Garmin, edita config.py con tus credenciales")
    print("2. Si no autenticaste WHOOP, ejecuta: python whoop_client.py")
    print("3. Para ver stats del día: python tracker_updater.py")
    print("4. Para actualizar Excel: python tracker_updater.py update")
    print("\n¡Disfruta tu tracker automatizado! 🎉\n")


if __name__ == '__main__':
    main()
