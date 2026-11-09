"""Behavior checks beyond the eight supplied grading tests."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import tools
from template import ToolCallingAgent

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "raw-data" / "customer_queries.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_all_sample_queries(case):
    result = ToolCallingAgent().run(case["query"])
    assert result["status"] == "completed"
    calls = [entry["action"] for entry in result["trace"] if entry["action"]]
    assert [call["name"] for call in calls] == case["expected_tools"]
    for call in calls:
        expected_key = "expected_args"
        if len(calls) > 1:
            expected_key += "_catalog" if call["name"] == "search_product_catalog" else "_ticket"
        assert call["arguments"] == case[expected_key]
    if len(calls) > 1:
        assert result["iterations"] == 3
        assert result["trace"][-1]["action"] is None
        assert result["trace"][-1]["final_answer"] == result["answer"]
        assert "Vinpearl Resort & Spa Nha Trang" in result["answer"]
        assert "Phạm Thị Dung" in result["answer"]
        assert "TK-" in result["answer"]


@pytest.mark.parametrize("budget,expected", [
    ("1,2 tỷ", 1_200_000_000), ("5.5 triệu", 5_500_000),
    ("600.000.000 VNĐ", 600_000_000), ("600 000 000 đồng", 600_000_000),
    ("600tr", 600_000_000),
])
def test_budget_formats(budget, expected):
    result = ToolCallingAgent().run(f"Tôi muốn xem xe điện giá dưới {budget}")
    assert result["trace"][0]["action"]["arguments"]["max_price"] == expected


def test_ticket_append_preserves_records_and_timezone(isolated_data):
    path = isolated_data / "support_tickets.json"
    before = json.loads(path.read_text(encoding="utf-8"))
    first = tools.submit_support_ticket("Nguyễn An", "Xe bị lỗi", "HIGH")
    second = tools.submit_support_ticket("Trần Bình", "Phòng bị ẩm mốc")
    after = json.loads(path.read_text(encoding="utf-8"))
    assert after[:-2] == before
    assert len({ticket["ticket_id"] for ticket in after}) == len(after)
    assert after[-2]["ticket_id"] == first["ticket_id"]
    assert after[-1]["ticket_id"] == second["ticket_id"]
    assert datetime.fromisoformat(after[-1]["created_at"]).utcoffset() == timedelta(hours=7)


def test_corrupt_tickets_are_not_overwritten(isolated_data):
    path = isolated_data / "support_tickets.json"
    path.write_text("{broken", encoding="utf-8")
    result = tools.submit_support_ticket("An", "Xe bị lỗi")
    assert "error" in result
    assert path.read_text(encoding="utf-8") == "{broken"


def test_ticket_file_can_be_created(isolated_data):
    path = isolated_data / "support_tickets.json"
    path.unlink()
    result = tools.submit_support_ticket("An", "Xe bị lỗi")
    assert result["status"] == "open"
    assert json.loads(path.read_text(encoding="utf-8"))[0]["ticket_id"] == result["ticket_id"]


@pytest.mark.parametrize("content", [None, "{broken", '{"not": "a list"}'])
def test_catalog_failures_are_reported(isolated_data, content):
    path = isolated_data / "product_catalog.json"
    if content is None:
        path.unlink()
    else:
        path.write_text(content, encoding="utf-8")
    result = ToolCallingAgent().run("Xem xe điện giá dưới 600 triệu")
    assert "Không thể tra cứu" in result["answer"]
    assert "không tìm thấy" not in result["answer"]


def test_catalog_case_and_price_boundary():
    result = tools.search_product_catalog(" XE_DIEN ", 315_000_000)
    assert [product["name"] for product in result] == ["VinFast VF 3"]


def test_iteration_limit_stops_before_second_tool(isolated_data):
    path = isolated_data / "support_tickets.json"
    before = path.read_bytes()
    result = ToolCallingAgent(max_iterations=1).run(CASES[2]["query"])
    assert result["status"] == "max_iterations_reached"
    assert result["iterations"] == 1
    assert "Vinpearl" in result["answer"]
    assert "TK-" not in result["answer"]
    assert path.read_bytes() == before


def test_zero_iterations_runs_no_tool():
    result = ToolCallingAgent(max_iterations=0).run(CASES[0]["query"])
    assert result["status"] == "max_iterations_reached"
    assert result["iterations"] == 0
    assert result["trace"] == []


def test_two_tools_need_third_step_for_aggregation():
    result = ToolCallingAgent(max_iterations=2).run(CASES[2]["query"])
    assert result["status"] == "max_iterations_reached"
    assert result["iterations"] == 2
    assert len(result["trace"]) == 2
    assert [entry["action"]["name"] for entry in result["trace"]] == CASES[2]["expected_tools"]
    assert "Phạm Thị Dung" in result["answer"]
    assert "chưa hoàn tất" in result["answer"]


def test_catalog_output_uses_numbered_list():
    result = ToolCallingAgent().run(CASES[0]["query"])
    assert "1. VinFast VF 5 Plus" in result["answer"]
    assert "2. VinFast VF 3" in result["answer"]


def test_policy_words_do_not_hide_catalog_request():
    result = ToolCallingAgent().run("Xem xe điện VinFast giá dưới 600 triệu và thông tin bảo hành")
    assert result["trace"][0]["action"]["name"] == "search_product_catalog"
    assert "VF 3" in result["answer"]


def test_ticket_with_inactive_product():
    result = ToolCallingAgent().run("Tôi tên An, xe VF 8 không hoạt động, cần hỗ trợ.")
    call = result["trace"][0]["action"]
    assert call["name"] == "submit_support_ticket"
    assert call["arguments"]["issue_description"] == "Xe VF 8 không hoạt động"


def test_lab_faq_is_explicitly_labeled_as_sample():
    result = ToolCallingAgent().run(CASES[3]["query"])
    assert "10 năm" in result["answer"]
    assert "dữ liệu mẫu" in result["answer"]
    assert result["trace"][0]["action"] is None


def test_malformed_budget_does_not_crash():
    result = ToolCallingAgent().run("Xem xe điện giá dưới 1..2 tỷ")
    assert result["status"] == "invalid_input"
    assert result["trace"] == []


def test_missing_name_does_not_create_ticket(isolated_data):
    path = isolated_data / "support_tickets.json"
    before = path.read_bytes()
    result = ToolCallingAgent().run("Xe điện VinFast của tôi bị lỗi ADAS, cần xử lý gấp")
    assert "tên khách hàng" in result["answer"]
    assert all(entry["action"] is None for entry in result["trace"])
    assert path.read_bytes() == before


def test_low_priority_is_not_misread_as_urgent():
    result = ToolCallingAgent().run("Tôi tên An, xe VF 8 bị lỗi màn hình, không gấp.")
    assert result["trace"][0]["action"]["arguments"]["priority"] == "low"


def test_trace_is_reset_on_agent_reuse():
    agent = ToolCallingAgent()
    first = agent.run(CASES[0]["query"])
    second = agent.run(CASES[3]["query"])
    assert len(second["trace"]) == 1
    assert second["trace"][0]["action"] is None
    assert first["trace"][0]["action"]["name"] == "search_product_catalog"


def test_unexpected_tool_failure_is_visible(monkeypatch):
    def broken_tool(**kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setitem(tools.TOOL_MAP, "search_product_catalog", broken_tool)
    result = ToolCallingAgent().run(CASES[0]["query"])
    assert "simulated failure" in result["answer"]
    assert "error" in result["trace"][0]["observation"][0]


def test_out_of_scope_has_no_tools():
    result = ToolCallingAgent().run("Hãy tư vấn điện thoại Samsung")
    assert "Vingroup" in result["answer"]
    assert all(entry["action"] is None for entry in result["trace"])


@pytest.mark.parametrize("value", ["", "   ", None])
def test_empty_input(value):
    assert ToolCallingAgent().run(value)["status"] == "invalid_input"
