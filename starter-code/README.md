# Lab #4 — Bài làm hoàn chỉnh

VinAssistant chạy bằng **Mock Simulator**, không cần API key, không gọi Live API.
`SYSTEM_PROMPT` và `TOOL_DEFINITIONS` là hợp đồng thiết kế cho agent; simulator
thực thi bằng keyword matching và regex như hướng dẫn lab.

Chạy các lệnh sau từ thư mục repo chứa `student_guide.md`:

```powershell
cd VinUni_Codelab_Day04
```

## Cài đặt

```powershell
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r starter-code/requirements.txt
```

Theo slide 6, sử dụng Python 3.12 hoặc 3.13. Khi clone repo mới, cần tạo `.venv`
và cài thư viện bằng các lệnh trên trước khi chạy demo/test.
Lệnh `py -3.13` yêu cầu Python Launcher. Nếu cài mới trên
Linux/macOS, thay `.venv/Scripts/python.exe` bằng `.venv/bin/python`.

## Chạy demo

```powershell
.venv/Scripts/python.exe -X utf8 starter-code/template.py
```

Demo so sánh baseline cố ý bịa giá với agent lấy giá từ JSON, đồng thời in trace.

## Chạy kiểm thử

```powershell
# 8 test gốc của bài lab
.venv/Scripts/python.exe -m pytest autograder/test_agent.py -v

# Toàn bộ test gốc và test bổ sung
.venv/Scripts/python.exe -m pytest autograder -v
```

`autograder/conftest.py` sao chép dữ liệu vào thư mục tạm cho từng test. Ticket
phát sinh trong kiểm thử không thay đổi `raw-data/support_tickets.json`.

## Sử dụng agent trong Python

Chạy Python từ `starter-code` để import `template`:

```python
from template import ToolCallingAgent

agent = ToolCallingAgent(max_iterations=5)
result = agent.run(
    "Cho tôi xem resort Vinpearl giá dưới 6 triệu. "
    "Và tôi cũng muốn ghi nhận phản hồi: tên tôi là Phạm Thị Dung, "
    "phòng tôi đặt ở Vinpearl Nha Trang bị ẩm mốc, mức độ trung bình."
)
print(result["answer"])
print(result["trace"])
```

Ví dụ trên gọi cả hai tool và **ghi ticket thật vào file JSON cục bộ**. Mỗi lần
gọi `run` là một yêu cầu độc lập, không lưu trí nhớ giữa các lượt hội thoại.

## Quy ước kết quả

- `answer`: câu trả lời tiếng Việt dựa trên kết quả tool.
- `trace`: các bước có `thought`, `action`, `observation`, và `final_answer` khi hoàn tất.
- `iterations`: số bước đã thực hiện; tối đa một tool mỗi bước. Một tool hoặc FAQ
  hoàn tất trong 1 bước; catalog + ticket dùng 3 bước theo slide 19: tra cứu,
  tạo ticket, rồi tổng hợp. Cần `max_iterations >= 3` cho tình huống này.
- `status`: `completed`, `max_iterations_reached`, hoặc `invalid_input`.

Lỗi tool được ghi trong observation và câu trả lời. `completed` nghĩa là vòng xử
lý đã kết thúc, không tự đồng nghĩa với việc ticket đã được tạo thành công.
Nếu thiếu tên hoặc mô tả, agent hỏi bổ sung và chưa gọi tool tạo ticket.

## Giới hạn

Đây là bài lab mô phỏng bằng từ khóa, không phải trợ lý production hiểu mọi cách
diễn đạt. Dữ liệu sản phẩm là dữ liệu mẫu, không phải giá bán hiện hành. FAQ bảo
hành pin trích tình huống mô phỏng ở slide 19, ghi rõ nguồn mẫu và không xác nhận
chính sách hiện hành. Các FAQ khác chưa có kho chính sách đầy đủ.
Ghi ticket dùng file tạm và thay thế nguyên tử, có khóa giữa các thread trong
cùng process; không dùng cho nhiều process ghi đồng thời.

Xem [báo cáo bài làm](../LAB_REPORT.md) để đối chiếu các milestone.
