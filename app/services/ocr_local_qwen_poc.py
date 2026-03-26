import base64
import html
import io
import os
import re
from typing import Any, Dict, List

import requests
from fastapi import HTTPException, UploadFile

from app.config import get_settings
from app.constants.prompt import OcrDefault, OcrMarkdownProofread
from app.externals import ocr_api
from app.log import logger
from app.utils.utilities import to_dict


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

    try:
        proofread_markdown = _proofread_markdown_with_qwen(raw_markdown)
        if proofread_markdown.strip():
            corrected_markdown = proofread_markdown
        else:
            warnings.append("Qwen proofread returned empty content; raw markdown was kept.")
    except Exception as exc:
        logger.warning(f"Qwen proofread fallback activated for {file_name}: {exc}")
        warnings.append(f"Qwen proofread failed: {exc}")

    extracted: Dict[str, Any] = {}
    try:
        extracted = _extract_structured_data_with_qwen(corrected_markdown)
    except Exception as exc:
        logger.warning(f"Qwen structured extraction fallback activated for {file_name}: {exc}")
        warnings.append(f"Qwen structured extraction failed: {exc}")

    export_file_name, export_content_type, export_bytes = _build_export_artifact(
        source_file_name=file_name,
        source_mime_type=mime_type,
        markdown_corrected=corrected_markdown,
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


def _proofread_markdown_with_qwen(markdown_text: str) -> str:
    settings = get_settings()
    payload = {
        "model": settings.qwen_proofread_model,
        "system": OcrMarkdownProofread.SYSTEM,
        "prompt": OcrMarkdownProofread.PROMPT_TEMPLATE.format(ocr_markdown=markdown_text),
        "stream": False,
    }
    response = ocr_api.call(method="POST", json=payload)
    if response["status"] != 200:
        raise RuntimeError(response["error_message"] or "Qwen proofread request failed")

    return _extract_text_from_response(response["data"]).strip()


def _extract_structured_data_with_qwen(markdown_text: str) -> Dict[str, Any]:
    settings = get_settings()
    payload = {
        "model": settings.qwen_extract_model,
        "system": OcrDefault.SYSTEM.strip(),
        "prompt": OcrDefault.PROMPT_TEMPLATE.format(ocr_text=markdown_text),
        "stream": False,
        "format": "json",
    }
    response = ocr_api.call(method="POST", json=payload)
    if response["status"] != 200:
        raise RuntimeError(response["error_message"] or "Qwen structured extraction request failed")

    extracted = _extract_json_from_response(response["data"])
    if not extracted:
        raise RuntimeError("Qwen structured extraction returned no JSON payload")

    return extracted


def _extract_text_from_response(response: Any) -> str:
    try:
        data = response.json()
    except Exception:
        data = None

    if isinstance(data, dict):
        text = _find_text_candidate(data)
        if text:
            return text

    response_text = getattr(response, "text", "")
    if response_text:
        return response_text

    return ""


def _extract_json_from_response(response: Any) -> Dict[str, Any]:
    try:
        data = response.json()
    except Exception:
        data = None

    structured = _find_structured_candidate(data)
    if structured is not None:
        return structured

    raw_text = _extract_text_from_response(response)
    structured = _find_structured_candidate(raw_text)
    if structured is not None:
        return structured

    return {}


def _find_structured_candidate(value: Any) -> Dict[str, Any] | None:
    if value is None:
        return None

    if isinstance(value, dict):
        if "fixed" in value or "dynamic" in value:
            return value

        thinking = to_dict(value.get("thinking"))
        if thinking:
            nested = _find_structured_candidate(thinking)
            if nested is not None:
                return nested

        for key in ("response", "content", "text", "output_text", "generated_text", "data"):
            nested = _find_structured_candidate(value.get(key))
            if nested is not None:
                return nested

        message = value.get("message")
        nested = _find_structured_candidate(message)
        if nested is not None:
            return nested

        choices = value.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                nested = _find_structured_candidate(choice)
                if nested is not None:
                    return nested

        return None

    if isinstance(value, list):
        for item in value:
            nested = _find_structured_candidate(item)
            if nested is not None:
                return nested
        return None

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None

        as_dict = to_dict(stripped)
        if as_dict is not None:
            nested = _find_structured_candidate(as_dict)
            if nested is not None:
                return nested

        match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if match:
            as_dict = to_dict(match.group(0))
            if as_dict is not None:
                nested = _find_structured_candidate(as_dict)
                if nested is not None:
                    return nested

    return None


def _find_text_candidate(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        parts = [_find_text_candidate(item) for item in value]
        return "\n".join(part for part in parts if part).strip()

    if isinstance(value, dict):
        for key in ("response", "content", "text", "output_text", "generated_text"):
            text = _find_text_candidate(value.get(key))
            if text:
                return text

        thinking = value.get("thinking")
        if isinstance(thinking, str) and thinking.strip():
            return thinking

        message = value.get("message")
        text = _find_text_candidate(message)
        if text:
            return text

        choices = value.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                text = _find_text_candidate(choice)
                if text:
                    return text

    return ""


def _build_export_artifact(
    *,
    source_file_name: str,
    source_mime_type: str,
    markdown_corrected: str,
    extracted: Dict[str, Any],
    warnings: List[str],
) -> tuple[str, str, bytes]:
    if source_mime_type == "application/pdf":
        return (
            _build_output_file_name(source_file_name, extension="pdf"),
            "application/pdf",
            _build_pdf_bytes(
                source_file_name=source_file_name,
                markdown_corrected=markdown_corrected,
                extracted=extracted,
                warnings=warnings,
            ),
        )

    return (
        _build_output_file_name(source_file_name, extension="doc"),
        "application/msword",
        _build_doc_bytes(
            source_file_name=source_file_name,
            markdown_corrected=markdown_corrected,
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
    markdown_corrected: str,
    extracted: Dict[str, Any],
    warnings: List[str],
) -> bytes:
    extracted_html = _build_extracted_html(extracted)
    warnings_html = _build_warnings_html(warnings)
    markdown_html = _markdown_text_to_html(markdown_corrected)
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

  <h2>Nội dung đã hiệu chỉnh</h2>
  {markdown_html}

  <h2>Dữ liệu trích xuất</h2>
  {extracted_html}

  <h2>Cảnh báo</h2>
  {warnings_html}
</body>
</html>
    """
    return document_html.encode("utf-8")


def _build_pdf_bytes(
    *,
    source_file_name: str,
    markdown_corrected: str,
    extracted: Dict[str, Any],
    warnings: List[str],
) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    left_margin = 40
    right_margin = 40
    top_margin = 50
    bottom_margin = 40
    line_height = 16
    usable_width = page_width - left_margin - right_margin
    body_font, bold_font = _resolve_pdf_fonts(TTFont=TTFont, pdfmetrics=pdfmetrics)

    def new_page() -> float:
        pdf.showPage()
        pdf.setFont(body_font, 11)
        return page_height - top_margin

    def write_line(text: str, y: float, *, font_name: str | None = None, font_size: int = 11) -> float:
        if y < bottom_margin:
            y = new_page()
        pdf.setFont(font_name or body_font, font_size)
        pdf.drawString(left_margin, y, text)
        return y - line_height

    def wrap_text(text: str, *, font_name: str | None = None, font_size: int = 11) -> List[str]:
        normalized = text.replace("\t", "    ")
        if not normalized:
            return [""]

        wrapped_lines: List[str] = []
        for raw_line in normalized.splitlines() or [""]:
            words = raw_line.split()
            if not words:
                wrapped_lines.append("")
                continue

            current = words[0]
            for word in words[1:]:
                candidate = f"{current} {word}"
                active_font = font_name or body_font
                if stringWidth(candidate, active_font, font_size) <= usable_width:
                    current = candidate
                else:
                    wrapped_lines.append(current)
                    current = word
            wrapped_lines.append(current)

        return wrapped_lines

    def write_block(title: str, content_lines: List[str], y: float) -> float:
        y = write_line(title, y, font_name=bold_font, font_size=13)
        for content_line in content_lines:
            y = write_line(content_line, y)
        return y - 6

    y = page_height - top_margin
    y = write_line("Ket qua OCR", y, font_name=bold_font, font_size=16)
    y = write_line(f"File nguon: {source_file_name}", y)
    y -= 6

    markdown_lines = wrap_text(markdown_corrected or "(rong)")
    y = write_block("Noi dung da hieu chinh", markdown_lines, y)

    extracted_lines = _flatten_extracted_lines(extracted)
    y = write_block("Du lieu trich xuat", extracted_lines, y)

    warning_lines = warnings or ["Khong co canh bao."]
    warning_lines = [line for item in warning_lines for line in wrap_text(item)]
    y = write_block("Canh bao", warning_lines, y)

    pdf.save()
    return buffer.getvalue()


def _resolve_pdf_fonts(*, TTFont: Any, pdfmetrics: Any) -> tuple[str, str]:
    font_candidates = [
        ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("DejaVuSans", "/usr/local/share/fonts/DejaVuSans.ttf"),
        ("ArialUnicodeMS", "/Library/Fonts/Arial Unicode.ttf"),
        ("ArialUnicodeMS", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        ("ArialUnicodeMS", "/System/Library/AssetsV2/com_apple_MobileAsset_Font7/*/AssetData/Arial Unicode.ttf"),
    ]
    bold_candidates = [
        ("DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("DejaVuSans-Bold", "/usr/local/share/fonts/DejaVuSans-Bold.ttf"),
        ("ArialUnicodeMS", "/Library/Fonts/Arial Unicode.ttf"),
        ("ArialUnicodeMS", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ]

    body_font = _register_first_available_font(font_candidates, TTFont=TTFont, pdfmetrics=pdfmetrics) or "Helvetica"
    bold_font = _register_first_available_font(bold_candidates, TTFont=TTFont, pdfmetrics=pdfmetrics) or "Helvetica-Bold"
    return body_font, bold_font


def _register_first_available_font(font_candidates: List[tuple[str, str]], *, TTFont: Any, pdfmetrics: Any) -> str | None:
    for font_name, font_path in font_candidates:
        if "*" in font_path:
            continue
        if not os.path.exists(font_path):
            continue
        try:
            registered_fonts = pdfmetrics.getRegisteredFontNames()
            if font_name not in registered_fonts:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
            return font_name
        except Exception:
            continue
    return None


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


def _flatten_extracted_lines(extracted: Dict[str, Any]) -> List[str]:
    if not extracted:
        return ["Khong co du lieu trich xuat."]

    lines: List[str] = []
    for section_name in ("fixed", "dynamic"):
        section_data = extracted.get(section_name)
        lines.append(f"[{section_name}]")
        if not isinstance(section_data, dict) or not section_data:
            lines.append("Khong co du lieu.")
            lines.append("")
            continue

        for key, value in section_data.items():
            label, normalized_value = _normalize_extracted_item(value, fallback_label=key)
            value_text = normalized_value or "(rong)"
            lines.append(f"{key} | {label}: {value_text}")
        lines.append("")

    return lines
