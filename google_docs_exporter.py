"""
Módulo para autenticación y exportación de artículos a Google Docs / Google Drive API.
Convierte el artículo en Markdown a un Google Doc con formato enriquecido (encabezados, listas, tablas y enlaces clicables).
Incluye métodos de autenticación interactivos y no bloqueantes para evitar congelamientos en Streamlit.
"""

import os
import io
import json
import subprocess
import threading
from typing import Dict, Any, Optional, Tuple
import markdown

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

from config import GOOGLE_SCOPES

TOKEN_FILE = "token.json"
DEFAULT_CREDENTIALS_FILE = "credentials.json"
DEFAULT_SERVICE_ACCOUNT_FILE = "service_account.json"
AUTH_PORT = 8088

# Almacenamiento en memoria para hilos de autenticación en segundo plano
_bg_flow = None
_bg_thread = None
_bg_auth_status = {"status": "idle", "message": ""}


def get_stored_credentials() -> Optional[Credentials]:
    """
    Intenta cargar credenciales guardadas en st.secrets (Streamlit Cloud) o token.json (local).
    Refresca el token automáticamente si ha expirado.
    """
    # 1. Intentar desde st.secrets (para Streamlit Community Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            # Caso A: Bloque [google_oauth] en secrets
            if "google_oauth" in st.secrets:
                oauth_val = st.secrets["google_oauth"]
                if isinstance(oauth_val, str):
                    oauth_val = json.loads(oauth_val)
                creds = Credentials.from_authorized_user_info(dict(oauth_val), GOOGLE_SCOPES)
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                if creds and creds.valid:
                    return creds
            # Caso B: Bloque [gcp_service_account] en secrets
            if "gcp_service_account" in st.secrets:
                sa_val = st.secrets["gcp_service_account"]
                if isinstance(sa_val, str):
                    sa_val = json.loads(sa_val)
                creds = service_account.Credentials.from_service_account_info(dict(sa_val), scopes=GOOGLE_SCOPES)
                if creds and creds.valid:
                    return creds
    except Exception as e:
        print(f"[AUTH] Error al verificar credenciales en st.secrets: {e}", flush=True)

    # 2. Intentar archivo local token.json
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, GOOGLE_SCOPES)
            if creds and creds.valid:
                return creds
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
                return creds
        except Exception:
            return None
    return None


def get_oauth_authorization_url(credentials_file: str = DEFAULT_CREDENTIALS_FILE, port: int = AUTH_PORT) -> Tuple[str, InstalledAppFlow]:
    """
    Genera la URL de autorización OAuth de Google sin bloquear el hilo de ejecución.
    """
    if not os.path.exists(credentials_file):
        raise FileNotFoundError(f"No se encontró el archivo '{credentials_file}'.")

    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_file,
        GOOGLE_SCOPES,
        redirect_uri=f"http://localhost:{port}/"
    )
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline"
    )
    return auth_url, flow


def complete_oauth_with_url(
    redirect_url: str,
    flow_instance: Optional[InstalledAppFlow] = None,
    credentials_file: str = DEFAULT_CREDENTIALS_FILE,
    port: int = AUTH_PORT
) -> bool:
    """
    Toma la URL completa a la que Google redirigió o el código de autorización
    e intercambia el código por las credenciales OAuth guardando token.json.
    Si se proporciona flow_instance, reutiliza su code_verifier para evitar invalid_grant (PKCE).
    """
    from urllib.parse import urlparse, parse_qs
    clean_str = redirect_url.strip()
    if not clean_str.startswith("http://") and not clean_str.startswith("https://"):
        clean_str = f"http://{clean_str}"

    flow = flow_instance or InstalledAppFlow.from_client_secrets_file(
        credentials_file,
        GOOGLE_SCOPES,
        redirect_uri=f"http://localhost:{port}/"
    )

    try:
        flow.fetch_token(authorization_response=clean_str)
    except Exception:
        # Fallback extrayendo el código directamente
        auth_code = clean_str
        parsed = urlparse(clean_str)
        qs = parse_qs(parsed.query)
        codes = qs.get("code")
        if codes:
            auth_code = codes[0]
        flow.fetch_token(code=auth_code)

    creds = flow.credentials
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    return True


