"""
Módulo para la generación de imágenes con Inteligencia Artificial (Flux / Pollinations).
Diseñado para crear imágenes de portada (Hero / Featured Images) en formato 16:9 panorámico
de alta resolución, con estilo fotográfico profesional de viajes listo para descargar.
"""

import urllib.parse
import urllib.request
import ssl
import random
from typing import Optional, Tuple
from google import genai


def create_travel_image_prompt(
    thematic: str,
    subcategory: str,
    country: str,
    api_key: Optional[str] = None
) -> str:
    """
    Crea un prompt visual optimizado en inglés utilizando Gemini (o plantilla si no está disponible)
    diseñado para generar fotografía de viajes cinematográfica y fotorrealista.
    """
    # Fallback predeterminado de alta calidad
    default_prompt = (
        f"Breathtaking cinematic wide travel photograph representing '{thematic}', "
        f"scenic landscape or iconic cityscape, golden hour sunset lighting, warm vibrant tones, "
        f"shot on 35mm lens, award-winning travel photography, 8k resolution, highly detailed, "
        f"clean composition, no text, no watermark, no logos"
    )

    if not api_key or not api_key.strip():
        return default_prompt

    try:
        client = genai.Client(api_key=api_key.strip())
        system_instruction = (
            "You are an expert AI prompt engineer specialized in hyper-realistic travel photography. "
            "Your task is to write a single-paragraph English prompt for generating an award-winning "
            "travel magazine cover image (16:9 panoramic ratio). "
            "Focus on: iconic visual atmosphere, natural golden hour lighting, cinematic composition, "
            "photorealistic details, architectural or natural splendor. "
            "CRITICAL: Do NOT include any text, letters, watermarks, or logos in the prompt description. "
            "Return ONLY the prompt string, nothing else."
        )

        res = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=(
                f"{system_instruction}\n\n"
                f"Article Theme: {thematic}\n"
                f"Subcategory: {subcategory}\n"
                f"Target Destination/Audience: {country}\n"
                f"Generate the visual prompt:"
            )
        )
        if res.text and len(res.text.strip()) > 20:
            clean_prompt = res.text.strip().replace('"', '').replace('\n', ' ')
            clean_prompt += ", cinematic 16:9, 8k resolution, photorealistic travel photography, no text, no watermark"
            return clean_prompt
    except Exception as e:
        print(f"[IMAGE_PROMPT] Usando prompt predeterminado por: {e}", flush=True)

    return default_prompt


def generate_travel_image(
    prompt: str,
    width: int = 1280,
    height: int = 720,
    model: str = "flux",
    seed: Optional[int] = None
) -> bytes:
    """
    Genera una imagen con Inteligencia Artificial utilizando el modelo Flux a través de Pollinations.
    Retorna los bytes en formato JPEG.
    """
    if seed is None:
        seed = random.randint(1000, 999999)

    encoded_prompt = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={width}&height={height}&model={model}&nologo=true&seed={seed}"
    )

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=45) as response:
            image_data = response.read()
            if len(image_data) > 1000:
                return image_data
            else:
                raise ValueError("La imagen recibida está vacía o dañada.")
    except Exception as e:
        # Reintento con modelo turbo si flux experimenta alta latencia
        if model == "flux":
            print(f"[IMAGE_GEN] Reintentando con modelo turbo por: {e}", flush=True)
            fallback_url = (
                f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                f"?width={width}&height={height}&model=turbo&nologo=true&seed={seed}"
            )
            req_fallback = urllib.request.Request(
                fallback_url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req_fallback, context=ctx, timeout=30) as fb_response:
                return fb_response.read()
        raise RuntimeError(f"Error al generar la imagen con IA: {e}")
