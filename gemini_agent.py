"""
Módulo para interactuar con la API de Gemini utilizando google-genai SDK y búsqueda web en tiempo real.
Soporta modelos activos (gemini-3.1-flash-lite, gemini-3-flash-preview, gemini-3.5-flash, gemini-3.8-flash)
con búsqueda web en vivo en tiempo real (vía ddgs y Google Search Grounding), anclaje temporal obligatorio al año actual (2026),
y extracción rigurosa de fuentes oficiales y citas markdown funcionales.
"""

import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types


def fetch_live_web_sources(
    thematic: str,
    subcategory: str,
    country: str,
    year: int
) -> tuple[List[Dict[str, str]], List[str]]:
    """
    Realiza búsquedas web en vivo para obtener fuentes reales, vigentes y oficiales del año actual.
    Retorna una lista de fuentes con título, url y snippet, junto con las consultas ejecutadas.
    """
    # Limpiar temática para generar consultas concisas y de alta precisión
    clean_words = re.sub(r'[^\w\s]', ' ', thematic).split()
    core_thematic = " ".join(clean_words[:6]) if len(clean_words) > 6 else thematic.strip()

    queries = [
        f"{core_thematic} {country} {year}",
        f"{core_thematic} requisitos {year}",
        f"{core_thematic} {subcategory} {year}"
    ]
    
    sources: List[Dict[str, str]] = []
    executed_queries: List[str] = []
    seen_urls = set()

    try:
        from ddgs import DDGS
        ddgs = DDGS()
        for q in queries:
            try:
                executed_queries.append(q)
                results = list(ddgs.text(q, max_results=4))
                for item in results:
                    url = item.get("href") or item.get("url")
                    title = item.get("title") or "Fuente oficial"
                    body = item.get("body") or item.get("snippet") or ""
                    if url and url.startswith("http") and url not in seen_urls:
                        # Excluir urls genéricas o de buscadores
                        if not any(banned in url for banned in ["duckduckgo.com", "google.com/search", "bing.com"]):
                            seen_urls.add(url)
                            sources.append({
                                "title": title.strip(),
                                "url": url.strip(),
                                "snippet": body.strip()[:260]
                            })
            except Exception as e_query:
                print(f"[SEARCH] Consulta '{q}' omitida: {e_query}", flush=True)
                continue
    except Exception as e_ddg:
        print(f"[SEARCH] Error al inicializar búsqueda en vivo: {e_ddg}", flush=True)

    return sources, executed_queries


