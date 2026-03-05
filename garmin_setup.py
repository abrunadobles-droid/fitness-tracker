"""
Formulario para conectar cuenta de Garmin
Flujo de 2 fases: Login SSO → MFA (si necesario) → OAuth exchange
"""
import streamlit as st
from datetime import datetime
from crypto import encrypt
from auth import get_supabase, get_user_id
from garmin_auth import garmin_login, garmin_verify_mfa, garmin_connect_with_ticket


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

    # Check if we're in MFA phase (Phase 2)
    mfa_phase = st.session_state.get("_garmin_mfa_session") is not None

    if mfa_phase:
        # ---- PHASE 2: MFA Code Input ----
        st.markdown("""
        <div class="mfa-note">
        ⚠️ TU CUENTA DE GARMIN TIENE VERIFICACION DE 2 PASOS (MFA).<br>
        INGRESA EL CODIGO DE TU APP DE AUTENTICACION.
        </div>
        """, unsafe_allow_html=True)

        with st.form("garmin_mfa_form"):
            mfa_code = st.text_input(
                "Codigo MFA / 2FA",
                placeholder="123456",
                key="garmin_mfa_input",
                max_chars=10,
            )
            mfa_submitted = st.form_submit_button(
                "Verificar Codigo", use_container_width=True
            )

        # Cancel button outside form
        if st.button("Cancelar", use_container_width=True):
            st.session_state["_garmin_mfa_session"] = None
            st.session_state.pop("_garmin_email_tmp", None)
            st.session_state.pop("_garmin_pwd_tmp", None)
            st.rerun()

        if mfa_submitted:
            if not mfa_code or not mfa_code.strip():
                st.error("Ingresa el codigo MFA")
            else:
                with st.spinner("Verificando codigo MFA..."):
                    try:
                        mfa_session = st.session_state["_garmin_mfa_session"]
                        email_tmp = st.session_state.get("_garmin_email_tmp", "")
                        pwd_tmp = st.session_state.get("_garmin_pwd_tmp", "")

                        # Phase 2: Submit MFA code → get ticket
                        ticket = garmin_verify_mfa(mfa_session, mfa_code.strip())

                        # Phase 3: Exchange ticket → OAuth tokens
                        client = garmin_connect_with_ticket(email_tmp, pwd_tmp, ticket)

                        # Save to Supabase
                        _save_garmin_connection(client, email_tmp, pwd_tmp)

                        # Clean up MFA state
                        st.session_state["_garmin_mfa_session"] = None
                        st.session_state.pop("_garmin_email_tmp", None)
                        st.session_state.pop("_garmin_pwd_tmp", None)

                        st.success("Garmin conectado exitosamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    else:
        # ---- PHASE 1: Email/Password Login ----
        with st.form("garmin_connect_form"):
            garmin_email = st.text_input(
                "Email de Garmin",
                placeholder="tu@email.com",
                key="garmin_email",
            )
            garmin_password = st.text_input(
                "Password de Garmin",
                type="password",
                key="garmin_pwd",
            )
            submitted = st.form_submit_button(
                "Conectar Garmin", use_container_width=True
            )

        if submitted:
            if not garmin_email or not garmin_password:
                st.error("Ingresa email y password de Garmin")
            else:
                with st.spinner("Conectando con Garmin..."):
                    try:
                        # Phase 1: SSO Login
                        result = garmin_login(
                            garmin_email.strip(),
                            garmin_password,
                        )

                        if result.get("mfa_required"):
                            # MFA needed → save session and switch to Phase 2
                            st.session_state["_garmin_mfa_session"] = result["session"]
                            st.session_state["_garmin_email_tmp"] = garmin_email.strip()
                            st.session_state["_garmin_pwd_tmp"] = garmin_password
                            st.rerun()
                        else:
                            # No MFA → exchange ticket directly
                            ticket = result["ticket"]
                            client = garmin_connect_with_ticket(
                                garmin_email.strip(),
                                garmin_password,
                                ticket,
                            )
                            _save_garmin_connection(
                                client, garmin_email.strip(), garmin_password
                            )
                            st.success("Garmin conectado exitosamente!")
                            st.rerun()

                    except Exception as e:
                        st.error(f"Error al conectar: {str(e)}")

    st.markdown("""
    <div class="privacy-note">
    🔒 TUS CREDENCIALES SE ALMACENAN ENCRIPTADAS (AES-128).<br>
    SOLO SE USAN PARA SINCRONIZAR TUS DATOS DE FITNESS.<br>
    PUEDES DESCONECTAR TU CUENTA EN CUALQUIER MOMENTO.
    </div>
    """, unsafe_allow_html=True)

    return False


def _save_garmin_connection(client, email, password):
    """Guarda la conexion de Garmin en Supabase."""
    token_string = client.garth.dumps()
    supabase = get_supabase()
    user_id = get_user_id()

    supabase.table("garmin_connections").insert({
        "user_id": user_id,
        "garmin_email": email,
        "garmin_password_encrypted": encrypt(password),
        "garmin_tokens": token_string,
        "tokens_updated_at": datetime.utcnow().isoformat(),
    }).execute()


def disconnect_garmin():
    """Desconecta la cuenta de Garmin del usuario."""
    supabase = get_supabase()
    user_id = get_user_id()

    supabase.table("garmin_connections").delete().eq(
        "user_id", user_id
    ).execute()
