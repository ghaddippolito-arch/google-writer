"""
Módulo de Memoria y Gestión del Historial de Artículos para ACI Writer.
Permite persistir, consultar, buscar, filtrar, recargar y respaldar todos
los artículos generados en la aplicación, incluyendo sus fuentes, métricas,
enlaces a Google Docs y metadatos de imágenes.
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "articles_memory.json")
MEMORY_IMAGES_DIR = os.path.join(BASE_DIR, "memory_images")


def _ensure_storage_ready() -> None:
    """Asegura que el directorio de imágenes y el archivo de memoria existan."""
    if not os.path.exists(MEMORY_IMAGES_DIR):
        try:
            os.makedirs(MEMORY_IMAGES_DIR, exist_ok=True)
        except Exception:
            pass

    if not os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def get_all_memory_articles() -> List[Dict[str, Any]]:
    """
    Retorna la lista completa de artículos almacenados en memoria,
    ordenados del más reciente al más antiguo.
    """
    _ensure_storage_ready()
    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            articles = json.load(f)
            if isinstance(articles, list):
                # Ordenar por fecha descendente
                return sorted(
                    articles,
                    key=lambda x: x.get("created_at", ""),
                    reverse=True
                )
    except Exception as e:
        print(f"[MEMORY] Error al leer historial: {e}", flush=True)

    return []


def save_article_to_memory(
    article_data: Dict[str, Any],
    thematic: str,
    category: str,
    subcategory: str,
    country: str,
    language: str,
    google_doc_url: Optional[str] = None,
    google_doc_id: Optional[str] = None,
    images_pack: Optional[List[Dict[str, Any]]] = None,
    existing_id: Optional[str] = None
) -> str:
    """
    Guarda o actualiza un artículo generado en la memoria permanente.
    Guarda también los bytes de las imágenes en disco si están disponibles.
    Retorna el ID único del artículo.
    """
    _ensure_storage_ready()
    articles = get_all_memory_articles()

    now = datetime.now()
    article_id = existing_id or f"art_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    # Guardar imágenes asociadas en disco
    images_meta = []
    if images_pack:
        art_img_dir = os.path.join(MEMORY_IMAGES_DIR, article_id)
        os.makedirs(art_img_dir, exist_ok=True)

        for img in images_pack:
            suffix = img.get("suffix", f"{img.get('id', 'img')}.jpg")
            img_filename = f"{img.get('id', 'img')}_{suffix}"
            img_path = os.path.join(art_img_dir, img_filename)

            if img.get("bytes"):
                try:
                    with open(img_path, "wb") as f_img:
                        f_img.write(img["bytes"])
                except Exception as e_w:
                    print(f"[MEMORY] Error guardando imagen {img_filename}: {e_w}", flush=True)

            images_meta.append({
                "id": img.get("id"),
                "role": img.get("role"),
                "badge": img.get("badge"),
                "description": img.get("description"),
                "query": img.get("query"),
                "title": img.get("title"),
                "url": img.get("url"),
                "suffix": suffix,
                "local_filename": img_filename
            })

    record = {
        "id": article_id,
        "created_at": now.isoformat(),
        "formatted_date": now.strftime("%d/%m/%Y, %H:%M"),
        "thematic": thematic.strip(),
        "title": article_data.get("title") or thematic.strip(),
        "category": category,
        "subcategory": subcategory,
        "country": country,
        "language": language,
        "word_count": article_data.get("word_count", 0),
        "reading_time_min": max(1, round(article_data.get("word_count", 0) / 200)),
        "model_used": article_data.get("model_used", ""),
        "markdown_text": article_data.get("text", ""),
        "sources": article_data.get("sources", []),
        "search_queries": article_data.get("search_queries", []),
        "google_doc_url": google_doc_url,
        "google_doc_id": google_doc_id,
        "has_google_doc": bool(google_doc_url),
        "images_metadata": images_meta
    }

    # Si ya existía un artículo con este ID, reemplazarlo; si no, agregarlo al inicio
    updated = False
    for idx, existing in enumerate(articles):
        if existing.get("id") == article_id:
            articles[idx] = record
            updated = True
            break

    if not updated:
        articles.insert(0, record)

    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"[MEMORY] Artículo '{article_id}' guardado exitosamente en memoria.", flush=True)
    except Exception as e:
        print(f"[MEMORY] Error al escribir en articles_memory.json: {e}", flush=True)

    return article_id


def update_article_google_doc(
    article_id: str,
    google_doc_url: str,
    google_doc_id: str
) -> bool:
    """
    Actualiza la URL y el ID de Google Docs para un artículo existente en memoria.
    """
    _ensure_storage_ready()
    articles = get_all_memory_articles()
    found = False

    for item in articles:
        if item.get("id") == article_id:
            item["google_doc_url"] = google_doc_url
            item["google_doc_id"] = google_doc_id
            item["has_google_doc"] = True
            found = True
            break

    if found:
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[MEMORY] Error actualizando Google Doc: {e}", flush=True)

    return False


def get_article_by_id(article_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene un artículo específico por su ID."""
    articles = get_all_memory_articles()
    for art in articles:
        if art.get("id") == article_id:
            return art
    return None


