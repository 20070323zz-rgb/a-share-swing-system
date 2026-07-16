"""Minimal BaoStock subprocess helper; emits one sanitized JSON document."""

from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import sys
import time

import baostock as bs


def main() -> int:
    request = json.load(sys.stdin)
    rows: list[list[str]] = []
    request_count = 0
    captured = io.StringIO()
    login_error = ""
    with redirect_stdout(captured):
        login = bs.login()
        if str(login.error_code) != "0":
            login_error = f"BaoStock login failed: {login.error_code} {login.error_msg}"
        else:
            try:
                for code in request["codes"]:
                    result = bs.query_history_k_data_plus(
                        code,
                        request["fields"],
                        start_date=request["trade_date"],
                        end_date=request["trade_date"],
                        frequency="d",
                        adjustflag=request["adjustflag"],
                    )
                    request_count += 1
                    if str(result.error_code) == "0":
                        while result.next():
                            rows.append(result.get_row_data())
                    time.sleep(float(request["request_interval_seconds"]))
            finally:
                bs.logout()
    if login_error:
        sys.stdout.write(json.dumps({"rows": [], "request_count": 0, "status": "NETWORK_FAILED", "error": login_error}))
        return 0
    payload = {
        "rows": rows,
        "request_count": request_count,
        "status": "ACCESS_PASS" if rows else "EMPTY_UNEXPECTED",
        "error": "",
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
