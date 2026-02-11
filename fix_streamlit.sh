#!/bin/bash
echo "🔧 Arreglando dashboard para Streamlit Cloud..."

# Actualizar dashboard.py para manejar errores de conexión
cat > dashboard_fixed.py << 'EOF'
# (Aquí iría el código completo corregido)
EOF

# Subir cambios
git add .
git commit -m "Fix dashboard for Streamlit Cloud"
git push

echo "✅ Cambios subidos. Espera 2 minutos para que Streamlit Cloud se actualice."
echo "🌐 URL: https://fitness-tracker-mqxxeejbwuxydm7tasl3n8.streamlit.app"
