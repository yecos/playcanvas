"""
generate_caption.py - Genera captions para redes sociales usando LLM

Soporta:
  - OpenAI (GPT-4o-mini por defecto, configurable)
  - Ollama local (Llama 3.1 8B recomendado)
  - z-ai-web-dev-sdk (GLM-4.6)

Uso:
    from generate_caption import generate_caption
    caption = generate_caption(prompt="sunset over Tokyo", platform="instagram")

CLI:
    python generate_caption.py --prompt "sunset over Tokyo" --platform instagram
"""
import os
import sys
import argparse
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import cprint, info, ok, warn, error, ROOT_DIR


# Templates de prompt segun plataforma
PLATFORM_TEMPLATES = {
    "instagram": """Escribe un caption para Instagram basado en este prompt de generacion de imagen:
"{image_prompt}"

Requisitos:
- Maximo 2200 caracteres
- Incluir 5-10 hashtags relevantes al final
- Tono: profesional pero cercano
- Emoji: 1-3 emojis relevantes
- NO uses #ad #sponsored #spam
- NO menciones que es generado por IA (se anadira automaticamente si es requerido)

Devuelve SOLO el caption, sin prefijo.""",

    "twitter": """Escribe un tweet basado en este prompt de generacion de imagen:
"{image_prompt}"

Requisitos:
- Maximo 280 caracteres
- 1-3 hashtags maximo
- Tono: conciso, llamativo
- 1 emoji opcional

Devuelve SOLO el texto del tweet.""",

    "facebook": """Escribe un post para Facebook basado en este prompt de generacion de imagen:
"{image_prompt}"

Requisitos:
- Maximo 1000 caracteres
- 2-4 hashtags
- Tono: conversacional, invita a comentar
- 1-2 emojis

Devuelve SOLO el texto del post.""",

    "pinterest": """Escribe una descripcion para Pinterest basado en este prompt de generacion de imagen:
"{image_prompt}"

Requisitos:
- Maximo 500 caracteres
- 3-5 keywords al final (separados por espacios, no hashtags)
- Tono: descriptivo, optimizado para busqueda

Devuelve SOLO la descripcion.""",

    "youtube": """Escribe una descripcion para un video de YouTube basado en este prompt:
"{image_prompt}"

Requisitos:
- Maximo 5000 caracteres
- Primera linea: hook llamativo
- Incluir timestamps sugeridos (0:00, 0:30, etc.)
- 5-10 tags al final separados por comas

Devuelve SOLO la descripcion.""",

    "tiktok": """Escribe una descripcion para TikTok basado en este prompt de generacion de imagen:
"{image_prompt}"

Requisitos:
- Maximo 150 caracteres
- 3-5 hashtags trending (#fyp, #foryou, etc.)
- Tono: energetico, viral-friendly

Devuelve SOLO la descripcion.""",
}


def generate_caption_openai(image_prompt: str, platform: str,
                            model: str = "gpt-4o-mini") -> str:
    """Genera caption con OpenAI."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai no instalado. pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no configurada en .env")

    client = OpenAI(api_key=api_key)
    template = PLATFORM_TEMPLATES.get(platform, PLATFORM_TEMPLATES["instagram"])
    user_prompt = template.format(image_prompt=image_prompt)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Eres un copywriter experto en redes sociales. Generas captions atractivas y optimizadas para cada plataforma."},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=500,
        temperature=0.8,
    )
    return response.choices[0].message.content.strip()


def generate_caption_ollama(image_prompt: str, platform: str,
                            model: str = "llama3.1:8b") -> str:
    """Genera caption con Ollama local."""
    try:
        import requests
    except ImportError:
        raise RuntimeError("requests no instalado")

    ollama_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    template = PLATFORM_TEMPLATES.get(platform, PLATFORM_TEMPLATES["instagram"])
    user_prompt = template.format(image_prompt=image_prompt)

    response = requests.post(
        f"{ollama_url}/api/generate",
        json={
            "model": model,
            "prompt": user_prompt,
            "stream": False,
            "options": {"temperature": 0.8}
        },
        timeout=60
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def generate_caption_zai(image_prompt: str, platform: str) -> str:
    """Genera caption con z-ai-web-dev-sdk (GLM-4.6)."""
    try:
        import requests
    except ImportError:
        raise RuntimeError("requests no instalado")

    # z-ai-web-dev-sdk expone un endpoint compatible OpenAI
    api_key = os.environ.get("ZAI_API_KEY")
    if not api_key:
        raise RuntimeError("ZAI_API_KEY no configurada")

    template = PLATFORM_TEMPLATES.get(platform, PLATFORM_TEMPLATES["instagram"])
    user_prompt = template.format(image_prompt=image_prompt)

    response = requests.post(
        "https://api.z.ai/api/paas/v4/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "glm-4.6",
            "messages": [
                {"role": "system", "content": "Eres un copywriter experto en redes sociales."},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.8,
        },
        timeout=60
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def generate_caption(image_prompt: str, platform: str = "instagram",
                     backend: Optional[str] = None) -> str:
    """
    Genera un caption usando el LLM configurado.
    Si backend no se especifica, prueba en orden: openai -> ollama -> zai
    """
    if backend is None:
        # Auto-detectar segun env vars
        if os.environ.get("OPENAI_API_KEY"):
            backend = "openai"
        elif os.environ.get("OLLAMA_HOST") or _ollama_running():
            backend = "ollama"
        elif os.environ.get("ZAI_API_KEY"):
            backend = "zai"
        else:
            raise RuntimeError(
                "No hay LLM configurado. Set OPENAI_API_KEY, OLLAMA_HOST, o ZAI_API_KEY en .env"
            )

    if backend == "openai":
        return generate_caption_openai(image_prompt, platform)
    elif backend == "ollama":
        return generate_caption_ollama(image_prompt, platform)
    elif backend == "zai":
        return generate_caption_zai(image_prompt, platform)
    else:
        raise ValueError(f"Backend desconocido: {backend}")


def _ollama_running() -> bool:
    """Verifica si Ollama esta corriendo localmente."""
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Generador de captions con LLM")
    parser.add_argument("--prompt", required=True, help="Prompt de la imagen")
    parser.add_argument("--platform", default="instagram",
                        choices=list(PLATFORM_TEMPLATES.keys()))
    parser.add_argument("--backend", choices=["openai", "ollama", "zai"],
                        help="Forzar backend")
    args = parser.parse_args()

    try:
        caption = generate_caption(args.prompt, args.platform, args.backend)
        print(caption)
    except Exception as e:
        error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