def build_prompt(
    thematic: str,
    language: str,
    country: str,
    category: str,
    subcategory: str,
    live_sources: Optional[List[Dict[str, str]]] = None,
    current_year: Optional[int] = None
) -> str:
    """
    Construye un prompt exhaustivo diseñado para generar artículos de +1500 palabras
    siguiendo estrictamente las directrices del 'Helpful Content System' y E-E-A-T de Google,
    con anclaje temporal obligatorio en el año actual (2026) y uso de fuentes reales.
    """
    if current_year is None:
        current_year = datetime.now().year

    # Construir el bloque de fuentes investigadas
    sources_context = ""
    if live_sources and len(live_sources) > 0:
        sources_context = f"### INVESTIGACIÓN WEB EN TIEMPO REAL (DATOS Y FUENTES VIGENTES {current_year}):\n"
        for idx, s in enumerate(live_sources[:8], 1):
            sources_context += f"{idx}. **{s['title']}**\n   - Enlace: {s['url']}\n   - Datos extraídos: {s.get('snippet', '')}\n"
        sources_context += (
            f"\nINSTRUCCIÓN DE USO DE FUENTES:\n"
            f"- DEBES incorporar estos datos y enlaces reales en el cuerpo del texto mediante enlaces markdown `[Texto](URL)`.\n"
            f"- Cita específicamente las páginas oficiales gubernamentales, embajadas, entidades de visados y sitios oficiales de turismo.\n"
        )
    else:
        sources_context = (
            f"### REQUISITO DE ENLACES Y FUENTES OFICIALES:\n"
            f"Debes incluir enlaces reales en formato markdown `[Texto](URL)` a portales oficiales de embajadas, "
            f"ministerios de relaciones exteriores, portales oficiales de turismo del destino, aerolíneas y asistencia al viajero (como Assist Card si aplica a la temática)."
        )

    return f"""
Actúa como un redactor sénior de contenido de viajes, especialista en SEO editorial y estratega de contenido con más de 12 años de experiencia.
Tu misión es redactar un artículo SEO exhaustivo, profundo, rigurosamente actualizado y de MÁS DE 1500 PALABRAS (extensión mínima obligatoria: 1500 palabras).

### Parámetros del artículo:
- **Temática principal:** {thematic}
- **Categoría:** {category}
- **Subcategoría:** {subcategory}
- **País de la audiencia objetivo:** {country}
- **Idioma de redacción:** {language}
- **Año actual:** {current_year}

---

### 🚨 REGLA TEMPORAL CRÍTICA (AÑO VIGENTE: {current_year}):
1. **ESTAMOS EN EL AÑO {current_year}:** Todo el artículo DEBE estar redactado estrictamente desde el presente del año {current_year}.
2. **PROHIBIDO HABLAR DE 2024 O 2025 COMO PRESENTE:** NUNCA escribas frases como "en este 2024", "para este 2024/2025" o "el próximo 2024". El año 2024 y 2025 son años pasados. Si los mencionas, debe ser únicamente en tiempo pasado o antecedente histórico (ej: "hasta finales de 2024...").
3. **DATOS VIGENTES:** Todas las normativas migratorias, visados, tasas turísticas, requisitos sanitarios, temporadas y costos deben estar actualizados a {current_year} y con proyección a {current_year + 1}.

---

### 🔗 REGLA OBLIGATORIA DE CITAS Y ENLACES REALES:
1. **Citas markdown en el texto:** Cada vez que menciones una ley, requisito de visa, portal gubernamental, embajada, aerolínea, servicio relevante (por ejemplo Assist Card si aplica a la subcategoría de asistencia) o sitio oficial de turismo, DEBES enlazarlo usando la sintaxis markdown: `[Nombre Descriptivo de la Fuente](https://url-real.com)`.
2. **Sección final obligatoria de fuentes:** Antes de la conclusión, debes incluir una sección con encabezado H2:
   `## 🌐 Fuentes y Enlaces Oficiales Consultados ({current_year})`
   Donde enlaces con viñetas al menos 3 a 5 portales oficiales y fuentes reales consultadas para verificar la información.

---

{sources_context}

---

### REGLAS FUNDAMENTALES DE 'HELPFUL CONTENT' DE GOOGLE Y E-E-A-T:
1. **Contenido enfocado en las personas (People-First):** El artículo debe responder directamente a la intención de búsqueda real del viajero, resolviendo dudas concretas con consejos prácticos y vivenciales, no contenido genérico o de relleno.
2. **Datos reales actualizados a {current_year}:** Proporciona datos precisos sobre precios aproximados, tipos de cambio, requisitos gubernamentales o de visados vigentes en {current_year}, sitios oficiales de turismo, normativas de equipaje o transporte actuales.
3. **Adaptación a la audiencia de {country}:** Adapta el vocabulario, las referencias prácticas (moneda local o conversión clara, documentación requerida para ciudadanos de {country}, aeropuertos o conexiones frecuentes) pensando en los viajeros de {country}.
4. **Estructura jerárquica clara (SEO On-Page):**
   - Un único título H1 optimizado para SEO al inicio (atractivo, con gancho y palabra clave principal).
   - Introducción con gancho (problema/solución/promesa).
   - Cuadro resumen de claves rápidas ("Lo más importante en 60 segundos").
   - Mínimo 6 secciones principales con encabezados `## H2` y subsecciones `### H3` que aborden el tema en profundidad.
   - Listas con viñetas, tablas comparativas (por ejemplo de precios, temporadas o requisitos en {current_year}) y bloques destacados tipo `> 💡 Consejo de experto:`.
   - Sección de Preguntas Frecuentes (FAQ) con mínimo 5 preguntas de alto valor con respuestas completas.
   - Conclusión reflexiva y llamada a la acción constructiva para la planificación del viaje en {current_year}.

---

### ESTRUCTURA REQUERIDA (Para asegurar +1500 palabras de calidad):
1. **# Título SEO Impactante (H1)**
2. **Introducción Empática y Contexto del Viajero en {current_year}** (~150 palabras)
3. **Puntos Clave / Resumen Rápido ({current_year})** (~100 palabras)
4. **Sección 1: Panorama General y Contexto Específico** (~250 palabras)
5. **Sección 2: Guía Paso a Paso / Requisitos y Datos Clave Actualizados** (~300 palabras con enlaces oficiales)
6. **Sección 3: Análisis Detallado según la Subcategoría ({subcategory})** (~350 palabras con datos concretos y recomendaciones verificadas)
7. **Sección 4: Tabla Comparativa o Desglose Práctico de Costos y Temporadas ({current_year})** (~200 palabras)
8. **Sección 5: Errores Comunes que Debes Evitar y Consejos de Seguridad/Ahorro** (~200 palabras)
9. **Sección 6: Preguntas Frecuentes (FAQ Schema-friendly)** (~250 palabras, mínimo 5 preguntas con respuestas completas)
10. **## 🌐 Fuentes y Enlaces Oficiales Consultados ({current_year})** (Lista con viñetas y enlaces markdown reales)
11. **Conclusión y Recomendaciones Finales** (~150 palabras)

**IMPORTANTE:**
- Extiéndete en cada punto con explicaciones ricas, ejemplos reales y datos precisos. NO resumas ni seas breve; la longitud mínima es 1500 palabras.
- Empieza directamente con el título `# H1`.
""".strip()


