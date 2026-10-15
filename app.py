"""
Aplicación Streamlit: Google Writer - Generador SEO con Gemini y Google Docs
Redacta artículos SEO de +1500 palabras con citas reales y Helpful Content de Google,
y los exporta directamente a tu cuenta de Google Docs.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Cargar variables de entorno locales si existen
load_dotenv()

from config import (
    CATEGORIES_AND_SUBCATEGORIES,
    LANGUAGES,
    COUNTRIES,
    GEMINI_MODELS,
    GOOGLE_SCOPES
)
from gemini_agent import generate_seo_article
from google_docs_exporter import (
    get_stored_credentials,
    authenticate_google_oauth,
    create_google_doc,
    get_oauth_authorization_url,
    complete_oauth_with_url,
    launch_external_auth_window,
    TOKEN_FILE,
    DEFAULT_CREDENTIALS_FILE,
    DEFAULT_SERVICE_ACCOUNT_FILE
)
def safe_fetch_article_images_pack(*args, **kwargs):
    import image_generator
    try:
        import importlib
        importlib.reload(image_generator)
    except Exception:
        pass
    return image_generator.fetch_article_images_pack(*args, **kwargs)

def safe_regenerate_single_image(*args, **kwargs):
    import image_generator
    return image_generator.regenerate_single_image(*args, **kwargs)

def safe_create_images_zip(*args, **kwargs):
    import image_generator
    return image_generator.create_images_zip(*args, **kwargs)

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Google Writer - SEO & Google Docs",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        color: #1a73e8;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #5f6368;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 16px;
        border-left: 4px solid #1a73e8;
        margin-bottom: 10px;
    }
    .doc-link-box {
        background: linear-gradient(135deg, #e8f0fe 0%, #d2e3fc 100%);
        border: 2px solid #1a73e8;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
        margin-bottom: 25px;
        text-align: center;
    }
    .doc-link-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #174ea6;
        margin-bottom: 8px;
    }
    .stButton>button {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# Inicialización del Session State
if "article_data" not in st.session_state:
    st.session_state.article_data = None
if "google_doc_url" not in st.session_state:
    st.session_state.google_doc_url = None
if "google_doc_id" not in st.session_state:
    st.session_state.google_doc_id = None
if "last_error" not in st.session_state:
    st.session_state.last_error = None
if "article_images_pack" not in st.session_state:
    st.session_state.article_images_pack = None
if "article_image_bytes" not in st.session_state:
    st.session_state.article_image_bytes = None
if "article_image_prompt" not in st.session_state:
    st.session_state.article_image_prompt = None


# ==========================================
# BARRA LATERAL: Configuración de Credenciales
# ==========================================
with st.sidebar:
    st.image("https://www.gstatic.com/images/branding/product/2x/docs_2020q4_48dp.png", width=48)
    st.title("Configuración")
    st.markdown("---")

    # 1. API Key de Gemini
    st.subheader("🤖 API de Gemini")
    secret_key = ""
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            secret_key = str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        pass
    env_gemini_key = secret_key or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    api_key_input = st.text_input(
        "Gemini API Key:",
        value=env_gemini_key,
        type="password",
        help="Obtén tu API Key gratuita en https://aistudio.google.com/app/apikey",
        placeholder="AIzaSy..."
    )
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input.strip()

    gemini_model = st.selectbox(
        "Modelo de Gemini:",
        options=GEMINI_MODELS,
        index=0,
        help="Modelos recomendados con soporte para Search Grounding en tiempo real."
    )

    st.markdown("---")

    # 2. Conexión con Google Docs
    st.subheader("📄 Conexión Google Docs")
    
    # Comprobar estado de credenciales
    stored_creds = get_stored_credentials()
    has_token = stored_creds is not None and stored_creds.valid
    has_credentials_file = os.path.exists(DEFAULT_CREDENTIALS_FILE)
    has_service_account = os.path.exists(DEFAULT_SERVICE_ACCOUNT_FILE)

    if has_token:
        st.success("🟢 Conectado con tu cuenta de Google Docs (`token.json` activo)")
        if st.button("🔌 Desconectar / Cambiar cuenta"):
            try:
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                st.session_state.google_doc_url = None
                st.rerun()
            except Exception as e:
                st.error(f"Error al eliminar token: {e}")
    elif has_credentials_file:
        st.info("🟡 Archivo `credentials.json` detectado.")
        
        # Mantener el mismo flow en session_state para que el code_verifier de PKCE coincida
        if "oauth_flow" not in st.session_state or st.session_state.get("oauth_flow") is None:
            try:
                auth_url, flow = get_oauth_authorization_url(DEFAULT_CREDENTIALS_FILE)
                st.session_state["oauth_flow"] = flow
                st.session_state["auth_url"] = auth_url
            except Exception:
                auth_url = None
        else:
            auth_url = st.session_state.get("auth_url")
            flow = st.session_state.get("oauth_flow")

        st.markdown("**Elige cómo autorizar tu cuenta:**")
        
        # Opción 1 (Recomendada y 100% automática): Archivo bat de Windows
        if st.button("🖥️ Abrir Asistente de Login (Ventana)", use_container_width=True, help="Abre una ventana de consola que abre tu navegador y guarda el token automáticamente."):
            launch_external_auth_window()
            st.toast("Se ha abierto una ventana de autorización. Búscala en tu barra de tareas.", icon="🔑")
        
        # Opción 2: Enlace directo en el navegador
        if auth_url:
            st.link_button("🌐 1. Abrir Login de Google en el navegador ↗", auth_url, use_container_width=True)

        st.markdown("---")
        st.markdown("📋 **2. Si Google te llevó a 'No se puede acceder a localhost:8088':**")
        pasted_oauth_url = st.text_input(
            "Copia la URL de esa pestaña y pégala aquí:",
            placeholder="http://localhost:8088/?state=...&code=...",
            help="Copia todo el texto de la barra de direcciones de esa pestaña de Chrome y pégalo aquí."
        )
        if st.button("💾 Conectar con esta URL", use_container_width=True):
            if pasted_oauth_url and ("code=" in pasted_oauth_url or pasted_oauth_url.strip().startswith("4/")):
                try:
                    active_flow = st.session_state.get("oauth_flow")
                    complete_oauth_with_url(pasted_oauth_url, flow_instance=active_flow)
                    st.session_state["oauth_error"] = None
                    st.session_state["oauth_flow"] = None
                    st.success("🎉 ¡Cuenta de Google Docs conectada exitosamente!")
                    st.rerun()
                except Exception as oauth_err:
                    st.session_state["oauth_error"] = str(oauth_err)
            else:
                st.session_state["oauth_error"] = "Asegúrate de pegar la URL completa que contiene 'code='."

        if st.session_state.get("oauth_error"):
            st.error(f"❌ {st.session_state['oauth_error']}")

        if st.button("🔄 Actualizar estado", use_container_width=True):
            st.rerun()
    elif has_service_account:
        st.info("🔵 Cuenta de servicio (`service_account.json`) activa.")
    else:
        st.warning("⚠️ Sin credenciales de Google Docs.")

    # Subir archivo credentials.json si no existe
    uploaded_file = st.file_uploader(
        "Subir `credentials.json` (OAuth) o `service_account.json`:",
        type=["json"],
        key="credentials_file_uploader",
        help="Archivo descargado de Google Cloud Console con las APIs de Google Docs y Drive habilitadas."
    )
    if uploaded_file is not None:
        file_signature = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("saved_credentials_signature") != file_signature:
            content = uploaded_file.getvalue()
            file_path = DEFAULT_CREDENTIALS_FILE
            # Verificar si es service_account
            if b'"service_account"' in content:
                file_path = DEFAULT_SERVICE_ACCOUNT_FILE
            with open(file_path, "wb") as f:
                f.write(content)
            st.session_state["saved_credentials_signature"] = file_signature
            st.success(f"✅ Archivo guardado exitosamente como `{file_path}`")
            st.rerun()

    # Tutorial desplegable
    with st.expander("ℹ️ ¿Cómo conectar Google Docs?"):
        st.markdown("""
        **Pasos para habilitar Google Docs en tu cuenta:**
        1. Ingresa a [Google Cloud Console](https://console.cloud.google.com/).
        2. Crea o selecciona un proyecto y habilita:
           - **Google Docs API**
           - **Google Drive API**
        3. Ve a **APIs & Servicios > Credenciales**:
           - Crea una credencial **ID de cliente de OAuth** (Tipo: *Aplicación de escritorio / Desktop app*).
           - En *Pantalla de consentimiento OAuth*, añade tu correo como usuario de prueba.
        4. Descarga el archivo JSON, nómbralo `credentials.json` y súbelo aquí arriba.
        """)


# ==========================================
# ÁREA PRINCIPAL: Formulario de Redacción
# ==========================================
st.markdown('<div class="main-title">✍️ Google Writer: Artículos SEO & Google Docs</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Genera artículos optimizados de <b>+1500 palabras</b> siguiendo '
    '<b>Google Helpful Content</b> con datos reales investigados en internet y expórtalos automáticamente a tu <b>Google Docs</b>.</div>',
    unsafe_allow_html=True
)

# Formulario principal con los campos requeridos
with st.container():
    col1, col2 = st.columns([1, 1])

    with col1:
        thematic = st.text_input(
            "📍 Temática:",
            placeholder="Ej: Viaje a Japón en primavera: itinerario, costos y visados",
            help="Ingresa el tema específico, destino o foco del artículo que deseas redactar."
        )

        language = st.selectbox(
            "🌐 Idioma:",
            options=LANGUAGES,
            index=0,
            help="Idioma en el que se redactará el artículo SEO."
        )

        # Por defecto seleccionar Colombia o Global
        default_idx = COUNTRIES.index("Colombia") if "Colombia" in COUNTRIES else 0
        country = st.selectbox(
            "🎯 País de la audiencia:",
            options=COUNTRIES,
            index=default_idx,
            help="Escribe o selecciona cualquier país del mundo."
        )

    with col2:
        # Menú desplegable de Categoría
        categories_list = list(CATEGORIES_AND_SUBCATEGORIES.keys())
        selected_category = st.selectbox(
            "📂 Categoría:",
            options=categories_list,
            index=0,
            key="selected_category_key",
            help="Selecciona la categoría principal de viaje."
        )

        # Menú desplegable condicional de Subcategoría (cambia según la categoría)
        cat_idx = categories_list.index(selected_category) if selected_category in categories_list else 0
        subcategories_list = CATEGORIES_AND_SUBCATEGORIES.get(selected_category, [])
        selected_subcategory = st.selectbox(
            "📑 Subcategoría:",
            options=subcategories_list,
            index=0,
            key=f"subcat_idx_{cat_idx}",
            help="Subcategoría específica vinculada a la categoría seleccionada."
        )
        st.caption(f"📌 *Opciones para: {selected_category}*")

# Opciones de generación
generate_image_opt = st.checkbox(
    "🎨 Generar pack de 3 imágenes para el artículo (1 Portada + 2 Interior)",
    value=True,
    help="Descarga directa en alta definición desde la web: 1 foto de portada panorámica (16:9) y 2 fotos para el interior del artículo. No se insertan en Google Docs."
)

# Botón Generar destacado
st.markdown("<br>", unsafe_allow_html=True)
generate_btn = st.button("🚀 Generar Artículo y Crear en Google Docs", type="primary", use_container_width=True)


# ==========================================
# LÓGICA DE GENERACIÓN Y EXPORTACIÓN
# ==========================================
if generate_btn:
    st.session_state.last_error = None
    print(f"[ACTION] Boton 'Generar' presionado para tematica: '{thematic}'", flush=True)
    
    # Validaciones previas
    if not thematic or not thematic.strip():
        st.error("⚠️ Por favor ingresa una **Temática** antes de generar.")
    elif not api_key_input or not api_key_input.strip():
        st.error("⚠️ Falta la **Gemini API Key**. Ingrésala en la barra lateral izquierda.")
    else:
        # 1. Generar contenido con Gemini
        with st.spinner("⏳ Investigando datos reales y redactando artículo SEO (+1500 palabras)... Esto tomará entre 15 y 30 segundos."):
            with st.status("Generando contenido SEO con Gemini...", expanded=True) as status:
                st.write("🔍 Conectando con Gemini API e investigando en la web en tiempo real...")
                st.write(f"🌐 Extrayendo fuentes oficiales y normativas actualizadas para '{thematic}'...")
                
                try:
                    article_result = generate_seo_article(
                        api_key=api_key_input,
                        thematic=thematic.strip(),
                        language=language,
                        country=country,
                        category=selected_category,
                        subcategory=selected_subcategory,
                        model_name=gemini_model
                    )
                    st.session_state.article_data = article_result
                    num_src = len(article_result.get("sources", []))
                    st.write(f"✅ Artículo redactado exitosamente: **{article_result['word_count']} palabras** y **{num_src} fuentes verificadas**.")
                    
                    # 2. Conectar y exportar a Google Docs API
                    st.write("📄 Conectando con Google Docs API para crear el documento en tu cuenta...")
                    doc_title = f"{thematic} - {selected_subcategory}"
                    
                    try:
                        doc_export = create_google_doc(
                            title=doc_title,
                            markdown_content=article_result["text"]
                        )
                        st.session_state.google_doc_url = doc_export["document_url"]
                        st.session_state.google_doc_id = doc_export["document_id"]
                        st.write(f"🎉 ¡Documento creado en Google Docs! Enlace listo.")
                        status.update(label="¡Artículo generado y guardado en Google Docs con éxito!", state="complete", expanded=False)
                    except Exception as doc_err:
                        st.session_state.google_doc_url = None
                        st.session_state.google_doc_id = None
                        status.update(label="Artículo generado (Pendiente exportar a Google Docs)", state="complete", expanded=False)
                        st.warning(
                            f"⚠️ El artículo se generó correctamente, pero hubo un detalle al crear el Google Doc: {doc_err}\n\n"
                            "Puedes autorizar tu cuenta en la barra lateral o con auth_google.bat y presionar el botón de exportación."
                        )

                    # 3. Generar pack de 3 imágenes (1 portada + 2 interior) si está habilitado
                    if generate_image_opt:
                        st.write("🎨 Generando pack de 3 imágenes HD (1 portada + 2 interior)...")
                        try:
                            images_pack = safe_fetch_article_images_pack(
                                thematic=thematic.strip(),
                                subcategory=selected_subcategory,
                                country=country,
                                api_key=api_key_input,
                                width=1280
                            )
                            st.session_state.article_images_pack = images_pack
                            if images_pack and len(images_pack) > 0:
                                st.session_state.article_image_bytes = images_pack[0]["bytes"]
                            st.write(f"✅ Pack de {len(images_pack)} imágenes generado exitosamente (listas para descargar).")
                        except Exception as img_err:
                            print(f"[IMAGE_GEN] Error al generar pack de imágenes: {img_err}", flush=True)
                            st.session_state.article_images_pack = None
                            st.warning(f"⚠️ El pack de imágenes no se pudo generar automáticamente: {img_err}")
                    else:
                        st.session_state.article_images_pack = None
                except Exception as gemini_err:
                    status.update(label="Error durante la generación", state="error", expanded=True)
                    st.error(f"❌ Ocurrió un error al generar con Gemini: {gemini_err}")
                    st.session_state.last_error = str(gemini_err)


# ==========================================
# MOSTRAR RESULTADOS
# ==========================================
if st.session_state.article_data:
    data = st.session_state.article_data

    # Banner del enlace a Google Docs si está disponible
    if st.session_state.google_doc_url:
        doc_url = st.session_state.google_doc_url
        st.markdown(f"""
        <div class="doc-link-box">
            <div class="doc-link-title">📄 Tu artículo ya está disponible en Google Docs</div>
            <p style="color: #3c4043; margin-bottom: 15px;">Se ha creado un nuevo documento en tu cuenta de Google con todo el contenido, formato y enlaces.</p>
            <a href="{doc_url}" target="_blank" style="
                background-color: #1a73e8;
                color: white;
                padding: 12px 28px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                font-size: 1.1rem;
                display: inline-block;
                box-shadow: 0 2px 6px rgba(26,115,232,0.4);
            ">
                🔗 Abrir Documento en Google Docs ↗
            </a>
            <div style="margin-top: 10px; font-size: 0.9rem; color: #5f6368;">
                Enlace directo: <a href="{doc_url}" target="_blank">{doc_url}</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Botón para reintentar exportar a Google Docs si el artículo ya está generado
        st.info("💡 Tu artículo está listo a continuación. Para enviarlo a Google Docs:")
        col_exp1, col_exp2 = st.columns([2, 1])
        with col_exp1:
            st.caption("Asegúrate de tener cargado `credentials.json` en la barra lateral.")
        with col_exp2:
            if st.button("📤 Exportar este artículo a Google Docs", use_container_width=True):
                with st.spinner("Creando documento en Google Docs..."):
                    try:
                        doc_export = create_google_doc(
                            title=data.get("title", "Artículo SEO"),
                            markdown_content=data["text"]
                        )
                        st.session_state.google_doc_url = doc_export["document_url"]
                        st.session_state.google_doc_id = doc_export["document_id"]
                        st.success("¡Documento creado exitosamente!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error al exportar: {err}")

    # Métricas y estadísticas del artículo
    st.markdown("### 📊 Estadísticas y Calidad SEO")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            label="📝 Recuento de Palabras",
            value=f"{data['word_count']} palabras",
            delta="Cumple +1500" if data['word_count'] >= 1500 else "Menor a 1500",
            delta_color="normal" if data['word_count'] >= 1500 else "inverse"
        )
    with m2:
        est_read_time = max(1, round(data['word_count'] / 200))
        st.metric(label="⏱️ Tiempo de Lectura", value=f"~{est_read_time} min")
    with m3:
        num_sources = len(data.get("sources", []))
        st.metric(label="🔍 Fuentes Web Citadas", value=f"{num_sources} fuentes")
    with m4:
        st.metric(label="🤖 Modelo Utilizado", value=data.get("model_used", gemini_model))

    # Pestañas de visualización
    tab_preview, tab_markdown, tab_sources, tab_images = st.tabs([
        "📖 Vista Previa del Artículo",
        "📋 Markdown Puro",
        "🌐 Fuentes y Búsqueda",
        "🖼️ Pack de Imágenes (3)"
    ])

    with tab_preview:
        st.markdown(data["text"])

    with tab_markdown:
        st.text_area("Contenido Markdown:", value=data["text"], height=500)
        st.download_button(
            label="💾 Descargar como archivo .md",
            data=data["text"],
            file_name=f"{data.get('title', 'articulo_seo').replace(' ', '_')}.md",
            mime="text/markdown"
        )

    with tab_sources:
        sources = data.get("sources", [])
        queries = data.get("search_queries", [])
        
        if queries:
            st.markdown("**Consultas de búsqueda realizadas en Google:**")
            for q in queries:
                st.markdown(f"- 🔎 `{q}`")
        
        if sources:
            st.markdown("<br>**Fuentes y enlaces extraídos en la investigación:**", unsafe_allow_html=True)
            for s in sources:
                st.markdown(f"- [{s.get('title', 'Fuente')}]({s.get('url')})")
        else:
            st.info("Las citas y enlaces markdown han sido incorporados directamente en el cuerpo del artículo.")

    with tab_images:
        images_pack = st.session_state.get("article_images_pack")
        clean_title = "".join(c for c in thematic if c.isalnum() or c in (" ", "_", "-")).rstrip().replace(" ", "_")
        if not clean_title:
            clean_title = "articulo_viajes"

        if images_pack and len(images_pack) > 0:
            st.markdown("### 🖼️ Pack de Imágenes del Artículo (1 Portada + 2 Interior)")
            st.caption("📐 Fotografías en Alta Definición (1280px) • 💾 Formato JPEG • 🚀 Listas para descargar y usar en tu web o CMS (No insertadas en Google Docs).")

            # Botón para descargar el pack completo en un único archivo ZIP
            try:
                zip_bytes = safe_create_images_zip(images_pack, clean_title)
                st.download_button(
                    label="📦 Descargar Pack Completo (ZIP con las 3 imágenes HD)",
                    data=zip_bytes,
                    file_name=f"{clean_title}_pack_imagenes.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )
            except Exception as e_zip:
                print(f"[ZIP] Error creando zip: {e_zip}", flush=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Mostrar las 3 imágenes en 3 columnas
            cols = st.columns(len(images_pack))
            for idx, (col, item) in enumerate(zip(cols, images_pack)):
                with col:
                    st.markdown(f"#### {item['badge']}")
                    st.caption(f"**{item['role']}**<br>{item['description']}", unsafe_allow_html=True)
                    st.image(item["bytes"], use_container_width=True)
                    
                    # Botón de descarga individual
                    st.download_button(
                        label=f"💾 Descargar {item['badge']} (.jpg)",
                        data=item["bytes"],
                        file_name=f"{clean_title}_{item['suffix']}",
                        mime="image/jpeg",
                        key=f"dl_img_{item['id']}_{idx}",
                        use_container_width=True
                    )

                    # Botón para regenerar esta imagen individual
                    if st.button(f"🔄 Otra opción de {item['badge']}", key=f"regen_{item['id']}_{idx}", use_container_width=True):
                        with st.spinner(f"Buscando alternativa para {item['badge']}..."):
                            try:
                                used_others = {other["url"] for other in images_pack if other.get("url") and other["id"] != item["id"]}
                                new_b, new_u, new_t = safe_regenerate_single_image(item["query"], exclude_urls=used_others, width=1280)
                                if new_b:
                                    item["bytes"] = new_b
                                    item["url"] = new_u or ""
                                    item["title"] = new_t or item["title"]
                                    st.session_state.article_images_pack = images_pack
                                    st.success("¡Imagen actualizada!")
                                    st.rerun()
                                else:
                                    st.warning("No se encontró otra alternativa diferente para esa consulta.")
                            except Exception as e_reg:
                                st.error(f"Error al regenerar: {e_reg}")

            st.markdown("---")

            # Botón para regenerar las 3 imágenes a la vez
            if st.button("🔄 Regenerar las 3 imágenes a la vez", use_container_width=True):
                with st.spinner("Regenerando el pack completo de 3 imágenes en alta definición..."):
                    try:
                        new_pack = safe_fetch_article_images_pack(
                            thematic=thematic.strip(),
                            subcategory=selected_subcategory,
                            country=country,
                            api_key=api_key_input,
                            width=1280
                        )
                        st.session_state.article_images_pack = new_pack
                        st.success("¡Pack de imágenes renovado exitosamente!")
                        st.rerun()
                    except Exception as e_all:
                        st.error(f"Error al regenerar el pack: {e_all}")

            with st.expander("🔍 Personalizar términos de búsqueda visual para cada imagen"):
                st.caption("Puedes ajustar el término o monumento para cualquiera de las 3 imágenes y volver a buscar:")
                col_q1, col_q2, col_q3 = st.columns(3)
                with col_q1:
                    q_portada = st.text_input("🌅 Búsqueda Portada:", value=images_pack[0]["query"] if len(images_pack) > 0 else "")
                with col_q2:
                    q_int1 = st.text_input("🏛️ Búsqueda Interior 1:", value=images_pack[1]["query"] if len(images_pack) > 1 else "")
                with col_q3:
                    q_int2 = st.text_input("🚶 Búsqueda Interior 2:", value=images_pack[2]["query"] if len(images_pack) > 2 else "")

                if st.button("🎨 Buscar con estos términos personalizados"):
                    with st.spinner("Buscando nuevas fotografías con los términos personalizados..."):
                        new_used = set()
                        custom_pack = []
                        new_queries = [q_portada, q_int1, q_int2]
                        for idx, cur_item in enumerate(images_pack):
                            target_q = new_queries[idx] if idx < len(new_queries) and new_queries[idx].strip() else cur_item["query"]
                            b, u, t = safe_regenerate_single_image(target_q, exclude_urls=new_used, width=1280)
                            if b:
                                new_used.add(u)
                                custom_pack.append({
                                    **cur_item,
                                    "query": target_q,
                                    "bytes": b,
                                    "url": u or "",
                                    "title": t or cur_item["title"]
                                })
                            else:
                                custom_pack.append({**cur_item, "query": target_q})
                        st.session_state.article_images_pack = custom_pack
                        st.rerun()

        else:
            st.info("💡 Aún no se ha generado el pack de imágenes para este artículo.")
            if st.button("📸 Generar Pack de 3 Imágenes Ahora (1 Portada + 2 Interior)", type="primary", use_container_width=True):
                with st.spinner("Buscando y optimizando 3 fotografías en alta definición para este artículo..."):
                    try:
                        pack = safe_fetch_article_images_pack(
                            thematic=thematic.strip() if thematic else "Viajes",
                            subcategory=selected_subcategory,
                            country=country,
                            api_key=api_key_input,
                            width=1280
                        )
                        st.session_state.article_images_pack = pack
                        st.rerun()
                    except Exception as e_pack:
                        st.error(f"No fue posible generar el pack: {e_pack}")

st.markdown("---")
st.caption("Google Writer • Desarrollado con Streamlit, Gemini API con Google Search Grounding y Google Docs API.")
