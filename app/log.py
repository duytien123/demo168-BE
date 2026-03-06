import json
import logging
import traceback
from datetime import datetime, timezone, timedelta

from typing import Any, Dict

from starlette_context import context


def value_serializer(v):
    return str(v)


class Formatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        jst = timezone(timedelta(hours=9))
        message_dict: Dict[str, Any] = {
            "level": record.levelname,
            "timestamp": datetime.fromtimestamp(record.created, tz=jst).strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            ),
        }

        if context.exists():
            message_dict["context"] = {
                "request_id": context.get("request_id"),
                "tenant_id": context.get("tenant_id"),
                "user_id": context.get("user_id"),
            }

        if isinstance(record.msg, dict):
            message_dict["msg"] = record.msg
        else:
            message_dict["msg"] = record.getMessage()

        if record.exc_info:
            message_dict["exc_info"] = traceback.format_exception(*record.exc_info)

        return json.dumps(message_dict, default=value_serializer, ensure_ascii=False, indent=1) + '\n'


logger = logging.getLogger("uvicorn")
formatter = Formatter()

for h in logger.handlers:
    h.setFormatter(formatter)
