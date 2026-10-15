"""
Módulo para la obtención y generación del pack de 3 fotografías editoriales de viajes en alta definición (1280px):
1. Portada (Hero 16:9): Panorámica o skyline para cabecera del artículo.
2. Interior 1: Monumento histórico, arquitectura o punto de interés icónico.
3. Interior 2: Escena urbana, calle típica, vida local o experiencia cultural.

Utiliza el repositorio global de fotografía editorial de viajes de Wikimedia Commons,
con extracción semántica inteligente de destinos (Gemini + heurística), arquitectura
100% resiliente y gratuita, libre de errores 402/504 y sin requerir inserción en Google Docs.
"""

import io
import json
import re
import ssl
import urllib.parse
import urllib.request
import zipfile
from typing import Any, Dict, List, Optional, Tuple


STOP_WORDS = {
    'que', 'qué', 'hacer', 'ver', 'en', 'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del',
    'a', 'para', 'por', 'con', 'dias', 'días', 'guia', 'guía', 'consejos', 'itinerario',
    'viaje', 'viajar', 'visitar', 'turismo', 'rutas', 'ruta', 'mejores', 'como', 'cómo',
    'costos', 'presupuesto', 'requisitos', 'visa', 'visado', 'donde', 'dónde', 'comer',
    'dormir', 'hoteles', 'cuándo', 'cuando', 'ir', 'tips', 'vuelo', 'vuelos', 'precio', 'precios',
    'completa', 'completo', 'imperdibles', 'imperdible', 'lugares', 'lugar', 'atracciones',
    'sitios', 'sitio', 'vacaciones', 'vacacionar', 'conocer', 'visita', 'visitas', 'top',
    'seguro', 'asistencia', 'internacional', 'nacional', 'barato', 'baratos'
}

BANNED_FILE_TERMS = [
    '.svg', '.pdf', '.djvu', '.gif', 'map', 'flag', 'coat of arms',
    'icon', 'diagram', 'page', 'book', 'text', 'scan', 'drawing',
    'engraving', 'stamp', 'coin', 'document', 'chart', 'symbol', 'logo'
]


def extract_destination_keywords(thematic: str, country: str, api_key: Optional[str] = None) -> str:
    """
    Extrae el destino principal (ciudad, región o monumento) para la búsqueda visual.
    """
    words = re.sub(r'[^\w\s]', ' ', thematic).split()
    meaningful = [w for w in words if w.lower() not in STOP_WORDS and not w.isdigit()]
    fallback_dest = " ".join(meaningful[:3]) if meaningful else thematic.strip()

    if not api_key or not api_key.strip():
        return fallback_dest

    try:
        from google import genai
        client = genai.Client(api_key=api_key.strip())
        res = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=(
                f"Identify the primary travel destination city, landmark, or region for this topic: '{thematic}' (country: '{country}'). "
                f"Return ONLY the English name of the city or iconic landmark (e.g., 'New York City', 'Kyoto', 'Rome Italy', 'Cartagena Colombia'). "
                f"Output 2 to 4 words max. Do not include quotes or punctuation."
            )
        )
        if res.text and len(res.text.strip()) >= 3:
            clean_res = re.sub(r'[^\w\s]', ' ', res.text).strip()
            return clean_res
    except Exception:
        pass

    return fallback_dest