def load_article_images_pack(article_id: str) -> List[Dict[str, Any]]:
    """
    Carga el pack de imágenes asociado a un artículo desde disco o metadatos.
    """
    art = get_article_by_id(article_id)
    if not art:
        return []

    images_meta = art.get("images_metadata", [])
    art_img_dir = os.path.join(MEMORY_IMAGES_DIR, article_id)
    pack: List[Dict[str, Any]] = []

    for meta in images_meta:
        local_filename = meta.get("local_filename")
        img_bytes = None
        if local_filename:
            full_path = os.path.join(art_img_dir, local_filename)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "rb") as f_img:
                        img_bytes = f_img.read()
                except Exception:
                    pass

        pack.append({
            "id": meta.get("id"),
            "role": meta.get("role"),
            "badge": meta.get("badge"),
            "description": meta.get("description"),
            "query": meta.get("query"),
            "title": meta.get("title"),
            "url": meta.get("url"),
            "suffix": meta.get("suffix"),
            "bytes": img_bytes
        })

    return pack


def delete_article_from_memory(article_id: str) -> bool:
    """Elimina un artículo de la memoria y borra sus imágenes guardadas."""
    _ensure_storage_ready()
    articles = get_all_memory_articles()
    new_articles = [a for a in articles if a.get("id") != article_id]

    if len(new_articles) == len(articles):
        return False

    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(new_articles, f, ensure_ascii=False, indent=2)

        # Borrar carpeta de imágenes si existe
        art_img_dir = os.path.join(MEMORY_IMAGES_DIR, article_id)
        if os.path.exists(art_img_dir):
            shutil.rmtree(art_img_dir, ignore_errors=True)

        return True
    except Exception as e:
        print(f"[MEMORY] Error al eliminar artículo: {e}", flush=True)
        return False


def export_memory_backup() -> str:
    """Exporta todo el historial en formato JSON para copia de seguridad."""
    articles = get_all_memory_articles()
    return json.dumps(articles, ensure_ascii=False, indent=2)


def import_memory_backup(json_str: str) -> Tuple[int, int]:
    """
    Importa artículos desde una copia de seguridad JSON.
    Retorna una tupla (artículos_nuevos_agregados, total_en_archivo).
    """
    _ensure_storage_ready()
    try:
        incoming = json.loads(json_str)
        if not isinstance(incoming, list):
            return 0, 0

        current = get_all_memory_articles()
        current_ids = {a.get("id") for a in current if a.get("id")}
        added_count = 0

        for inc in incoming:
            if not isinstance(inc, dict) or not inc.get("thematic"):
                continue
            inc_id = inc.get("id")
            if not inc_id or inc_id not in current_ids:
                if not inc_id:
                    inc["id"] = f"art_imported_{uuid.uuid4().hex[:8]}"
                current.append(inc)
                current_ids.add(inc["id"])
                added_count += 1

        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)

        return added_count, len(incoming)
    except Exception as e:
        print(f"[MEMORY] Error importando backup: {e}", flush=True)
        return 0, 0


