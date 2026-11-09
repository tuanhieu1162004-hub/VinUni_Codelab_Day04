"""Local JSON-backed tools for the Lab #4 mock agent."""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Dict, List

RAW_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "raw-data"))
DEFAULT_MAX_PRICE = 999999999999
VIETNAM_TZ = timezone(timedelta(hours=7))
_TICKET_LOCK = Lock()


def search_product_catalog(
    category: str, max_price: int = DEFAULT_MAX_PRICE
) -> List[Dict[str, Any]]:
    """Filter by category and inclusive VND budget; return an error object on failure."""
    if not isinstance(category, str) or category.strip().lower() not in {"xe_dien", "du_lich"}:
        return [{"error": "Danh mục phải là 'xe_dien' hoặc 'du_lich'."}]
    if isinstance(max_price, bool) or not isinstance(max_price, int) or max_price < 0:
        return [{"error": "Giá tối đa phải là số nguyên VNĐ không âm."}]
    try:
        with open(os.path.join(RAW_DATA_DIR, "product_catalog.json"), encoding="utf-8") as stream:
            products = json.load(stream)
        if not isinstance(products, list) or any(
            not isinstance(product, dict)
            or not isinstance(product.get("name"), str)
            or not isinstance(product.get("category"), str)
            or type(product.get("price_vnd")) is not int
            or product["price_vnd"] < 0
            for product in products
        ):
            return [{"error": "Dữ liệu danh mục sản phẩm không hợp lệ."}]
        return [
            product for product in products
            if product["category"].lower() == category.strip().lower()
            and product["price_vnd"] <= max_price
        ]
    except FileNotFoundError:
        return [{"error": "Product catalog file not found."}]
    except (OSError, ValueError) as exc:
        return [{"error": f"Không thể đọc danh mục sản phẩm: {exc}"}]


def submit_support_ticket(
    customer_name: str, issue_description: str, priority: str = "medium"
) -> Dict[str, Any]:
    """Append a validated ticket without overwriting records on read/write errors."""
    if not isinstance(customer_name, str) or not customer_name.strip():
        return {"error": "Vui lòng cung cấp tên khách hàng."}
    if not isinstance(issue_description, str) or not issue_description.strip():
        return {"error": "Vui lòng cung cấp mô tả vấn đề."}
    if not isinstance(priority, str) or priority.strip().lower() not in {"low", "medium", "high"}:
        return {"error": "Mức ưu tiên phải là low, medium hoặc high."}

    tickets_file = os.path.join(RAW_DATA_DIR, "support_tickets.json")
    with _TICKET_LOCK:
        temporary_file = None
        try:
            existing_tickets = []
            if os.path.exists(tickets_file):
                with open(tickets_file, encoding="utf-8") as stream:
                    existing_tickets = json.load(stream)
            if not isinstance(existing_tickets, list) or any(
                not isinstance(ticket, dict) or not isinstance(ticket.get("ticket_id"), str)
                for ticket in existing_tickets
            ):
                return {"error": "Dữ liệu ticket không hợp lệ; chưa tạo ticket mới."}

            now = datetime.now(VIETNAM_TZ)
            existing_ids = {ticket["ticket_id"] for ticket in existing_tickets}
            sequence = len(existing_tickets) + 1
            ticket_id = f"TK-{now:%Y%m%d}-{sequence:03d}"
            while ticket_id in existing_ids:
                sequence += 1
                ticket_id = f"TK-{now:%Y%m%d}-{sequence:03d}"
            ticket = {
                "ticket_id": ticket_id,
                "customer_name": customer_name.strip(),
                "issue_description": issue_description.strip(),
                "priority": priority.strip().lower(),
                "status": "open",
                "created_at": now.isoformat(),
                "category": "general",
            }
            existing_tickets.append(ticket)
            # Replace only after the entire new JSON has been written successfully.
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=RAW_DATA_DIR,
                prefix=".tickets-", suffix=".tmp", delete=False
            ) as stream:
                temporary_file = stream.name
                json.dump(existing_tickets, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
            os.replace(temporary_file, tickets_file)
            return {
                "ticket_id": ticket_id,
                "customer_name": ticket["customer_name"],
                "priority": ticket["priority"],
                "status": "open",
                "message": f"Ticket {ticket_id} đã được tạo thành công.",
            }
        except (OSError, ValueError) as exc:
            return {"error": f"Không thể lưu yêu cầu hỗ trợ: {exc}"}
        finally:
            if temporary_file and os.path.exists(temporary_file):
                os.unlink(temporary_file)


TOOL_DEFINITIONS = [
    {
        "name": "search_product_catalog",
        "description": "Tra cứu sản phẩm/dịch vụ Vingroup theo danh mục và giá tối đa (VNĐ).",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string", "enum": ["xe_dien", "du_lich"],
                    "description": "xe_dien: xe điện VinFast; du_lich: dịch vụ Vinpearl.",
                },
                "max_price": {
                    "type": "integer", "minimum": 0, "default": DEFAULT_MAX_PRICE,
                    "description": "Giá tối đa bằng VNĐ, bao gồm giá bằng ngưỡng.",
                },
            },
            "required": ["category"],
            "additionalProperties": False,
        },
    },
    {
        "name": "submit_support_ticket",
        "description": "Tạo và lưu ticket khi khách hàng báo sự cố hoặc yêu cầu ghi nhận phản hồi.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string", "minLength": 1, "description": "Tên do khách hàng cung cấp.",
                },
                "issue_description": {
                    "type": "string", "minLength": 1, "description": "Vấn đề do khách hàng cung cấp.",
                },
                "priority": {
                    "type": "string", "enum": ["low", "medium", "high"],
                    "default": "medium", "description": "Mức ưu tiên: thấp, trung bình hoặc cao.",
                },
            },
            "required": ["customer_name", "issue_description"],
            "additionalProperties": False,
        },
    },
]

TOOL_MAP = {
    "search_product_catalog": search_product_catalog,
    "submit_support_ticket": submit_support_ticket,
}
