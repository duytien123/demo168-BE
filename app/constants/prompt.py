# from dataclasses import dataclass

# # OCR_MODEL = "qwen3-vl:2b"
# OCR_MODEL = "qwen3.5:2b"

# fixed_keys_explain = """
#        Giải thích KEY CỐ ĐỊNH:

#         1. loai_tai_lieu:
#         - Loại văn bản hành chính.
#         - Ví dụ: "Công văn", "Quyết định", "Thông báo", "Tờ trình", "Giấy chứng nhận".

#         2. so_ky_hieu:
#         - Địnhh nghĩa: là số hoặc ký hiệu văn bản
#         - Vị trí: không lấy trong nội dung chính, chỉ lấy nếu có ở đầu văn bảng.
#         - Thường có dạng: Số:1928/SKHCN-CĐS
#         - Số ký tự không quá 100
#         - Giữ nguyên ký tự gốc như ảnh (/, -, chữ in hoa).

#         3. ngay_tao:
#         - Ngày ban hành hoặc ngày tạo văn bản.
#         - Chuẩn hoá về định dạng DD/MM/YYYY nếu suy ra được.
#         - Nếu không xác định rõ → null.

#         4. year:
#         - Năm của văn bản (lấy từ ngày tạo nếu có).
#         - Phải là số nguyên (ví dụ: 2025).

#         5. month:
#         - Tháng của văn bản (lấy từ ngày tạo nếu có).
#         - Phải là số nguyên từ 1 đến 12.

#         6. sender:
#         - Cơ quan hoặc cá nhân ban hành văn bản.
#         - Ví dụ: "Sở Khoa học và Công nghệ tỉnh Đắk Lắk".

#         7. receiver:
#         - Đơn vị hoặc cá nhân nhận chính (Kính gửi).
#         - Không lấy phần "Nơi nhận" cuối văn bản.

#         8. cmnd:
#         - Số CMND (nếu có).
#         - Chỉ giữ chữ số.

#         9. cccd:
#         - Số CCCD (nếu có).
#         - Chỉ giữ chữ số (12 số).

#         10. noi_dung_chinh:
#         - Nội dung chính của văn bản.
#         - Có thể tóm tắt ngắn gọn nhưng giữ nguyên ý.

#         11. confidence: 
#         - Xác định độ tin cậy khi trích xuất dữ liệu, Ví dụ: 0.87

#         """

# @dataclass(frozen=True)
# class OcrDefault:
#     PROMPT = f"""
#         Bạn là hệ thống trích xuất dữ liệu từ ảnh văn bản hành chính Việt Nam.
#         Bạn hãy thực hiện từng bước bên đưới để trả về dữ liệu đung nhất có thể.

#         BƯỚC 1: Dựa vào KEY CỐ ĐỊNH bên dưới để xác định giá trị (value) và mô tả cho key (label).
#             - ví dụ:  {{"ngay_tao": {{"label": "ngày tạo", "value": "25/10/2025"}} }}
#             {fixed_keys_explain}

#         BƯỚC 2: bạn tự đề xuất các key quan trọng(dynamic):
#             - Có thể đề xuất thêm các key khác nếu thật sự cần.
#             - Key dynamic phải là snake_case không dấu.
#             - Nếu trùng với bất kỳ key cố định nào -> BỎ QUA (không thêm).
        
#         BƯỚC 3: Dựa vào KEY đã xuất ở BƯỚC 2 để xác định giá trị (value) và mô tả cho key (label).
#             - ví dụ: {{"address": {{"label": "Địa chỉ", "value": "TP HCM"}} }}

#         BƯỚC 4: OUTPUT (BẮT BUỘC): Tổng hợp từ BƯỚC 1 đến 3. Chỉ trả về 1 JSON object hợp lệ, theo đúng format bên dưới (gồm key, label, value).
#         {{
#             "fixed": {{
#                 "<fixed_key>": {{"label": "<string>", "value": <string|number|null|array_of_strings>}}
#             }},
#             "dynamic": {{
#                 "<dynamic_key>": {{"label": "<string>", "value": <string|number|null|array_of_strings>}}
#             }}
#         }}

#         BƯỚC 5: Quy tắc bắt buộc
#             - Data trả về theo đúng cấu trúc tại BƯỚC 4
#             - "fixed" phải chứa TẤT CẢ key cố định (đủ 11 key), tất cả phải có label tiếng việt có nhĩa. Nếu không tìm thấy thì value = null.
#             - "dynamic" chỉ chứa key mới, không trùng fixed, tất cả phải có label tiếng việt có nhĩa. Có thể là {{}}.
#             - Array nếu có thì luôn là array of strings.
#             - Chuẩn hoá:
#                 + ngay_tao: "DD/MM/YYYY" hoặc null
#                 + year/month: int hoặc null
#                 + cmnd/cccd: chỉ chữ số hoặc null
#                 + confidence: float 0..1 hoặc null

