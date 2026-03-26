# Qwen Response Reference

Tài liệu này mô tả các dạng dữ liệu trả về từ Qwen mà `demo168-BE` đang chấp nhận trong luồng:

`local DeepSeek OCR -> Qwen proofread -> Qwen structured extract`

Service sử dụng tài liệu này:
- [ocr_local_qwen_poc.py](/Users/letien/Documents/Tien/demo168-BE/app/services/ocr_local_qwen_poc.py)

## 1. Proofread Markdown

Bước proofread dùng Qwen để sửa lỗi chính tả có kiểm soát và mong đợi **markdown text**.

Service sẽ cố lấy text theo thứ tự từ các key:
- `response`
- `content`
- `text`
- `output_text`
- `generated_text`
- `message`
- `choices[*]`
- fallback cuối cùng: `thinking` nếu `thinking` là string

### Ví dụ response hợp lệ

```json
{
  "model": "qwen3-vl:4b",
  "response": "# Công văn\n\nNội dung đã được sửa lỗi chính tả."
}
```

hoặc:

```json
{
  "choices": [
    {
      "message": {
        "content": "# Công văn\n\nNội dung đã được sửa lỗi chính tả."
      }
    }
  ]
}
```

### Kết quả mà service lấy ra

```text
# Công văn

Nội dung đã được sửa lỗi chính tả.
```

Nếu Qwen trả text rỗng hoặc call lỗi:
- service giữ nguyên `markdown_raw`
- thêm warning vào response

## 2. Structured Extract

Bước extract dùng Qwen để trích xuất JSON theo schema `fixed/dynamic`.

Service chấp nhận các dạng:

### 2.1. JSON nằm trực tiếp ở root

```json
{
  "fixed": {
    "loai_tai_lieu": { "label": "Loại tài liệu", "value": "Công văn" },
    "so_ky_hieu": { "label": "Số ký hiệu", "value": "123/SKHCN" }
  },
  "dynamic": {}
}
```

### 2.2. JSON nằm trong `thinking`

```json
{
  "thinking": "{\"fixed\": {\"loai_tai_lieu\": {\"label\": \"Loại tài liệu\", \"value\": \"Công văn\"}}, \"dynamic\": {}}"
}
```

### 2.3. JSON nằm trong text wrapper

```json
{
  "response": "{\"fixed\": {\"loai_tai_lieu\": {\"label\": \"Loại tài liệu\", \"value\": \"Công văn\"}}, \"dynamic\": {}}"
}
```

hoặc:

```json
{
  "choices": [
    {
      "message": {
        "content": "{\"fixed\": {\"loai_tai_lieu\": {\"label\": \"Loại tài liệu\", \"value\": \"Công văn\"}}, \"dynamic\": {}}"
      }
    }
  ]
}
```

## 3. Structured Schema Mong Đợi

Service mong đợi JSON có dạng:

```json
{
  "fixed": {
    "loai_tai_lieu": { "label": "Loại tài liệu", "value": "Công văn" },
    "so_ky_hieu": { "label": "Số ký hiệu", "value": "123/SKHCN" },
    "ngay_tao": { "label": "Ngày tạo", "value": "25/03/2026" },
    "year": { "label": "Năm", "value": 2026 },
    "month": { "label": "Tháng", "value": 3 },
    "sender": { "label": "Nơi gửi", "value": "Sở Khoa học và Công nghệ" },
    "receiver": { "label": "Nơi nhận", "value": "UBND tỉnh" },
    "cmnd": { "label": "Chứng minh nhân dân", "value": null },
    "cccd": { "label": "Căn cước công dân", "value": null },
    "noi_dung_chinh": { "label": "Nội dung chính", "value": "..." },
    "confidence": { "label": "Độ tin cậy", "value": 0.91 }
  },
  "dynamic": {
    "nguoi_ky": { "label": "Người ký", "value": "Nguyễn Văn A" }
  }
}
```

Lưu ý:
- `fixed` và `dynamic` là format Qwen extract trả về.
- POC hiện **không chuẩn hóa sâu thêm** nếu Qwen đã trả được JSON hợp lệ.
- Nếu Qwen extract lỗi hoặc không có JSON, field `extracted` trong API response sẽ là `{}` và warning sẽ được thêm vào.

## 4. Response Của Endpoint POC

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
  "extracted": {
    "fixed": {},
    "dynamic": {}
  },
  "export_file_name": "sample.pdf",
  "export_content_type": "application/pdf",
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
- `markdown_corrected`: markdown sau bước Qwen proofread
- `extracted`: JSON extract từ Qwen
- `export_file_name`: tên file export được dựng từ kết quả
- `export_content_type`: content type của file export
- `export_base64`: nội dung file export dưới dạng base64
- `warnings`: danh sách fallback hoặc lỗi mềm

## 4.1. Quy tắc chọn file export

- Nếu file upload có `mime_type = application/pdf` thì service tạo **PDF text**
- Nếu file upload là ảnh thì service tạo **`.doc`**

## 4.2. Cách lưu file export

Client chỉ cần decode `export_base64` và ghi ra file với tên `export_file_name`.

Ví dụ Python:

```python
import base64

with open(response["export_file_name"], "wb") as f:
    f.write(base64.b64decode(response["export_base64"]))
```

Ghi chú:
- Với ảnh: file được dựng dưới dạng HTML tương thích Word và đóng gói với đuôi `.doc`.
- Với PDF: file được dựng là PDF text, không phải ảnh chụp nhúng vào PDF.

## 5. Hành vi Fallback

### Qwen proofread lỗi

Response vẫn thành công nếu OCR local đã ra markdown:

```json
{
  "markdown_raw": "...",
  "markdown_corrected": "...same as raw...",
  "warnings": [
    "Qwen proofread failed: ..."
  ]
}
```

### Qwen structured extract lỗi

```json
{
  "extracted": {},
  "warnings": [
    "Qwen structured extraction failed: ..."
  ]
}
```

### Local Ollama OCR lỗi

Endpoint trả lỗi HTTP 502:

```json
{
  "detail": "Local Ollama OCR call failed: ..."
}
```
