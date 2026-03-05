"""
Formulario para conectar cuenta de Garmin
Soporta cuentas con MFA/2FA habilitado
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


def _is_mfa_error(error_msg):
    """Detecta si el error es por MFA/2FA requerido."""
    mfa_indicators = [
        "MFA",
        "OAuth1 token is required",
        "EOFError",
        "2FA",
        "two-factor",
        "verification",
    ]
    error_lower = error_msg.lower()
    return any(ind.lower() in error_lower for ind in mfa_indicators)


def _garmin_login(email, password, mfa_code=None):
    """Login a Garmin Connect con soporte MFA.

    Usa garth directamente para pasar prompt_mfa callback.
    Retorna el cliente Garmin autenticado.
    """
    client = Garmin(email, password)

    if mfa_code:
        # Login con codigo MFA via garth
        client.garth.login(email, password, prompt_mfa=lambda: mfa_code)
    else:
        # Login normal - si MFA es requerido y no hay codigo,
        # prompt_mfa default (input()) fallara en el servidor
        client.garth.login(email, password)

    # Setear profile info (normalmente lo hace Garmin.login())
    client.display_name = client.garth.profile["displayName"]
    client.full_name = client.garth.profile["fullName"]

    return client


def show_garmin_connect_form():
    """Muestra formulario para conectar Garmin. Retorna True si ya esta conectado."""
    if check_garmin_connection():
        return True

    st.markdown("""
    <style>
    .garmin-title {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        letter-spacing: 4px !important;
        background: linear-gradient(135deg, #c4b5fd, #7c3aed, #06b6d4) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        text-align: center;
        margin-bottom: 8px;
    }
    .garmin-info {
        font-family: 'Space Mono', monospace;
        font-size: 0.6rem;
        color: #cbd5e1;
        text-align: center;
        letter-spacing: 1px;
        margin-bottom: 24px;
        line-height: 1.6;
    }
    .privacy-note {
        font-family: 'Space Mono', monospace;
        font-size: 0.55rem;
        color: #cbd5e1;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 14px 18px;
        margin-top: 16px;
        line-height: 1.6;
        backdrop-filter: blur(10px);
    }
    .mfa-note {
        font-family: 'Space Mono', monospace;
        font-size: 0.55rem;
        color: #f59e0b;
        background: rgba(245,158,11,0.08);
        border: 1px solid rgba(245,158,11,0.2);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 16px;
        line-height: 1.6;
        backdrop-filter: blur(10px);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="top-gradient"></div>', unsafe_allow_html=True)
    st.markdown('<div class="garmin-title">CONECTA TU GARMIN</div>', unsafe_allow_html=True)
    st.markdown('<div class="garmin-info">Ingresa tus credenciales de Garmin Connect<br>para sincronizar tus datos de fitness</div>', unsafe_allow_html=True)

    # MFA - mostrar aviso si se detecto que la cuenta lo necesita
    mfa_needed = st.session_state.get("_garmin_mfa_needed", False)

    if mfa_needed:
        st.markdown("""
        <div class="mfa-note">
        ⚠️ TU CUENTA DE GARMIN TIENE VERIFICACION DE 2 PASOS (MFA).<br>
        INGRESA EL CODIGO DE TU APP DE AUTENTICACION Y HAZ CLIC EN CONECTAR.
        </div>
        """, unsafe_allow_html=True)

    # Usar st.form para que los valores no se pierdan en mobile
    with st.form("garmin_connect_form"):
        garmin_email = st.text_input(
            "Email de Garmin",
            placeholder="tu@email.com",
            key="garmin_email"
        )
        garmin_password = st.text_input(
            "Password de Garmin",
            type="password",
            key="garmin_pwd"
        )

        mfa_code = ""
        if mfa_needed:
            mfa_code = st.text_input(
                "Codigo MFA / 2FA",
                placeholder="123456",
                key="garmin_mfa_code",
                max_chars=10
            )

        submitted = st.form_submit_button(
            "Conectar Garmin",
            use_container_width=True
        )

    # Procesar fuera del form para poder usar st.spinner y st.rerun
    if submitted:
        if not garmin_email or not garmin_password:
            st.error("Ingresa email y password de Garmin")
        elif mfa_needed and not mfa_code:
            st.error("Ingresa el codigo MFA de tu app de autenticacion")
        else:
            with st.spinner("Verificando credenciales de Garmin..."):
                try:
                    client = _garmin_login(
                        garmin_email.strip(),
                        garmin_password,
                        mfa_code=mfa_code.strip() if mfa_code else None
                    )

                    # Serializar tokens de sesion
                    token_string = client.garth.dumps()

                    # Guardar en Supabase (password encriptado)
                    supabase = get_supabase()
                    user_id = get_user_id()

                    supabase.table("garmin_connections").insert({
                        "user_id": user_id,
                        "garmin_email": garmin_email.strip(),
                        "garmin_password_encrypted": encrypt(garmin_password),
                        "garmin_tokens": token_string,
                        "tokens_updated_at": datetime.utcnow().isoformat()
                    }).execute()

                    # Limpiar estado MFA
                    st.session_state["_garmin_mfa_needed"] = False
                    st.success("Garmin conectado exitosamente!")
                    st.rerun()
                except Exception as e:
                    error_msg = str(e)
                    if _is_mfa_error(error_msg):
                        st.session_state["_garmin_mfa_needed"] = True
                        st.warning(
                            "Tu cuenta de Garmin tiene verificacion de "
                            "2 pasos (MFA). Ingresa el codigo de tu app "
                            "de autenticacion y vuelve a intentar."
                        )
                        st.rerun()
                    elif "401" in error_msg or "Unauthorized" in error_msg:
                        st.error(
                            "Credenciales de Garmin incorrectas. "
                            "Verifica tu email y password."
                        )
                    elif "429" in error_msg or "Too Many" in error_msg:
                        st.error(
                            "Demasiados intentos. Espera unos minutos "
                            "y vuelve a intentar."
                        )
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
