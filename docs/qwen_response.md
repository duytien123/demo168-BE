# OCR Response Reference

Tài liệu này mô tả response của endpoint OCR POC hiện tại trong `demo168-BE`.

Luồng đang dùng:

`local DeepSeek OCR -> tạo file .doc từ markdown_raw`

Service sử dụng tài liệu này:
- [ocr_local_qwen_poc.py](/Users/letien/Documents/Tien/demo168-BE/app/services/ocr_local_qwen_poc.py)

## 1. Response Của Endpoint POC

Endpoint:

```text
POST /ocr/poc/local-qwen/
```

Response normalized:

```json
{
  "provider": "local_deepseek_qwen",
  "file_name": "sample.pdf",
  "mime_type": "application/pdf",
  "pages_processed": 2,
  "markdown_raw": "## Trang 1\n\n...",
  "markdown_corrected": "## Trang 1\n\n...",
  "extracted": {},
  "export_file_name": "sample.doc",
  "export_content_type": "application/msword",
  "export_base64": "<base64-exported-file>",
  "warnings": []
}
```

### Ý nghĩa các field

- `provider`: tên pipeline đang dùng
- `file_name`: tên file upload
- `mime_type`: content type xác định được
- `pages_processed`: số ảnh/page đã OCR local
- `markdown_raw`: markdown thô từ local DeepSeek OCR
- `markdown_corrected`: hiện bằng đúng `markdown_raw` để giữ tương thích response shape
- `extracted`: hiện để trống `{}` vì đã bỏ luồng Qwen extract
- `export_file_name`: tên file export được dựng từ kết quả
- `export_content_type`: content type của file export
- `export_base64`: nội dung file export dưới dạng base64
- `warnings`: danh sách fallback hoặc lỗi mềm

## 1.1. Quy tắc file export

- Service luôn tạo file **`.doc`**
- Nội dung chính ghi vào file `.doc` luôn lấy từ `markdown_raw`
- `markdown_corrected` và `extracted` không tham gia vào bước dựng file

## 1.2. Cách lưu file export

Client chỉ cần decode `export_base64` và ghi ra file với tên `export_file_name`.

Ví dụ Python:

```python
import base64

with open(response["export_file_name"], "wb") as f:
    f.write(base64.b64decode(response["export_base64"]))
```

Ghi chú:
- File được dựng dưới dạng HTML tương thích Word và đóng gói với đuôi `.doc`.

## 2. Hành vi lỗi

### Local Ollama OCR lỗi

Endpoint trả lỗi HTTP 502:

```json
{
  "detail": "Local Ollama OCR call failed: ..."
}
```