#         BƯỚC 6: Kiểm tra lại
#             - Kiểm tra lại kết quả của bạn trước khi trả về cho tất cả các BƯỚC 1 đến 5
        
#         BƯỚC 7: trả về kết quả đúng nhất sau khi đã kiểm tra và sửa lại.
#         """

#     SYSTEM = "Bạn là hệ thống trích xuất dữ liệu từ ảnh văn bản hành chính Việt Nam vì vậy hãy trả lời chính xác và gắn gọn."


from dataclasses import dataclass

OCR_MODEL = "qwen3-vl:4b"
# OCR_MODEL = "qwen3.5:2b"

fixed_keys_explain = """
    Giải thích KEY CỐ ĐỊNH:

    1. loai_tai_lieu:
    - Loại văn bản hành chính.
    - Ví dụ: "Công văn", "Quyết định", "Thông báo", "Tờ trình", "Giấy chứng nhận".

    2. so_ky_hieu:
    - Định nghĩa: là số hoặc ký hiệu văn bản.
    - Vị trí: không lấy trong nội dung chính, chỉ lấy nếu có ở đầu văn bản.
    - Thường có dạng: Số: 1928/SKHCN-CĐS
    - Số ký tự không quá 100.
    - Giữ nguyên ký tự gốc như ảnh (/, -, chữ in hoa).

    3. ngay_tao:
    - Ngày ban hành hoặc ngày tạo văn bản.
    - Chuẩn hoá về định dạng DD/MM/YYYY nếu suy ra được.
    - Nếu không xác định rõ → null.

    4. year:
    - Năm của văn bản (lấy từ ngày tạo nếu có).
    - Phải là số nguyên (ví dụ: 2025).

    5. month:
    - Tháng của văn bản (lấy từ ngày tạo nếu có).
    - Phải là số nguyên từ 1 đến 12.

    6. sender:
    - Cơ quan hoặc cá nhân ban hành văn bản.
    - Ví dụ: "Sở Khoa học và Công nghệ tỉnh Đắk Lắk".

    7. receiver:
    - Đơn vị hoặc cá nhân nhận chính (Kính gửi).
    - Không lấy phần "Nơi nhận" cuối văn bản.

    8. cmnd:
    - Vị trí: Ngay phía sau CMND hoặc CMTND (nếu có), không có thì để null
    - Chỉ giữ chữ số.

    9. cccd:
    - Vị trí: Ngay phía sau CCCD hoặc số căn cước công dân (nếu có).
    - Chỉ giữ chữ số (12 số).

    10. noi_dung_chinh:
    - Nội dung chính của văn bản.
    - Có thể tóm tắt ngắn gọn nhưng giữ nguyên ý.

    11. confidence:
    - Độ tin cậy khi trích xuất dữ liệu (kiểu số)
    """