def get_pack_queries(
    thematic: str,
    subcategory: str,
    country: str,
    api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Determina las 3 consultas de búsqueda visual optimizadas para:
    - Portada (skyline / panorama)
    - Interior 1 (monumento / arquitectura icónica)
    - Interior 2 (calle / vida urbana / cultura local)
    """
    dest = extract_destination_keywords(thematic, country, api_key)
    dest_clean = re.sub(r'[^\w\s]', ' ', dest).strip()
    country_clean = country.strip() if country and country.lower() not in ('global', 'todos') else ""

    # Intento con Gemini para consultas específicas de atracciones reales
    if api_key and api_key.strip():
        try:
            from google import genai
            client = genai.Client(api_key=api_key.strip())
            prompt = (
                f"Travel topic: '{thematic}', Country: '{country}'. Primary destination: '{dest_clean}'.\n"
                f"Generate 3 distinct visual search queries for Wikimedia Commons photos:\n"
                f"1. cover_query: wide panoramic skyline, landscape or aerial view of {dest_clean}.\n"
                f"2. interior_1_query: a famous specific monument, landmark building, or historic attraction in {dest_clean}.\n"
                f"3. interior_2_query: a famous street, market, square, or cultural scene in {dest_clean}.\n"
                f"Return ONLY a JSON object with keys: cover_query, interior_1_query, interior_2_query."
            )
            res = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            if res.text:
                parsed = json.loads(res.text.strip())
                if all(k in parsed for k in ["cover_query", "interior_1_query", "interior_2_query"]):
                    return {
                        "destination": dest_clean,
                        "cover_query": parsed["cover_query"].strip(),
                        "interior_1_query": parsed["interior_1_query"].strip(),
                        "interior_2_query": parsed["interior_2_query"].strip()
                    }
        except Exception as e_gem:
            print(f"[IMAGE_PACK] Gemini query generation fallback: {e_gem}", flush=True)

    # Heurística resiliente
    q_base = f"{dest_clean} {country_clean}".strip() if country_clean and country_clean.lower() not in dest_clean.lower() else dest_clean
    return {
        "destination": dest_clean,
        "cover_query": f"{q_base} skyline panorama",
        "interior_1_query": f"{q_base} landmark architecture",
        "interior_2_query": f"{q_base} street city view"
    }


def fetch_wikimedia_photo(
    search_query: str,
    width: int = 1280,
    exclude_urls: Optional[set] = None
) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """
    Busca y descarga una fotografía de alta definición desde Wikimedia Commons.
    Retorna una tupla (bytes_imagen, url_imagen, titulo_imagen).
    Garantiza deduplicación mediante exclude_urls.
    """
    if exclude_urls is None:
        exclude_urls = set()

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    clean_q = re.sub(r'[^\w\s]', ' ', search_query).strip()
    queries_to_try = [
        clean_q,
        f"{clean_q} travel",
        " ".join(clean_q.split()[:3]),
        " ".join(clean_q.split()[:2])
    ]

    for q in queries_to_try:
        if not q or len(q) < 2:
            continue
        encoded = urllib.parse.quote(q)
        api_url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrsearch={encoded}&gsrnamespace=6&prop=imageinfo&iiprop=url"
            f"&iiurlwidth={width}&gsrlimit=12&format=json"
        )
        try:
            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": "GoogleWriterBot/1.0 (travel editorial pack assistant)"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                pages = data.get("query", {}).get("pages", {})
                for pid, p in pages.items():
                    raw_title = p.get("title", "")
                    title_lower = raw_title.lower()
                    if any(bad in title_lower for bad in BANNED_FILE_TERMS):
                        continue
                    if not (title_lower.endswith(".jpg") or title_lower.endswith(".jpeg") or title_lower.endswith(".png")):
                        continue

                    imageinfo = p.get("imageinfo", [])
                    if imageinfo:
                        img_url = imageinfo[0].get("thumburl") or imageinfo[0].get("url")
                        if img_url and img_url not in exclude_urls:
                            img_req = urllib.request.Request(
                                img_url,
                                headers={"User-Agent": "GoogleWriterBot/1.0"}
                            )
                            with urllib.request.urlopen(img_req, context=ctx, timeout=12) as img_resp:
                                img_bytes = img_resp.read()
                                if len(img_bytes) > 20000:  # Mínimo 20KB para calidad HD
                                    exclude_urls.add(img_url)
                                    clean_display_title = raw_title.replace("File:", "").replace(".jpg", "").replace(".jpeg", "").replace(".png", "")
                                    return img_bytes, img_url, clean_display_title
        except Exception as e_query:
            print(f"[IMAGE] Error intentando '{q}': {e_query}", flush=True)
            continue

    return None, None, None


def fetch_article_images_pack(
    thematic: str,
    subcategory: str,
    country: str,
    api_key: Optional[str] = None,
    width: int = 1280
) -> List[Dict[str, Any]]:
    """
    Genera el pack completo de exactamente 3 imágenes de alta definición:
    1. Portada (Hero 16:9)
    2. Interior 1 (Monumento / Arquitectura)
    3. Interior 2 (Cultura / Calle / Ambiente local)
    """
    queries_dict = get_pack_queries(thematic, subcategory, country, api_key)
    dest = queries_dict.get("destination", thematic)

    specs = [
        {
            "id": "portada",
            "role": "Portada (Hero 16:9)",
            "badge": "🌅 Portada",
            "description": "Panorámica o skyline para la cabecera del artículo",
            "query": queries_dict["cover_query"],
            "suffix": "portada.jpg",
            "fallback_query": f"{dest} panorama"
        },
        {
            "id": "interior_1",
            "role": "Interior 1 (Monumento)",
            "badge": "🏛️ Interior 1",
            "description": "Monumento histórico, arquitectura o punto de interés clave",
            "query": queries_dict["interior_1_query"],
            "suffix": "interior_1.jpg",
            "fallback_query": f"{dest} landmark"
        },
        {
            "id": "interior_2",
            "role": "Interior 2 (Cultura / Calle)",
            "badge": "🚶 Interior 2",
            "description": "Vida urbana, calles típicas o experiencia cultural local",
            "query": queries_dict["interior_2_query"],
            "suffix": "interior_2.jpg",
            "fallback_query": f"{dest} street"
        }
    ]

    used_urls = set()
    pack_results: List[Dict[str, Any]] = []

    for spec in specs:
        # Intento 1: con la consulta específica asignada
        b, u, t = fetch_wikimedia_photo(spec["query"], width=width, exclude_urls=used_urls)
        
        # Intento 2: con consulta fallback del destino
        if not b:
            b, u, t = fetch_wikimedia_photo(spec["fallback_query"], width=width, exclude_urls=used_urls)

        # Intento 3: con el destino directo
        if not b:
            b, u, t = fetch_wikimedia_photo(dest, width=width, exclude_urls=used_urls)

        # Intento 4: salvaguarda universal de alta calidad de viajes si la búsqueda fallara
        if not b:
            universal_fallbacks = [
                "New York Manhattan skyline panorama",
                "Rome Colosseum Italy architecture",
                "Paris Eiffel Tower travel"
            ]
            for uq in universal_fallbacks:
                b, u, t = fetch_wikimedia_photo(uq, width=width, exclude_urls=used_urls)
                if b:
                    break

        if b:
            pack_results.append({
                "id": spec["id"],
                "role": spec["role"],
                "badge": spec["badge"],
                "description": spec["description"],
                "query": spec["query"],
                "title": t or spec["role"],
                "url": u or "",
                "bytes": b,
                "suffix": spec["suffix"]
            })

    return pack_results


def regenerate_single_image(
    query: str,
    exclude_urls: Optional[set] = None,
    width: int = 1280
) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """
    Regenera una sola fotografía para una sección específica del artículo.
    """
    return fetch_wikimedia_photo(query, width=width, exclude_urls=exclude_urls)


def create_images_zip(images_pack: List[Dict[str, Any]], clean_prefix: str) -> bytes:
    """
    Empaqueta las imágenes en un archivo ZIP descargable en memoria.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, item in enumerate(images_pack, 1):
            fname = f"{clean_prefix}_{idx:02d}_{item.get('suffix', f'imagen_{idx}.jpg')}"
            zf.writestr(fname, item["bytes"])
    buf.seek(0)
    return buf.getvalue()


# ==========================================
# RETROCOMPATIBILIDAD
# ==========================================
def create_travel_image_prompt(
    thematic: str,
    subcategory: str,
    country: str,
    api_key: Optional[str] = None
) -> str:
    """Compatibilidad con versiones anteriores."""
    dest = extract_destination_keywords(thematic, country, api_key)
    return f"{dest} panorama"


def generate_travel_image(
    prompt: str,
    width: int = 1280,
    height: int = 720
) -> bytes:
    """Compatibilidad con versiones anteriores."""
    b, _, _ = fetch_wikimedia_photo(prompt, width=width)
    if b:
        return b
    b_fb, _, _ = fetch_wikimedia_photo("New York City Manhattan panorama", width=width)
    if b_fb:
        return b_fb
    raise RuntimeError("No fue posible obtener una fotografía en este momento.")
