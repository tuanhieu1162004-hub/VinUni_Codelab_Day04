# Báo cáo hoàn thành Lab #4

Đề bài: [VinUni Codelab Day04](https://github.com/GDGoC-FPTU/VinUni_Codelab_Day04_Template),
đối chiếu `student_guide.md`, `starter-code/README.md`, autograder, bộ câu hỏi mẫu
và toàn bộ 24 trang [slide hướng dẫn](https://docs.google.com/presentation/d/1C_6NMasZka4Pl6a6YzDf1IlIi-BubuquRXm31ddsLUI/edit).

## 1. System Prompt

`starter-code/template.py` đã có đủ năm phần:

| Phần | Nội dung đã triển khai |
| --- | --- |
| Persona | VinAssistant, giao tiếp tiếng Việt, phạm vi mô phỏng lab |
| Available Tools | Mô tả tên, tham số, tác dụng của cả hai tool |
| Core Rules | Tra cứu trước khi tư vấn giá; không bịa mã ticket; hỏi thông tin còn thiếu |
| Operational Boundaries | Hệ sinh thái Vingroup; không tự hứa chính sách hoặc thời gian xử lý |
| Output Contract | Trace có quyết định ngắn, action, observation và câu trả lời cuối |

Simulator dùng các quy tắc đã cài đặt bằng Python, không gửi prompt đến LLM.

## 2. Tools và JSON Schema

Trong `starter-code/tools.py`:

- `search_product_catalog`: đọc JSON bằng UTF-8, lọc danh mục và giá `<= max_price`,
  nhận diện danh mục không phân biệt chữ hoa/thường; phân biệt lỗi đọc dữ liệu với
  danh sách kết quả rỗng.
- `submit_support_ticket`: kiểm tra đầu vào, đọc dữ liệu cũ, cấp mã
  `TK-YYYYMMDD-NNN` không trùng dữ liệu đang có, thêm ticket trạng thái `open`.
  Thời gian dùng múi giờ UTC+07:00. File tạm được thay thế nguyên tử sau khi ghi xong;
  JSON hỏng không bị ghi đè bằng danh sách mới.
- `TOOL_DEFINITIONS`: đủ hai schema, gồm kiểu dữ liệu, thuộc tính bắt buộc,
  enum danh mục/ưu tiên, giá trị mặc định và giới hạn tham số thừa.
- `TOOL_MAP`: ánh xạ tên tool sang hàm thực thi, được agent sử dụng khi dispatch.

## 3. Baseline và Agent Loop

Baseline không gọi tool và cố ý đưa ví dụ giá sai có gắn nhãn minh họa. Với câu hỏi
xe điện dưới 600 triệu, baseline bịa VF 5 Plus giá 400 triệu. Agent tra JSON và trả:

```text
Sản phẩm phù hợp theo danh mục lab:
1. VinFast VF 5 Plus: 548.000.000 VNĐ
2. VinFast VF 3: 315.000.000 VNĐ
```

Agent phân tích riêng hai intent, lấy danh mục/ngân sách/tên/mô tả/ưu tiên, sau đó
thực hiện tối đa một tool trong mỗi bước. Một tool tổng hợp ngay observation
thành câu trả lời, phù hợp `iterations == 1` của autograder. Hai tool cần 3 bước:
catalog, ticket, rồi bước tổng hợp riêng như slide 19 và sơ đồ trong student guide.
FAQ hoàn tất trong một bước và không gọi tool.

| Tình huống mẫu | Tool thực thi | Kết quả kiểm tra |
| --- | --- | --- |
| TC01: xe điện dưới 600 triệu | Catalog, `xe_dien`, 600.000.000 | Đúng tham số; có VF 3 và VF 5 Plus |
| TC02: Lê Minh Khoa báo lỗi ADAS | Ticket, ưu tiên `high` | Đúng tên, mô tả sự cố và mức ưu tiên |
| TC03: resort dưới 6 triệu + phản hồi phòng | Catalog rồi ticket, ưu tiên `medium` | Đúng cả hai tool, tham số và câu trả lời tổng hợp |
| TC04: FAQ bảo hành pin | Không gọi tool | Dùng tình huống bảo hành mẫu từ slide 19, ghi rõ đây là mô phỏng |
| TC05: xe dưới 200 triệu | Catalog, `xe_dien`, 200.000.000 | Thông báo không tìm thấy sản phẩm phù hợp |

Các giá trên là dữ liệu mẫu của bài lab.

## 4. Safeguards

- Dừng đúng `max_iterations`; giữ kết quả đã có và thông báo phần chưa hoàn tất.
- Không ghi ticket khi thiếu tên hoặc mô tả vấn đề.
- Báo lỗi tool qua observation và câu trả lời, không giả mã ticket thành công.
- Xóa trace cũ khi sử dụng lại cùng instance agent.
- Xử lý input trống, câu hỏi ngoài phạm vi, file thiếu và JSON hỏng.
- Đường dẫn dữ liệu tính từ `__file__`, độc lập thư mục chạy lệnh.

## 5. Kết quả kiểm thử

Đã chạy trên Windows với Python 3.13.18 (đúng giới hạn ở slide 6) và pytest 9.2.0:

```powershell
.venv/Scripts/python.exe -m pytest autograder -v
```

**41 passed**: 8 test gốc và 33 trường hợp bổ sung. Không sửa nội dung
`autograder/test_agent.py`. Bộ bổ sung kiểm tra đúng tham số cho cả 5 câu hỏi mẫu,
định dạng ngân sách, lưu nối tiếp ticket, timezone, file hỏng/thiếu, giới hạn bước,
thiếu tên, mức ưu tiên, reset trace, ngoại lệ tool và input không hợp lệ. Sau khi
đối chiếu slide, bổ sung kiểm tra bước tổng hợp thứ ba, danh sách đánh số, câu hỏi
kết hợp tra cứu/bảo hành, mô tả không hoạt động, nhãn FAQ mô phỏng và ngân sách sai.

Fixture trong `autograder/conftest.py` tạo bản sao dữ liệu riêng cho từng test.
Ticket kiểm thử không được thêm vào dữ liệu gốc. Demo `template.py` đã chạy thành công.

## 6. Cách chạy và giới hạn

Hướng dẫn cài đặt, demo và sử dụng Python nằm tại
[`starter-code/README.md`](starter-code/README.md).

Chương trình là mock dùng từ khóa/regex, không cần API key và chưa tích hợp Live API.
Các cách diễn đạt ngoài bộ luật có thể cần hỏi lại hoặc bổ sung parser. Mỗi lượt
`run` độc lập. Lưu trữ JSON phù hợp thực hành một process, không thay cho database
khi triển khai nhiều process hoặc nhiều máy chủ.

## 7. Đối chiếu slide và nộp bài

| Slide | Yêu cầu | Trạng thái |
| --- | --- | --- |
| 6, 12 | Python > 3.11 và < 3.14; môi trường ảo; cài requirements | Đã chuẩn bị Python 3.13.18 và `.venv` |
| 14–16 | Hai hàm tool và hai JSON Schema | Hoàn thành, giữ chữ ký và các trường dữ liệu yêu cầu |
| 17 | Prompt có phạm vi, quy tắc, định dạng; sản phẩm dùng bảng/danh sách đánh số | Hoàn thành |
| 18 | Baseline không dùng tool, có thể chạy mock | Hoàn thành bằng mock; Live API là tùy chọn, chưa tích hợp |
| 19 | Rule-based intent detection, gọi tool tuần tự, trace, max iterations, tổng hợp bước 3 | Hoàn thành |
| 20–22 | Chạy demo và hoàn thiện các file | Demo và toàn bộ kiểm thử đã chạy |
| 23–24 | Repo GitHub `VinUni-Codelab-Day04`, push bài làm, điền form | Chưa thực hiện; cần tài khoản và thông tin người nộp |

Khác biệt có chủ đích với mã minh họa: thiếu tên thì hỏi lại thay vì tự đặt tên
ẩn danh; không hứa liên hệ trong 24 giờ khi dữ liệu tool không có cam kết đó.
FAQ gắn nhãn dữ liệu mẫu của slide, không biến số liệu học tập thành chính sách thực tế.

Form nộp bài theo slide 24: https://forms.gle/nzwFKAooNbb7iot36.
