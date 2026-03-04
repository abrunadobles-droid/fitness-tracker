"""
Formulario para conectar cuenta de Garmin
"""
import streamlit as st
from datetime import datetime
from garminconnect import Garmin
from crypto import encrypt, decrypt
from auth import get_supabase, get_user_id


def check_garmin_connection():
    """Verifica si el usuario tiene Garmin conectado. Retorna True si si."""
    supabase = get_supabase()
    user_id = get_user_id()

    result = supabase.table("garmin_connections").select("id").eq(
        "user_id", user_id
    ).execute()

    return bool(result.data)


def show_garmin_connect_form():
    """Muestra formulario para conectar Garmin. Retorna True si ya esta conectado."""
    if check_garmin_connection():
        return True

    st.markdown("""
    <style>
    .garmin-title {
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 2rem !important;
        letter-spacing: 3px !important;
        color: #fff !important;
        text-align: center;
        margin-bottom: 8px;
    }
    .garmin-info {
        font-family: 'Space Mono', monospace;
        font-size: 0.6rem;
        color: #888;
        text-align: center;
        letter-spacing: 1px;
        margin-bottom: 24px;
        line-height: 1.6;
    }
    .privacy-note {
        font-family: 'Space Mono', monospace;
        font-size: 0.55rem;
        color: #555;
        background: #0d0d0d;
        border: 1px solid #1a1a1a;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 16px;
        line-height: 1.5;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)
    st.markdown('<div class="garmin-title">CONECTA TU GARMIN</div>', unsafe_allow_html=True)
    st.markdown('<div class="garmin-info">Ingresa tus credenciales de Garmin Connect<br>para sincronizar tus datos de fitness</div>', unsafe_allow_html=True)

    garmin_email = st.text_input("Email de Garmin", placeholder="tu@email.com")
    garmin_password = st.text_input("Password de Garmin", type="password")

    if st.button("Conectar Garmin", use_container_width=True):
        if not garmin_email or not garmin_password:
            st.error("Ingresa email y password de Garmin")
        else:
            with st.spinner("Verificando credenciales de Garmin..."):
                try:
                    # Verificar que las credenciales funcionan
                    client = Garmin(garmin_email, garmin_password)
                    client.login()

                    # Serializar tokens de sesion
                    token_string = client.garth.dumps()

                    # Guardar en Supabase (password encriptado)
                    supabase = get_supabase()
                    user_id = get_user_id()

                    supabase.table("garmin_connections").insert({
                        "user_id": user_id,
                        "garmin_email": garmin_email,
                        "garmin_password_encrypted": encrypt(garmin_password),
                        "garmin_tokens": token_string,
                        "tokens_updated_at": datetime.utcnow().isoformat()
                    }).execute()

                    st.success("Garmin conectado exitosamente!")
                    st.rerun()
                except Exception as e:
                    error_msg = str(e)
                    if "401" in error_msg or "Unauthorized" in error_msg:
                        st.error("Credenciales de Garmin incorrectas. Verifica tu email y password.")
                    else:
                        st.error(f"Error al conectar: {error_msg}")

    st.markdown("""
    <div class="privacy-note">
    🔒 TUS CREDENCIALES SE ALMACENAN ENCRIPTADAS (AES-128).<br>
    SOLO SE USAN PARA SINCRONIZAR TUS DATOS DE FITNESS.<br>
    PUEDES DESCONECTAR TU CUENTA EN CUALQUIER MOMENTO.
    </div>
    """, unsafe_allow_html=True)

    return False


def disconnect_garmin():
    """Desconecta la cuenta de Garmin del usuario."""
    supabase = get_supabase()
    user_id = get_user_id()

    supabase.table("garmin_connections").delete().eq(
        "user_id", user_id
    ).execute()