def get_memory_statistics() -> Dict[str, Any]:
    """Calcula estadísticas generales de la memoria de artículos."""
    articles = get_all_memory_articles()
    total_articles = len(articles)
    total_words = sum(a.get("word_count", 0) for a in articles)
    avg_words = round(total_words / total_articles) if total_articles > 0 else 0
    synced_docs = sum(1 for a in articles if a.get("has_google_doc"))

    categories_count: Dict[str, int] = {}
    destinations_count: Dict[str, int] = {}

    for a in articles:
        cat = a.get("category", "Sin categoría")
        categories_count[cat] = categories_count.get(cat, 0) + 1

        dest = a.get("country", "Global")
        destinations_count[dest] = destinations_count.get(dest, 0) + 1

    return {
        "total_articles": total_articles,
        "total_words": total_words,
        "avg_words": avg_words,
        "synced_docs": synced_docs,
        "top_categories": sorted(categories_count.items(), key=lambda x: x[1], reverse=True)[:5],
        "top_destinations": sorted(destinations_count.items(), key=lambda x: x[1], reverse=True)[:5]
    }


def render_memory_view() -> None:
    """Renderiza la interfaz completa de la Memoria e Historial de artículos en Streamlit."""
    import streamlit as st

    st.markdown("### 📚 Memoria y Archivo de Artículos")
    st.caption("Consulta todos los artículos generados, sus enlaces a Google Docs, estadísticas, o recárgalos en el redactor.")

    stats = get_memory_statistics()
    sm1, sm2, sm3, sm4 = st.columns(4)
    with sm1:
        st.metric("📑 Artículos en Memoria", f"{stats['total_articles']}")
    with sm2:
        st.metric("✍️ Palabras Acumuladas", f"{stats['total_words']:,}".replace(",", "."))
    with sm3:
        st.metric("📄 En Google Docs", f"{stats['synced_docs']}")
    with sm4:
        st.metric("📊 Promedio / Artículo", f"{stats['avg_words']} palabras")

    st.markdown("---")

    all_articles = get_all_memory_articles()

    if not all_articles:
        st.info("💡 Aún no tienes artículos guardados en la memoria. Puedes redactar uno en la pestaña **✍️ Redactor de Artículos** y se guardará automáticamente aquí.")
    else:
        # Controles de búsqueda y filtros
        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
        with f_col1:
            search_query = st.text_input("🔍 Buscar por temática, palabra clave o título:", placeholder="Ej: Nueva York, Japón, presupuesto...", key="mem_search")
        with f_col2:
            unique_cats = ["Todas"] + sorted(list({a.get("category", "") for a in all_articles if a.get("category")}))
            filter_cat = st.selectbox("📂 Categoría:", options=unique_cats, key="mem_cat_filter")
        with f_col3:
            sort_by = st.selectbox(
                "🔃 Ordenar:",
                ["Más recientes primero", "Más antiguos primero", "Mayor cantidad de palabras", "Alfabético (A-Z)"],
                key="mem_sort"
            )

        # Aplicar filtros
        filtered = list(all_articles)
        if search_query and search_query.strip():
            sq = search_query.strip().lower()
            filtered = [
                a for a in filtered
                if sq in a.get("title", "").lower()
                or sq in a.get("thematic", "").lower()
                or sq in a.get("markdown_text", "").lower()
            ]

        if filter_cat != "Todas":
            filtered = [a for a in filtered if a.get("category") == filter_cat]

        if sort_by == "Más recientes primero":
            filtered = sorted(filtered, key=lambda x: x.get("created_at", ""), reverse=True)
        elif sort_by == "Más antiguos primero":
            filtered = sorted(filtered, key=lambda x: x.get("created_at", ""))
        elif sort_by == "Mayor cantidad de palabras":
            filtered = sorted(filtered, key=lambda x: x.get("word_count", 0), reverse=True)
        elif sort_by == "Alfabético (A-Z)":
            filtered = sorted(filtered, key=lambda x: x.get("title", "").lower())

        st.caption(f"Mostrando **{len(filtered)} de {len(all_articles)} artículos** almacenados.")

        for art in filtered:
            art_id = art.get("id")
            has_doc = art.get("has_google_doc") and art.get("google_doc_url")
            doc_status = "📄 En Google Docs" if has_doc else "📝 Pendiente Google Docs"
            card_title = f"{art.get('title', 'Artículo')} ({art.get('formatted_date', '')}) • {art.get('word_count', 0)} palabras • {doc_status}"

            with st.expander(card_title, expanded=False):
                # Metadatos del artículo
                m_c1, m_c2, m_c3 = st.columns(3)
                with m_c1:
                    st.markdown(f"**📂 Categoría:** {art.get('category')}")
                    st.markdown(f"**📑 Subcategoría:** {art.get('subcategory')}")
                with m_c2:
                    st.markdown(f"**🎯 Audiencia:** {art.get('country')}")
                    st.markdown(f"**🌐 Idioma:** {art.get('language')}")
                with m_c3:
                    st.markdown(f"**⏱️ Tiempo estimado:** ~{art.get('reading_time_min', 5)} min")
                    st.markdown(f"**🤖 Modelo:** `{art.get('model_used', 'Gemini')}`")

                st.markdown("<br>", unsafe_allow_html=True)

                # Botones de acción
                b1, b2, b3, b4 = st.columns([2, 2, 2, 1])
                with b1:
                    if has_doc:
                        st.markdown(
                            f"""<a href="{art['google_doc_url']}" target="_blank" style="
                                background-color: #1a73e8; color: white; padding: 8px 16px;
                                border-radius: 6px; text-decoration: none; font-weight: bold;
                                display: inline-block; text-align: center; width: 100%;">
                                🔗 Abrir en Google Docs ↗
                            </a>""",
                            unsafe_allow_html=True
                        )
                    else:
                        st.caption("No exportado a Google Docs aún.")

                with b2:
                    if st.button("👁️ Cargar en el Redactor", key=f"load_art_{art_id}", type="primary", use_container_width=True):
                        st.session_state.article_data = {
                            "title": art.get("title"),
                            "text": art.get("markdown_text"),
                            "word_count": art.get("word_count", 0),
                            "sources": art.get("sources", []),
                            "search_queries": art.get("search_queries", []),
                            "model_used": art.get("model_used", "")
                        }
                        st.session_state.active_thematic = art.get("thematic", "")
                        st.session_state.google_doc_url = art.get("google_doc_url")
                        st.session_state.google_doc_id = art.get("google_doc_id")
                        st.session_state.current_article_id = art_id

                        # Cargar imágenes desde el almacenamiento si existen
                        pack = load_article_images_pack(art_id)
                        st.session_state.article_images_pack = pack
                        if pack and len(pack) > 0:
                            st.session_state.article_image_bytes = pack[0].get("bytes")

                        st.session_state.selected_view = "✍️ Redactor de Artículos"
                        st.rerun()

                with b3:
                    clean_fname = "".join(c for c in art.get("title", "articulo") if c.isalnum() or c in (" ", "_", "-")).rstrip().replace(" ", "_")
                    st.download_button(
                        label="💾 Descargar Markdown (.md)",
                        data=art.get("markdown_text", ""),
                        file_name=f"{clean_fname}.md",
                        mime="text/markdown",
                        key=f"dl_md_{art_id}",
                        use_container_width=True
                    )

                with b4:
                    if st.button("🗑️ Eliminar", key=f"del_art_{art_id}", use_container_width=True):
                        delete_article_from_memory(art_id)
                        st.success("Artículo eliminado.")
                        st.rerun()

                # Lectura rápida del contenido
                with st.expander("📖 Vista previa rápida del texto"):
                    st.markdown(art.get("markdown_text", ""))
                    sources = art.get("sources", [])
                    if sources:
                        st.markdown("<br>**Fuentes citadas:**", unsafe_allow_html=True)
                        for s in sources:
                            st.markdown(f"- [{s.get('title', 'Fuente')}]({s.get('url')})")

    st.markdown("---")

    # Copia de seguridad y restauración
    with st.expander("⚙️ Copia de Seguridad y Restauración de Memoria"):
        st.caption("Descarga una copia completa de todos tus artículos en formato JSON para guardarla en tu computadora, o restaura artículos desde un archivo anterior.")
        bk_col1, bk_col2 = st.columns(2)
        with bk_col1:
            bk_json = export_memory_backup()
            st.download_button(
                label="📥 Descargar Copia de Seguridad (.json)",
                data=bk_json,
                file_name=f"aci_writer_memoria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        with bk_col2:
            uploaded_bk = st.file_uploader("📤 Restaurar copia desde archivo .json", type=["json"], key="bk_uploader")
            if uploaded_bk is not None:
                if st.button("Restaurar Artículos", use_container_width=True):
                    try:
                        str_val = uploaded_bk.read().decode("utf-8")
                        added, total = import_memory_backup(str_val)
                        st.success(f"¡Se importaron {added} artículos nuevos (de {total} en el archivo)!")
                        st.rerun()
                    except Exception as e_imp:
                        st.error(f"Error al importar archivo: {e_imp}")
