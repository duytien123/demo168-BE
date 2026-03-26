import base64
import html
import io
import re
from typing import Dict, List

import requests
from fastapi import HTTPException, UploadFile

from app.config import get_settings
from app.log import logger


LOCAL_DEEPSEEK_MARKDOWN_PROMPT = "<|grounding|>Convert the document to markdown."
LOCAL_DEEPSEEK_OPTIONS = {"temperature": 0}
PDF_MAX_DIMENSION = 3000
PDF_TARGET_DPI = 144


async def run_local_qwen_poc(file: UploadFile) -> Dict[str, Any]:
    file_name = file.filename or "upload"
    mime_type = file.content_type or _guess_content_type_from_filename(file_name)
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    if not _is_supported_file(mime_type, file_name):
        raise HTTPException(status_code=400, detail="Only image files and PDF files are supported")

    rendered_images = _materialize_input_images(file_bytes=file_bytes, mime_type=mime_type, file_name=file_name)
    raw_markdown = _ocr_images_to_markdown(rendered_images)

    if not raw_markdown.strip():
        raise HTTPException(status_code=502, detail="Local DeepSeek OCR returned empty markdown")

    warnings: List[str] = []
    corrected_markdown = raw_markdown
    extracted: Dict[str, str] = {}

    export_file_name, export_content_type, export_bytes = _build_export_artifact(
        source_file_name=file_name,
        markdown_source=raw_markdown,
        extracted=extracted,
        warnings=warnings,
    )

    return {
        "provider": "local_deepseek_qwen",
        "file_name": file_name,
        "mime_type": mime_type,
        "pages_processed": len(rendered_images),
        "markdown_raw": raw_markdown,
        "markdown_corrected": corrected_markdown,
        "extracted": extracted,
        "export_file_name": export_file_name,
        "export_content_type": export_content_type,
        "export_base64": base64.b64encode(export_bytes).decode("utf-8"),
        "warnings": warnings,
    }


def _is_supported_file(mime_type: str, file_name: str) -> bool:
    if mime_type.startswith("image/") or mime_type == "application/pdf":
        return True
    lowered = file_name.lower()
    return lowered.endswith((".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif", ".pdf"))


def _guess_content_type_from_filename(file_name: str) -> str:
    lowered = file_name.lower()
    if lowered.endswith(".pdf"):
        return "application/pdf"
    if lowered.endswith(".png"):
        return "image/png"
    if lowered.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lowered.endswith(".webp"):
        return "image/webp"
    if lowered.endswith(".heic"):
        return "image/heic"
    if lowered.endswith(".heif"):
        return "image/heif"
    return "application/octet-stream"


def _materialize_input_images(*, file_bytes: bytes, mime_type: str, file_name: str) -> List[bytes]:
    if mime_type == "application/pdf" or file_name.lower().endswith(".pdf"):
        return _extract_pdf_page_bytes(file_bytes)
    return [_preprocess_image_bytes(file_bytes)]


def _load_image_module():
    from PIL import Image

    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
    except Exception:
        pass

    Image.MAX_IMAGE_PIXELS = None
    return Image


def _preprocess_image_bytes(file_bytes: bytes) -> bytes:
    Image = _load_image_module()

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")

            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            return img_buffer.getvalue()
    except Exception as exc:
        logger.warning(f"Falling back to raw image bytes because preprocessing failed: {exc}")
        return file_bytes


def _extract_pdf_page_bytes(file_bytes: bytes) -> List[bytes]:
    import fitz

    Image = _load_image_module()
    images: List[bytes] = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    try:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            rect = page.rect
            width, height = rect.width, rect.height

            zoom = PDF_TARGET_DPI / 72.0
            if (width * zoom > PDF_MAX_DIMENSION) or (height * zoom > PDF_MAX_DIMENSION):
                zoom = PDF_MAX_DIMENSION / max(width, height)
            zoom = max(zoom, 0.5)

            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            images.append(img_buffer.getvalue())
    finally:
        doc.close()

    return images


def _ocr_images_to_markdown(images: List[bytes]) -> str:
    markdown_parts: List[str] = []

    for index, image_bytes in enumerate(images, start=1):
        page_markdown = _call_local_deepseek_markdown(image_bytes)
        page_markdown = page_markdown.strip()
        if not page_markdown:
            continue

        if len(images) == 1:
            markdown_parts.append(page_markdown)
        else:
            markdown_parts.append(f"## Trang {index}\n\n{page_markdown}")

    return "\n\n".join(part for part in markdown_parts if part).strip()