def launch_external_auth_window():
    """
    Lanza una ventana interactiva de Windows (CMD) ejecutando auth_google.bat.
    Es 100% independiente de Streamlit, por lo que nunca se congela y permite
    ver la URL y abrir el navegador con total claridad.
    """
    bat_path = os.path.abspath("auth_google.bat")
    if os.path.exists(bat_path):
        subprocess.Popen(f'start "Autenticar Google" cmd.exe /c "{bat_path}"', shell=True)
    else:
        py_exe = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python", "Python311", "python.exe")
        if not os.path.exists(py_exe):
            py_exe = "python"
        subprocess.Popen(f'start "Autenticar Google" cmd.exe /k "{py_exe}" auth_google.py', shell=True)


def authenticate_google_oauth(credentials_file: str = DEFAULT_CREDENTIALS_FILE, port: int = AUTH_PORT) -> Credentials:
    """
    Ejecuta el flujo OAuth 2.0 abriendo el navegador.
    """
    creds = get_stored_credentials()
    if creds and creds.valid:
        return creds

    if not os.path.exists(credentials_file):
        raise FileNotFoundError(f"No se encontró el archivo de credenciales '{credentials_file}'.")

    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_file,
        GOOGLE_SCOPES,
        redirect_uri=f"http://localhost:{port}/"
    )
    creds = flow.run_local_server(port=port, prompt="consent", open_browser=True)

    with open(TOKEN_FILE, "w", encoding="utf-8") as token:
        token.write(creds.to_json())

    return creds


def authenticate_service_account(service_account_file: str = DEFAULT_SERVICE_ACCOUNT_FILE) -> Credentials:
    """
    Autenticación mediante cuenta de servicio (Service Account).
    """
    if not os.path.exists(service_account_file):
        raise FileNotFoundError(f"No se encontró el archivo de cuenta de servicio '{service_account_file}'.")
    return service_account.Credentials.from_service_account_file(
        service_account_file, scopes=GOOGLE_SCOPES
    )


