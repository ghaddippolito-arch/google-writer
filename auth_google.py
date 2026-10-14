"""
Script independiente para autenticar Google Docs / Google Drive OAuth 2.0.
Abre el navegador con la URL autorizada correcta y guarda las credenciales en token.json.
"""

import sys
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from config import GOOGLE_SCOPES

TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

def main():
    print("=" * 65)
    print("      ASISTENTE DE AUTENTICACIÓN GOOGLE DOCS / DRIVE")
    print("=" * 65)
    print()

    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ ERROR: No se encontró el archivo '{CREDENTIALS_FILE}'.")
        print("Asegúrate de colocar tu credentials.json en esta carpeta.")
        input("\nPresiona Enter para salir...")
        sys.exit(1)

    print("📁 Archivo 'credentials.json' detectado.")
    print("Iniciando flujo de autorización OAuth 2.0...")
    print("Se abrirá tu navegador para que inicies sesión y permitas el acceso.")
    print()

    # Puerto fijo 8088
    port = 8088
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE,
        GOOGLE_SCOPES,
        redirect_uri=f"http://localhost:{port}/"
    )

    try:
        # run_local_server genera la URL, abre el navegador y valida el token en una sola llamada coherente
        creds = flow.run_local_server(
            port=port,
            prompt="consent",
            open_browser=True
        )
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        print()
        print("=" * 65)
        print("✅ ¡AUTENTICACIÓN EXITOSA!")
        print(f"Se ha creado el archivo '{TOKEN_FILE}' correctamente.")
        print("Ya puedes cerrar esta ventana y regresar a la aplicación Streamlit.")
        print("=" * 65)
    except Exception as e:
        print()
        print(f"❌ Error durante la autenticación: {e}")

    print()
    input("Presiona Enter para cerrar esta ventana...")

if __name__ == "__main__":
    main()