def generate_seo_article(
    api_key: str,
    thematic: str,
    language: str,
    country: str,
    category: str,
    subcategory: str,
    model_name: str = "gemini-3.1-flash-lite"
) -> Dict[str, Any]:
    """
    Genera el artículo SEO utilizando los modelos Gemini activos.
    Ejecuta investigación web en vivo y anclaje al año actual (2026).
    Maneja cuotas de herramientas de búsqueda de forma transparente para evitar errores 429.
    """
    if not api_key or not api_key.strip():
        raise ValueError("La API Key de Gemini es obligatoria. Por favor ingrésala en la barra lateral.")

    clean_key = api_key.strip()
    client = genai.Client(api_key=clean_key)
    current_year = datetime.now().year

    # 1. Ejecutar investigación web en tiempo real
    print(f"[SEARCH] Investigando en tiempo real para '{thematic}' ({current_year})...", flush=True)
    live_sources, search_queries = fetch_live_web_sources(
        thematic=thematic,
        subcategory=subcategory,
        country=country,
        year=current_year
    )
    print(f"[SEARCH] Se encontraron {len(live_sources)} fuentes web en tiempo real.", flush=True)

    # 2. Construir prompt contextualizado con las fuentes y el año actual
    prompt = build_prompt(
        thematic=thematic,
        language=language,
        country=country,
        category=category,
        subcategory=subcategory,
        live_sources=live_sources,
        current_year=current_year
    )

    # Lista de modelos activos prioritarios en este entorno
    active_models_queue = [
        model_name,
        "gemini-3.1-flash-lite",
        "gemini-3-flash-preview",
        "gemini-3.5-flash",
        "gemini-3.8-flash"
    ]
    # Eliminar duplicados manteniendo orden
    models_to_try = []
    for m in active_models_queue:
        if m and m not in models_to_try:
            models_to_try.append(m)

    response = None
    last_error = None
    used_model = models_to_try[0]
    grounding_sources: List[Dict[str, str]] = []

    # Iterar sobre los modelos probados
    for current_model in models_to_try:
        # Intento 1: Con Google Search Grounding de Gemini
        try:
            print(f"[GEN] Probando '{current_model}' con Google Search Grounding...", flush=True)
            search_cfg = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.7,
                max_output_tokens=8192,
            )
            response = client.models.generate_content(
                model=current_model,
                contents=prompt,
                config=search_cfg,
            )
            used_model = current_model
            print(f"[GEN] Éxito con búsqueda en '{current_model}'!", flush=True)

            # Extraer fuentes de grounding si estuvieron disponibles
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                grounding_metadata = getattr(candidate, "grounding_metadata", None)
                if grounding_metadata:
                    if hasattr(grounding_metadata, "web_search_queries") and grounding_metadata.web_search_queries:
                        for q in grounding_metadata.web_search_queries:
                            if q not in search_queries:
                                search_queries.append(q)
                    grounding_chunks = getattr(grounding_metadata, "grounding_chunks", None)
                    if grounding_chunks:
                        for chunk in grounding_chunks:
                            web = getattr(chunk, "web", None)
                            if web:
                                title = getattr(web, "title", "Fuente")
                                uri = getattr(web, "uri", "")
                                if uri:
                                    grounding_sources.append({"title": title, "url": uri})
            break

        except Exception as e_search:
            print(f"[GEN] Google Search Tool no disponible en '{current_model}' ({e_search}). Generando con fuentes inyectadas...", flush=True)

            # Intento 2: Si la herramienta de búsqueda de Google devuelve 429 o no está habilitada,
            # generar directamente utilizando las fuentes web reales ya inyectadas en el prompt.
            try:
                direct_cfg = types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                )
                response = client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=direct_cfg,
                )
                used_model = current_model
                print(f"[GEN] Éxito directo con '{current_model}' y fuentes web inyectadas!", flush=True)
                break
            except Exception as e_direct:
                last_error = e_direct
                print(f"[GEN] Falló directo en '{current_model}': {e_direct}", flush=True)
                continue

    if response is None:
        raise RuntimeError(
            f"No fue posible generar el artículo. Último error: {last_error}"
        )

    article_text = response.text or ""

    # Extraer enlaces markdown generados en el texto para enriquecer la lista de fuentes
    markdown_links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', article_text)

    # Consolidar todas las fuentes únicas (Grounding + Búsqueda en vivo + Enlaces en el texto)
    all_sources: List[Dict[str, str]] = []
    seen_urls = set()

    # Prioridad 1: Fuentes de Grounding oficial si hubo
    for s in grounding_sources:
        u = s.get("url", "")
        if u and u not in seen_urls:
            seen_urls.add(u)
            all_sources.append(s)

    # Prioridad 2: Enlaces explícitos citados en el texto por el modelo
    for anchor, u in markdown_links:
        if u not in seen_urls and not any(skip in u for skip in ["example.com", "localhost", "url-real.com"]):
            seen_urls.add(u)
            all_sources.append({"title": anchor.strip(), "url": u.strip()})

    # Prioridad 3: Fuentes obtenidas en la investigación previa
    for s in live_sources:
        u = s.get("url", "")
        if u and u not in seen_urls:
            seen_urls.add(u)
            all_sources.append({"title": s.get("title", "Fuente"), "url": u})

    words = article_text.split()
    word_count = len(words)

    # Extraer el título H1 del artículo
    title = f"{thematic} - {subcategory}"
    for line in article_text.splitlines():
        clean_line = line.strip()
        if clean_line.startswith("# "):
            title = clean_line.lstrip("#").strip()
            break

    return {
        "text": article_text,
        "word_count": word_count,
        "title": title,
        "sources": all_sources,
        "search_queries": search_queries,
        "model_used": used_model
    }
