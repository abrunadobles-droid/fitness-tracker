"""
Encripcion/desencripcion de credenciales usando Fernet (AES-128-CBC)
"""
from cryptography.fernet import Fernet
import streamlit as st


def get_fernet():
    """Obtiene instancia de Fernet usando key de Streamlit Secrets."""
    key = st.secrets["encryption"]["key"]
    return Fernet(key.encode())


def encrypt(plaintext: str) -> str:
    """Encripta un string, retorna ciphertext base64."""
    f = get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Desencripta un ciphertext base64, retorna plaintext."""
    f = get_fernet()
    return f.decrypt(ciphertext.encode()).decode()
