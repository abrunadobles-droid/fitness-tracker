"""
Autenticacion con Supabase - Login, Registro, Logout
Incluye "Recordarme" via localStorage del navegador
"""
import json
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client


def get_supabase():
    """Inicializa cliente de Supabase con token del usuario para RLS."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)

    # Pasar el JWT del usuario para que RLS funcione
    if "access_token" in st.session_state and st.session_state.access_token:
        supabase.postgrest.auth(st.session_state.access_token)

    return supabase


# ---- Funciones de localStorage (Remember Me) ----

def _store_refresh_token(refresh_token):
    """Guarda refresh token en localStorage del navegador."""
    safe_token = json.dumps(refresh_token)
    components.html(f"""
    <script>
    try {{ localStorage.setItem('ht_rt', {safe_token}); }} catch(e) {{}}
    </script>
    """, height=0)


def _clear_refresh_token():
    """Elimina refresh token de localStorage del navegador."""
    components.html("""
    <script>
    try { localStorage.removeItem('ht_rt'); } catch(e) {}
    </script>
    """, height=0)


def try_auto_login():
    """Intenta restaurar sesion desde token guardado en el navegador.

    Usa localStorage + query params como puente JS->Python:
    1. Primera carga: inyecta JS que lee localStorage y redirige con ?_rt=token
    2. Segunda carga: Python lee ?_rt, refresca sesion con Supabase, limpia URL

    Retorna True si la sesion fue restaurada.
    """
    # Ya loggeado
    if "user" in st.session_state and st.session_state.user:
        return True

    # Ya intentamos auto-login en esta sesion
    if st.session_state.get("_auto_login_done"):
        return False

    params = st.query_params
    rt = params.get("_rt")

    if rt:
        # Tenemos refresh token desde localStorage redirect
        st.query_params.clear()
        st.session_state["_auto_login_done"] = True
        try:
            supabase = get_supabase()
            res = supabase.auth.refresh_session(rt)
            if res and res.session:
                st.session_state.user = res.user
                st.session_state.access_token = res.session.access_token
                # Actualizar token guardado (Supabase rota tokens)
                _store_refresh_token(res.session.refresh_token)
                st.rerun()
        except Exception:
            # Token invalido/expirado, limpiar storage
            _clear_refresh_token()
        return False

    # Primera carga - inyectar JS para revisar localStorage
    st.session_state["_auto_login_done"] = True
    components.html("""
    <script>
    try {
        const rt = localStorage.getItem('ht_rt');
        if (rt) {
            const url = new URL(window.parent.location.href);
            if (!url.searchParams.has('_rt')) {
                url.searchParams.set('_rt', rt);
                window.parent.location.replace(url.toString());
            }
        }
    } catch(e) {}
    </script>
    """, height=0)
    return False


def show_auth_page():
    """Muestra pagina de login/registro. Retorna True si el usuario esta autenticado."""
    if "user" in st.session_state and st.session_state.user:
        return True

    # CSS para la pagina de auth (Neon Glass theme)
    st.markdown("""
    <style>
    .auth-title {
        font-family: 'Inter', sans-serif !important;
        font-size: 2.4rem !important;
        font-weight: 800 !important;
        letter-spacing: 6px !important;
        background: linear-gradient(135deg, #c4b5fd, #7c3aed, #06b6d4) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        text-align: center;
        margin-bottom: 8px;
    }
    .auth-subtitle {
        font-family: 'Space Mono', monospace;
        font-size: 0.65rem;
        color: #cbd5e1;
        text-align: center;
        letter-spacing: 3px;
        margin-bottom: 32px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="top-gradient"></div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">HABIT TRACKER</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-subtitle">TRACK YOUR HABITS</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["LOGIN", "REGISTRO"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email", placeholder="tu@email.com")
            password = st.text_input("Password", type="password", key="login_pwd")
            remember = st.checkbox("Recordarme", value=True, key="login_remember")
            login_submitted = st.form_submit_button(
                "Iniciar Sesion", use_container_width=True
            )

        if login_submitted:
            if not email or not password:
                st.error("Ingresa email y password")
            else:
                with st.spinner("Verificando..."):
                    try:
                        supabase = get_supabase()
                        res = supabase.auth.sign_in_with_password({
                            "email": email.strip(),
                            "password": password
                        })
                        st.session_state.user = res.user
                        st.session_state.access_token = res.session.access_token
                        if remember and res.session.refresh_token:
                            _store_refresh_token(res.session.refresh_token)
                        st.rerun()
                    except Exception as e:
                        error_msg = str(e)
                        if "Invalid login" in error_msg:
                            st.error("Email o password incorrecto")
                        else:
                            st.error(f"Error: {error_msg}")

    with tab2:
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="reg_email", placeholder="tu@email.com")
            reg_password = st.text_input("Password", type="password", key="reg_pwd")
            reg_password2 = st.text_input("Confirmar Password", type="password", key="reg_pwd2")
            reg_submitted = st.form_submit_button(
                "Crear Cuenta", use_container_width=True
            )

        if reg_submitted:
            if not reg_email or not reg_password:
                st.error("Ingresa email y password")
            elif reg_password != reg_password2:
                st.error("Los passwords no coinciden")
            elif len(reg_password) < 6:
                st.error("El password debe tener al menos 6 caracteres")
            else:
                with st.spinner("Creando cuenta..."):
                    try:
                        supabase = get_supabase()
                        res = supabase.auth.sign_up({
                            "email": reg_email.strip(),
                            "password": reg_password
                        })
                        # Auto-login si no requiere confirmacion de email
                        if res.session:
                            st.session_state.user = res.user
                            st.session_state.access_token = res.session.access_token
                            # Auto-recordar al registrarse
                            if res.session.refresh_token:
                                _store_refresh_token(res.session.refresh_token)
                            st.success("Cuenta creada!")
                            st.rerun()
                        else:
                            st.success("Cuenta creada. Ya puedes iniciar sesion.")
                    except Exception as e:
                        error_msg = str(e)
                        if "already registered" in error_msg:
                            st.error("Este email ya esta registrado")
                        else:
                            st.error(f"Error: {error_msg}")

    return False


def show_logout_button():
    """Muestra boton de logout. Limpia token guardado."""
    if st.button("LOGOUT", use_container_width=True):
        _clear_refresh_token()
        st.session_state.user = None
        st.session_state.access_token = None
        st.session_state["_auto_login_done"] = False
        st.rerun()


def get_user_id():
    """Retorna el user_id del usuario loggeado."""
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.id
    return None


def get_user_email():
    """Retorna el email del usuario loggeado."""
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.email
    return None
