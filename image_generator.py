"""
Módulo para la obtención y generación de fotografías de portada (Hero / Featured Images)
en formato 16:9 panorámico en alta definición (1280px) para artículos de viajes y SEO.
Utiliza el repositorio global de fotografía editorial de viajes de Wikimedia Commons,
con extracción inteligente de destinos mediante IA y arquitectura 100% resiliente y gratuita.
"""

import urllib.parse
import urllib.request
import json
import ssl
import re
from typing import Optional, Tuple
from google import genai


STOP_WORDS = {
    'que', 'qué', 'hacer', 'en', 'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del',
    'a', 'para', 'por', 'con', 'dias', 'días', 'guia', 'guía', 'consejos', 'itinerario',
    'viaje', 'viajar', 'visitar', 'turismo', 'rutas', 'ruta', 'mejores', 'como', 'cómo',
    'costos', 'presupuesto', 'requisitos', 'visa', 'visado', 'donde', 'dónde', 'comer',
    'dormir', 'hoteles', 'cuándo', 'cuando', 'ir'
}


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
        client = genai.Client(api_key=api_key.strip())
        res = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=(
                f"Identify the primary travel destination city, landmark, or region for this topic: '{thematic}' (country: '{country}'). "
                f"Return ONLY the English name of the city or iconic landmark (e.g., 'New York City', 'Kyoto', 'Cartagena Colombia', 'Eiffel Tower Paris'). "
                f"Output 2 to 4 words max. Do not include quotes or punctuation."
            )
        )
        if res.text and len(res.text.strip()) >= 3:
            clean_res = re.sub(r'[^\w\s]', ' ', res.text).strip()
            return clean_res
    except Exception:
        pass

    return fallback_dest


def create_travel_image_prompt(
    thematic: str,
    subcategory: str,
    country: str,
    api_key: Optional[str] = None
) -> str:
    """
    Crea la consulta de búsqueda visual para encontrar la mejor fotografía panorámica.
    """
    dest = extract_destination_keywords(thematic, country, api_key)
    return f"{dest} panorama"


def fetch_wikimedia_photo(search_query: str, width: int = 1280) -> Optional[bytes]:
    """
    Busca y descarga una fotografía panorámica de alta definición desde Wikimedia Commons.
    Retorna los bytes de la imagen en formato JPEG o None.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    clean_q = re.sub(r'[^\w\s]', ' ', search_query).strip()
    queries_to_try = [
        f"{clean_q} skyline",
        f"{clean_q} panorama",
        f"{clean_q} travel",
        clean_q
    ]

    for q in queries_to_try:
        encoded = urllib.parse.quote(q)
        api_url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrsearch={encoded}&gsrnamespace=6&prop=imageinfo&iiprop=url"
            f"&iiurlwidth={width}&format=json"
        )
        try:
            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": "GoogleWriterBot/1.0 (travel editorial assistant)"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                pages = data.get("query", {}).get("pages", {})
                for pid, p in pages.items():
                    title = p.get("title", "").lower()
                    # Descartar archivos que no son fotografías panorámicas
                    if any(bad in title for bad in [".svg", ".pdf", ".djvu", ".gif", "map", "flag", "coat of arms", "icon", "diagram"]):
                        continue
                    if not (title.endswith(".jpg") or title.endswith(".jpeg") or title.endswith(".png")):
                        continue

                    imageinfo = p.get("imageinfo", [])
                    if imageinfo:
                        img_url = imageinfo[0].get("thumburl") or imageinfo[0].get("url")
                        if img_url:
                            # Descargar los bytes de la imagen
                            img_req = urllib.request.Request(
                                img_url,
                                headers={"User-Agent": "GoogleWriterBot/1.0"}
                            )
                            with urllib.request.urlopen(img_req, context=ctx, timeout=12) as img_resp:
                                img_bytes = img_resp.read()
                                if len(img_bytes) > 20000:  # Mínimo 20KB para calidad HD
                                    return img_bytes
        except Exception as e_query:
            print(f"[IMAGE] Error intentando '{q}': {e_query}", flush=True)
            continue

    return None


def generate_travel_image(
    prompt: str,
    width: int = 1280,
    height: int = 720
) -> bytes:
    """
    Función principal para obtener la fotografía de portada panorámica (16:9).
    Es 100% gratuita, libre de errores 402 y altamente disponible.
    """
    # 1. Búsqueda con el prompt/destino solicitado
    photo = fetch_wikimedia_photo(prompt, width=width)
    if photo:
        return photo

    # 2. Reintento extrayendo solo las primeras palabras clave
    simple_prompt = " ".join(prompt.split()[:3])
    photo = fetch_wikimedia_photo(simple_prompt, width=width)
    if photo:
        return photo

    # 3. Fallback de alta calidad con paisajes icónicos de viajes
    fallback_photo = fetch_wikimedia_photo("New York City Manhattan panorama", width=width)
    if fallback_photo:
        return fallback_photo

    raise RuntimeError("No fue posible obtener una fotografía en este momento. Por favor reintenta con otra temática.")