def get_active_credentials(custom_creds_path: Optional[str] = None) -> Credentials:
    """
    Obtiene las credenciales activas disponibles (token.json > custom path > credentials.json > service_account.json).
    """
    # 1. Verificar si ya hay un token.json activo
    stored = get_stored_credentials()
    if stored and stored.valid:
        return stored

    target_path = custom_creds_path if custom_creds_path and os.path.exists(custom_creds_path) else None

    # 2. Intentar archivo especificado o credentials.json
    client_secrets = target_path or (DEFAULT_CREDENTIALS_FILE if os.path.exists(DEFAULT_CREDENTIALS_FILE) else None)
    if client_secrets:
        try:
            with open(client_secrets, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("type") == "service_account":
                return authenticate_service_account(client_secrets)
            else:
                raise RuntimeError(
                    "Tu cuenta de Google Docs aún no ha sido autorizada. "
                    "Por favor pulsa 'Abrir Asistente de Login' en la barra lateral o ejecuta 'auth_google.bat' para conectar tu cuenta una sola vez."
                )
        except Exception as e:
            raise RuntimeError(f"Error al procesar el archivo de credenciales '{client_secrets}': {e}")

    # 3. Intentar service_account.json si existe
    if os.path.exists(DEFAULT_SERVICE_ACCOUNT_FILE):
        return authenticate_service_account(DEFAULT_SERVICE_ACCOUNT_FILE)

    raise FileNotFoundError(
        "No se encontraron credenciales de Google configuradas. "
        "Sube tu archivo 'credentials.json' (OAuth 2.0 Desktop) o 'service_account.json' en la barra lateral."
    )


def markdown_to_html_document(title: str, markdown_text: str) -> str:
    """
    Convierte el texto Markdown en un documento HTML limpio y semántico con estilos
    para que Google Docs lo interprete fielmente (H1, H2, H3, párrafos, listas, enlaces y tablas).
    """
    body_html = markdown.markdown(
        markdown_text,
        extensions=["extra", "nl2br", "tables", "sane_lists"]
    )

    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
    body {{
        font-family: Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.5;
        color: #202124;
        margin: 20px;
    }}
    h1 {{
        font-size: 20pt;
        color: #1a73e8;
        font-weight: bold;
        margin-top: 24px;
        margin-bottom: 12px;
    }}
    h2 {{
        font-size: 15pt;
        color: #202124;
        font-weight: bold;
        border-bottom: 1px solid #dadce0;
        padding-bottom: 4px;
        margin-top: 20px;
        margin-bottom: 10px;
    }}
    h3 {{
        font-size: 12pt;
        color: #3c4043;
        font-weight: bold;
        margin-top: 16px;
        margin-bottom: 8px;
    }}
    p {{
        margin-bottom: 12px;
    }}
    ul, ol {{
        margin-bottom: 12px;
        padding-left: 24px;
    }}
    li {{
        margin-bottom: 6px;
    }}
    a {{
        color: #1a73e8;
        text-decoration: underline;
    }}
    blockquote {{
        border-left: 4px solid #1a73e8;
        background-color: #f1f3f4;
        padding: 8px 16px;
        margin: 12px 0;
        color: #3c4043;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 16px;
    }}
    th, td {{
        border: 1px solid #dadce0;
        padding: 8px 12px;
        text-align: left;
    }}
    th {{
        background-color: #f8f9fa;
        font-weight: bold;
    }}
</style>
</head>
<body>
{body_html}
</body>
</html>
"""
    return full_html


def create_google_doc(
    title: str,
    markdown_content: str,
    credentials_path: Optional[str] = None,
    share_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea un nuevo documento en la cuenta de Google Docs del usuario.
    Convierte el contenido en Markdown a un Google Doc con títulos y enlaces formateados.
    Retorna el ID y el enlace web directo al documento.
    """
    creds = get_active_credentials(credentials_path)

    # 1. Crear documento convirtiendo HTML con Google Drive API (Método principal de formato enriquecido)
    try:
        drive_service = build("drive", "v3", credentials=creds)
        html_content = markdown_to_html_document(title, markdown_content)

        file_metadata = {
            "name": title,
            "mimeType": "application/vnd.google-apps.document",
            "description": "Artículo SEO generado con ACI Writer y Gemini"
        }

        media = MediaInMemoryUpload(
            html_content.encode("utf-8"),
            mimetype="text/html",
            resumable=True
        )

        doc_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink"
        ).execute()

        doc_id = doc_file.get("id")
        doc_url = doc_file.get("webViewLink") or f"https://docs.google.com/document/d/{doc_id}/edit"

        # Si se usó Service Account y se proporcionó un email, compartirlo
        if share_email and share_email.strip():
            try:
                drive_service.permissions().create(
                    fileId=doc_id,
                    body={"role": "writer", "type": "user", "emailAddress": share_email.strip()},
                    fields="id"
                ).execute()
            except Exception:
                pass

        return {
            "success": True,
            "document_id": doc_id,
            "document_url": doc_url,
            "title": title,
            "method": "drive_html_import"
        }

    except Exception as drive_err:
        # Fallback usando directamente Google Docs API v1 en caso de restricciones de Drive MIME conversion
        try:
            docs_service = build("docs", "v1", credentials=creds)
            body = {"title": title}
            doc = docs_service.documents().create(body=body).execute()
            doc_id = doc.get("documentId")
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

            # Insertar texto completo en el documento
            requests = [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": markdown_content
                    }
                }
            ]
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": requests}
            ).execute()

            return {
                "success": True,
                "document_id": doc_id,
                "document_url": doc_url,
                "title": title,
                "method": "docs_api_fallback",
                "note": f"Exportado con formato plano por: {drive_err}"
            }
        except Exception as docs_err:
            raise RuntimeError(f"Error al crear el documento en Google Docs: {docs_err} (Error previo Drive: {drive_err})")
