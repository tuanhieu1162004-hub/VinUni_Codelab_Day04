# VinUni Codelab Day04 — Prompt Engineering & Tool Calling

Bài làm Lab #4: VinAssistant dùng hai tool tra cứu danh mục sản phẩm và tạo ticket
hỗ trợ. Chạy bằng mock simulator theo hướng dẫn lab, không cần API key.

## Cài đặt và chạy trên Windows

Cần Git và Python **3.12 hoặc 3.13** theo slide hướng dẫn.

```powershell
git clone https://github.com/tuanhieu1162004-hub/VinUni_Codelab_Day04.git
cd VinUni_Codelab_Day04
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r starter-code/requirements.txt
.\.venv\Scripts\python.exe -X utf8 starter-code/template.py
```

Nếu dùng Python 3.12, thay `py -3.13` bằng `py -3.12`. Trên Linux/macOS, tạo môi
trường bằng `python3.13 -m venv .venv` và dùng `.venv/bin/python` cho các lệnh sau đó.

## Kiểm thử

```powershell
# 8 test gốc
.\.venv\Scripts\python.exe -m pytest autograder/test_agent.py -v

# Toàn bộ test
.\.venv\Scripts\python.exe -m pytest autograder -v
```

Đã kiểm tra với Python 3.13.18: **41/41 test đạt**, gồm 8 test gốc và 33 trường hợp
bổ sung. Fixture dùng bản sao dữ liệu tạm, không thêm ticket test vào dữ liệu gốc.

## Nội dung bài làm

- System Prompt có persona, tools, quy tắc, phạm vi và định dạng đầu ra.
- `search_product_catalog`: đọc JSON, lọc danh mục và ngân sách VNĐ.
- `submit_support_ticket`: thêm ticket, giữ dữ liệu cũ, cấp ID và thời gian UTC+07:00.
- Hai JSON Schema và bảng dispatch `TOOL_MAP`.
- Intent detection độc lập cho catalog và ticket; một yêu cầu có thể dùng cả hai.
- Một tool hoặc FAQ hoàn tất trong 1 bước; hai tool dùng 3 bước theo slide:
  tra cứu, tạo ticket, tổng hợp kết quả.
- Trace, giới hạn vòng lặp, xử lý lỗi, kết quả rỗng và thiếu thông tin khách hàng.

Dữ liệu sản phẩm và FAQ là dữ liệu mẫu phục vụ học tập. Simulator dùng từ khóa và
regex; mỗi lần gọi `run` là một yêu cầu độc lập. Tạo ticket ngoài kiểm thử sẽ ghi vào
`raw-data/support_tickets.json`.

## Tài liệu

- [Báo cáo bài làm và đối chiếu slide](LAB_REPORT.md)
- [Hướng dẫn sử dụng agent và chạy thử](starter-code/README.md)
- [Đề bài gốc](student_guide.md)
- [Slide hướng dẫn](https://docs.google.com/presentation/d/1C_6NMasZka4Pl6a6YzDf1IlIi-BubuquRXm31ddsLUI/edit)