@dataclass(frozen=True)
class OcrDefault:
    SYSTEM = """
        Bạn là hệ thống AI chuyên trích xuất dữ liệu từ VĂN BẢN HÀNH CHÍNH VIỆT NAM.

        Bạn phải phân tích OCR_TEXT và trích xuất dữ liệu.

        QUY TẮC BẮT BUỘC:
        - Chỉ trả về DUY NHẤT 1 JSON object hợp lệ.
        - Không giải thích.
        - Không thêm text ngoài JSON.

        QUY TẮC QUAN TRỌNG NHẤT:
        - TUYỆT ĐỐI KHÔNG được tự suy đoán hoặc tự tạo dữ liệu.
        - CHỈ được lấy dữ liệu xuất hiện trong OCR_TEXT.
        - Nếu OCR_TEXT không chứa thông tin cho một key → value = null.

        Ví dụ:
        Nếu OCR_TEXT không có "cccd" thì:
        "cccd": {"label": "Căn cước công dân", "value": null}

        Không được tạo số giả.
        Không được suy đoán.
        Không được điền giá trị mặc định.

        CẤU TRÚC VĂN BẢN:
        HEADER
        BODY
        FOOTER
        ...
        """

    # PROMPT: dùng cho text-only model. Bạn sẽ chèn OCR_TEXT vào cuối.
    # 
    PROMPT_TEMPLATE = f"""
        NHIỆM VỤ:
        Phân tích OCR_TEXT của một VĂN BẢN HÀNH CHÍNH VIỆT NAM và trích xuất dữ liệu.

        OCR_TEXT có thể sai chính tả hoặc thiếu dấu do OCR.

        HÃY DỰA VÀO CẤU TRÚC VĂN BẢN:

        HEADER:
        - Quốc hiệu
        - Tên cơ quan
        - Số / Ký hiệu văn bản
        - Địa danh, ngày tháng
        - Tiêu đề

        BODY:
        - Nội dung chính
        - Lý do
        - thông tin chính
        - cmnd
        - cccd

        FOOTER:
        - Chữ ký
        - Họ tên
        - Chức vụ
        - Nơi nhận

        QUY TẮC XÁC ĐỊNH DỮ LIỆU:

        - so_ky_hieu → thường nằm ở HEADER
        - ngay_tao → thường nằm ở HEADER
        - sender → HEADER hoặc FOOTER
        - receiver → sau cụm "Kính gửi"
        - noi_dung_chinh → BODY
        - cmnd → BODY
           +  Vị trí: Ngay phía sau CMND hoặc CMTND (nếu có), không có thì để null
        - cccd → BODY
            +  Vị trí: Ngay phía sau CCCD hoặc số căn cước công dân (nếu có).


        KHÔNG được tạo dữ liệu nếu OCR_TEXT không chứa thông tin đó.

        ------------------------------------------------

        OUTPUT BẮT BUỘC:

        Chỉ trả về DUY NHẤT 1 JSON object hợp lệ theo cấu trúc:

        {{
        "fixed": {{
            "loai_tai_lieu":   {{"label": "<string>", "value": <string|null>}},
            "so_ky_hieu":      {{"label": "<string>", "value": <string|null>}},
            "ngay_tao":        {{"label": "<string>", "value": <string|null>}},
            "year":            {{"label": "<string>", "value": <number|null>}},
            "month":           {{"label": "<string>", "value": <number|null>}},
            "sender":          {{"label": "<string>", "value": <string|null>}},
            "receiver":        {{"label": "<string>", "value": <string|null>}},
            "cmnd":            {{"label": "<string>", "value": <string|null>}},
            "cccd":            {{"label": "<string>", "value": <string|null>}},
            "noi_dung_chinh":  {{"label": "<string>", "value": <string|null>}},
            "confidence":      {{"label": "<string>", "value": <number|null>}}
        }},
        "dynamic": {{
            "<dynamic_key>": {{"label": "<string>", "value": <string|number|null|array_of_strings>}}
        }}
        }}

        ------------------------------------------------

        QUY TẮC BẮT BUỘC:

        1. "fixed" phải chứa ĐỦ 11 keys.
        2. Nếu không tìm thấy thông tin → value = null.
        3. Không được bịa dữ liệu.
        4. dynamic:
            - key phải snake_case không dấu
            - không trùng fixed key
            - có thể là {{}}
        5. QUY TẮC QUAN TRỌNG NHẤT:
            - CHỈ sử dụng dữ liệu xuất hiện trực tiếp trong OCR_TEXT.
            - KHÔNG được tự tạo thông tin.
            - KHÔNG được suy đoán.
            - Không bỏ dấu, thêm dấu.
            - KHÔNG được bổ sung dữ liệu từ kiến thức bên ngoài.
      

        nếu OCR_TEXT không chứa số đó.

        ------------------------------------------------

        CHUẨN HOÁ DỮ LIỆU:

        ngay_tao:
        - định dạng DD/MM/YYYY
        - nếu không rõ → null

        year:
        - số nguyên
        - lấy từ ngay_tao nếu có

        month:
        - số nguyên từ 1 đến 12

        cmnd / cccd:
        - chỉ giữ chữ số
        - cccd thường có 12 số

        confidence:
        - số thực từ 0 đến 1
        - thể hiện độ tin cậy của kết quả

        ------------------------------------------------

        GIẢI THÍCH KEY CỐ ĐỊNH:

        {fixed_keys_explain}

        ------------------------------------------------

        OCR_TEXT:

        <<<OCR_TEXT
        {{ocr_text}}
        OCR_TEXT
        >>>
        """.strip()


@dataclass(frozen=True)
class OcrMarkdownProofread:
    SYSTEM = """
        Bạn là hệ thống hậu xử lý OCR cho văn bản hành chính Việt Nam.

        Nhiệm vụ của bạn là sửa lỗi chính tả, lỗi dấu tiếng Việt và lỗi xuống dòng OCR
        khi và chỉ khi có căn cứ rõ ràng từ ngữ cảnh trong chính tài liệu.

        QUY TẮC BẮT BUỘC:
        - Chỉ trả về markdown đã hiệu chỉnh.
        - Giữ nguyên cấu trúc markdown, tiêu đề, bảng, danh sách nếu có.
        - Không thêm nội dung mới.
        - Không suy đoán dữ liệu bị thiếu.
        - Không thay đổi số hiệu, mã văn bản, ngày tháng, CMND, CCCD, tên riêng,
          ký hiệu hoặc số liệu nếu không chắc chắn.
        - Nếu không chắc chắn thì giữ nguyên.
        - Không thêm giải thích trước hoặc sau markdown.
        """.strip()

    PROMPT_TEMPLATE = """
        Hãy hiệu chỉnh OCR_MARKDOWN bên dưới theo đúng quy tắc.

        OCR_MARKDOWN:

        <<<OCR_MARKDOWN
        {ocr_markdown}
        OCR_MARKDOWN
        >>>
        """.strip()
