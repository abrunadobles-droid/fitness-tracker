"""
Autenticacion con Supabase - Login, Registro, Logout
"""
import streamlit as st
from supabase import create_client


def get_supabase():
    """Inicializa cliente de Supabase con token del usuario para RLS."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)

    if "access_token" in st.session_state and st.session_state.access_token:
        supabase.postgrest.auth(st.session_state.access_token)

    return supabase


def show_auth_page():
    """Muestra pagina de login/registro. Retorna True si el usuario esta autenticado."""
    if "user" in st.session_state and st.session_state.user:
        return True

    st.title("HABIT TRACKER")
    st.caption("TRACK YOUR HABITS")

    tab1, tab2 = st.tabs(["LOGIN", "REGISTRO"])

    with tab1:
        email = st.text_input("Email", key="login_email", placeholder="tu@email.com")
        password = st.text_input("Password", type="password", key="login_pwd")

        if st.button("Iniciar Sesion", use_container_width=True):
            if not email or not password:
                st.error("Ingresa email y password")
            else:
                with st.spinner("Verificando..."):
                    try:
                        supabase = get_supabase()
                        res = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        st.session_state.user = res.user
                        st.session_state.access_token = res.session.access_token
                        st.rerun()
                    except Exception as e:
                        error_msg = str(e)
                        if "Invalid login" in error_msg:
                            st.error("Email o password incorrecto")
                        else:
                            st.error(f"Error: {error_msg}")

    with tab2:
        reg_email = st.text_input("Email", key="reg_email", placeholder="tu@email.com")
        reg_password = st.text_input("Password", type="password", key="reg_pwd")
        reg_password2 = st.text_input("Confirmar Password", type="password", key="reg_pwd2")

        if st.button("Crear Cuenta", use_container_width=True):
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
                            "email": reg_email,
                            "password": reg_password
                        })
                        if res.session:
                            st.session_state.user = res.user
                            st.session_state.access_token = res.session.access_token
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
    """Muestra boton de logout."""
    if st.button("LOGOUT", use_container_width=True):
        st.session_state.user = None
        st.session_state.access_token = None
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
