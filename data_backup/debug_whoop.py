"""
Debug WHOOP - Ver datos exactos
"""

from whoop_client_v2 import WhoopClientV2
from datetime import datetime

print("\n" + "="*70)
print("DEBUG WHOOP - ENERO 2026")
print("="*70)

whoop = WhoopClientV2()

# Obtener resumen
summary = whoop.get_monthly_summary(2026, 1)

print("\n📊 RESUMEN OBTENIDO:")
print(f"   Total noches registradas: {len(summary['sleep'])}")
print(f"   Promedio calculado: {summary['avg_sleep_hours']:.2f}h")
print(f"   Días antes 9:30 PM: {summary['days_sleep_before_930pm']}")

print("\n🛌 PRIMERAS 5 NOCHES (para verificar):")
print("-" * 70)

for i, sleep in enumerate(summary['sleep'][:5], 1):
    start_time = sleep.get('start', 'N/A')
    
    # Calcular horas
    if sleep.get('score') and sleep['score'].get('stage_summary'):
        total_ms = sleep['score']['stage_summary'].get('total_in_bed_time_milli', 0)
        hours = total_ms / 3600000
        
        # Parsear hora de inicio
        if start_time != 'N/A':
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            local_time = dt.strftime('%Y-%m-%d %H:%M')
            hour = dt.hour
            minute = dt.minute
            
            # Verificar si es antes de 9:30 PM
            before_930 = "✅ SÍ" if (hour < 21 or (hour == 21 and minute < 30)) else "❌ NO"
        else:
            local_time = "N/A"
            before_930 = "?"
        
        print(f"\nNoche {i}:")
        print(f"   Inicio: {local_time}")
        print(f"   Duración: {hours:.1f}h")
        print(f"   Antes 9:30 PM: {before_930}")

print("\n" + "="*70)

# Verificar con chat de WHOOP
print("\n💬 COMPARACIÓN CON CHAT WHOOP:")
print(f"   Chat WHOOP dice: 7.0h promedio")
print(f"   Nosotros calculamos: {summary['avg_sleep_hours']:.1f}h")
print(f"   Diferencia: {abs(7.0 - summary['avg_sleep_hours']):.1f}h")

if abs(7.0 - summary['avg_sleep_hours']) > 0.5:
    print("\n⚠️  HAY DIFERENCIA SIGNIFICATIVA")
    print("   Posibles causas:")
    print("   1. Estamos usando 'total_in_bed_time' en lugar de 'sleep time'")
    print("   2. Incluimos siestas (naps)")
    print("   3. Zona horaria incorrecta")
else:
    print("\n✅ Los datos coinciden")

# Verificar naps
naps = [s for s in summary['sleep'] if s.get('nap', False)]
print(f"\n😴 Siestas detectadas: {len(naps)}")

# Mostrar estructura de un registro
print("\n📋 ESTRUCTURA DE UN REGISTRO DE SUEÑO:")
if summary['sleep']:
    import json
    print(json.dumps(summary['sleep'][0], indent=2))