def _call_local_deepseek_markdown(image_bytes: bytes) -> str:
    settings = get_settings()
    url = f"{settings.ollama_host.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {
                "role": "user",
                "content": LOCAL_DEEPSEEK_MARKDOWN_PROMPT,
                "images": [base64.b64encode(image_bytes).decode("utf-8")],
            }
        ],
        "options": LOCAL_DEEPSEEK_OPTIONS,
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=settings.request_timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Local Ollama OCR call failed: {exc}") from exc

    data = response.json()
    content = data.get("message", {}).get("content", "")
    if isinstance(content, str):
        return content
    return ""


def _build_export_artifact(
    *,
    source_file_name: str,
    markdown_source: str,
    extracted: Dict[str, Any],
    warnings: List[str],
) -> tuple[str, str, bytes]:
    return (
        _build_output_file_name(source_file_name, extension="doc"),
        "application/msword",
        _build_doc_bytes(
            source_file_name=source_file_name,
            markdown_source=markdown_source,
            extracted=extracted,
            warnings=warnings,
        ),
    )


def _build_output_file_name(source_file_name: str, *, extension: str) -> str:
    base_name = source_file_name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if "." in base_name:
        base_name = base_name.rsplit(".", 1)[0]
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", base_name).strip("._") or "ocr_result"
    return f"{safe_name}.{extension}"


def _build_doc_bytes(
    *,
    source_file_name: str,
    markdown_source: str,
    extracted: Dict[str, Any],
    warnings: List[str],
) -> bytes:
    extracted_html = _build_extracted_html(extracted)
    warnings_html = _build_warnings_html(warnings)
    markdown_html = _markdown_text_to_html(markdown_source)
    title = html.escape(source_file_name)

    document_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: "Times New Roman", serif; font-size: 12pt; line-height: 1.5; margin: 24px; }}
    h1, h2 {{ margin-bottom: 8px; }}
    h2 {{ margin-top: 20px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 8px; }}
    th, td {{ border: 1px solid #000; padding: 6px 8px; vertical-align: top; text-align: left; }}
    th {{ background: #f0f0f0; }}
    pre {{ white-space: pre-wrap; word-break: break-word; }}
    .warning {{ color: #a94442; }}
  </style>
</head>
<body>
  <h1>Kết quả OCR</h1>
  <p><strong>File nguồn:</strong> {title}</p>

  <h2>Nội dung OCR local</h2>
  {markdown_html}

  <h2>Dữ liệu trích xuất</h2>
  {extracted_html}

  <h2>Cảnh báo</h2>
  {warnings_html}
</body>
</html>
    """
    return document_html.encode("utf-8")


def _markdown_text_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    html_parts: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            html_parts.append("<p>&nbsp;</p>")
            continue
        if stripped.startswith("### "):
            html_parts.append(f"<h3>{html.escape(stripped[4:])}</h3>")
            continue
        if stripped.startswith("## "):
            html_parts.append(f"<h2>{html.escape(stripped[3:])}</h2>")
            continue
        if stripped.startswith("# "):
            html_parts.append(f"<h1>{html.escape(stripped[2:])}</h1>")
            continue
        html_parts.append(f"<p>{html.escape(line)}</p>")

    return "\n".join(html_parts) if html_parts else "<p></p>"


def _build_extracted_html(extracted: Dict[str, Any]) -> str:
    if not extracted:
        return "<p>Không có dữ liệu trích xuất.</p>"

    sections: List[str] = []
    for section_name in ("fixed", "dynamic"):
        section_data = extracted.get(section_name)
        if not isinstance(section_data, dict) or not section_data:
            sections.append(f"<h3>{html.escape(section_name)}</h3><p>Không có dữ liệu.</p>")
            continue

        rows: List[str] = []
        for key, value in section_data.items():
            label, normalized_value = _normalize_extracted_item(value, fallback_label=key)
            rows.append(
                "<tr>"
                f"<td>{html.escape(str(key))}</td>"
                f"<td>{html.escape(label)}</td>"
                f"<td>{html.escape(normalized_value)}</td>"
                "</tr>"
            )

        section_html = (
            f"<h3>{html.escape(section_name)}</h3>"
            "<table>"
            "<thead><tr><th>Key</th><th>Label</th><th>Value</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody>"
            "</table>"
        )
        sections.append(section_html)

    return "".join(sections)


def _normalize_extracted_item(value: Any, *, fallback_label: str) -> tuple[str, str]:
    if isinstance(value, dict):
        label = str(value.get("label") or fallback_label)
        raw_value = value.get("value")
    else:
        label = fallback_label
        raw_value = value

    if raw_value is None:
        normalized_value = ""
    elif isinstance(raw_value, list):
        normalized_value = ", ".join(str(item) for item in raw_value)
    else:
        normalized_value = str(raw_value)

    return label, normalized_value


def _build_warnings_html(warnings: List[str]) -> str:
    if not warnings:
        return "<p>Không có cảnh báo.</p>"

    items = "".join(f"<li class=\"warning\">{html.escape(item)}</li>" for item in warnings)
    return f"<ul>{items}</ul>"
