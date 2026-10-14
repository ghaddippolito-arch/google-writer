# Google Writer ✍️

Aplicación web local desarrollada en Python con **Streamlit** para la generación automatizada de artículos SEO de alta calidad (+1500 palabras) optimizados bajo los criterios de **Google Helpful Content System**, con datos reales investigados en internet vía **Google Search Grounding**, y exportación directa a **Google Docs**.

---

## 🌟 Características Principales

1. **Campos de Interfaz Dinámicos y Condicionales:**
   - **Temática:** Texto libre con el destino o temática de viaje.
   - **Idioma:** Español, Inglés, Portugués, Francés, Italiano, Alemán.
   - **País de la audiencia:** Adaptación de terminología, requisitos migratorios, precios y perspectivas del viajero local.
   - **Categoría:** Menú desplegable principal.
   - **Subcategoría:** Menú desplegable condicional reactivo que se actualiza automáticamente al cambiar la categoría.

2. **Categorías y Subcategorías Soportadas:**
   - **Requisitos y documentos para viajar:**
     - Guía de visados para viajeros
     - Requisitos esenciales para viajar
     - Equipaje: todo lo que necesitas saber
   - **Qué hacer en los mejores destinos turísticos:**
     - Actividades increíbles para viajeros
     - Itinerario diario para tu viaje
     - Dónde comer en los mejores destinos
     - Consejos para viajar con niños
   - **Presupuesto de viaje: guía práctica:**
     - Costos locales en tu ciudad de destino
     - Dinero necesario para viajar
   - **Asistencia al viajero: todo lo que debes saber:**
     - Sistema de salud local en tu viaje
     - Assist card: tu compañero de viaje
     - Salud y enfermedades en el viaje
   - **Mejor época para viajar a tu destino:**
     - Cuándo ir a tu destino: guía completa
     - Clima en tu destino: todo lo que necesitas saber
     - Fechas especiales para viajar
   - **Mapa de tu destino: guía interactiva:**
     - Transporte en tu destino: guía completa
     - Cómo trasladarse en tu viaje
     - Mapas interactivos para tus viajes
   - **Todo sobre alojamientos: opciones y consejos:**
     - Toda la información para saber dónde hospedarse
     - Los mejores hoteles para tu viaje
     - Los hoteles más baratos para tu viaje
   - **Tips de viaje: consejos esenciales:**
     - Los mejores Tips de Viaje.

3. **Inteligencia Artificial y Google Search Grounding:**
   - Conexión oficial a través de la SDK `google-genai` (modelos Gemini 2.5 Flash / 2.0 Flash).
   - Acceso en tiempo real al buscador de Google (`types.Tool(google_search=...)`) para contrastar datos reales, normativas, precios y sitios oficiales.
   - Enlaces citados en formato markdown `[Fuente](URL)` a lo largo del contenido.
   - Redacción estructurada de **+1500 palabras** con encabezados H1, H2, H3, tablas comparativas, cajas de consejos y sección FAQ.

4. **Integración con Google Docs API:**
   - Conversión inteligente de Markdown a formato nativo de Google Docs (encabezados, listas, tablas y enlaces hipervinculados).
   - Crea un nuevo documento en tu cuenta personal mediante OAuth 2.0 o Service Account.
   - Muestra un botón e hipervínculo directo al documento creado (`https://docs.google.com/document/d/.../edit`).

---

## 🚀 Cómo Iniciar la Aplicación

### Opción 1: Archivo Batch (Un clic)
Haz doble clic en el archivo `run_app.bat`.

### Opción 2: Terminal / PowerShell
```powershell
python -m streamlit run app.py
```

El servidor abrirá automáticamente en tu navegador local en:
`http://localhost:8501`

---

## 🔑 Configuración de Credenciales

### 1. Gemini API Key
- Puedes ingresarla directamente en la barra lateral de la app o crear un archivo `.env` con:
  ```env
  GEMINI_API_KEY=tu_api_key_aqui
  ```
- Si aún no tienes una, obtén tu clave gratuita en [Google AI Studio](https://aistudio.google.com/app/apikey).

### 2. Google Docs & Drive (OAuth 2.0)
Para que la app cree documentos directamente en tu Google Drive / Google Docs:
1. Ve a [Google Cloud Console](https://console.cloud.google.com/).
2. Habilita las APIs **Google Docs API** y **Google Drive API**.
3. En **APIs y Servicios > Credenciales**, crea una credencial de tipo **ID de cliente de OAuth** (Tipo de aplicación: *Aplicación de escritorio* o *Desktop app*).
4. Descarga el archivo JSON y nómbralo `credentials.json` en la carpeta del proyecto (o súbelo mediante el selector en la barra lateral de Streamlit).
5. La primera vez que generes o pulses "Iniciar sesión en Google", se abrirá una ventana en tu navegador para que otorgues permiso. Una vez aceptado, se creará `token.json` y no necesitarás volver a iniciar sesión.
