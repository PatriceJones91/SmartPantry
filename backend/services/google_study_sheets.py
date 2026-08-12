<<<<<<< HEAD
"""Private Google Sheets reader for Smart Pantry study evidence.

This module is used only by the admin research dashboard. It reads the first
worksheet in each configured Google Form response spreadsheet using a Google
service account. The service account JSON stays in the backend environment and
is never returned to the browser.
"""
=======
>>>>>>> e45c667 (Finalize admin study evidence dashboard)
from __future__ import annotations

import json
import os
import re
from statistics import mean
from typing import Any

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

DEFAULT_SHEETS = {
    "consent": "1XIgid0NU73_zQyZN8iA3JryeVAzLcP5Eyafp5KLuYYU",
    "pre": "1PIu5qXpy-QTHkgSXJyrLCDTzQtMZj7-lbqtydWOw5IQ",
    "task1": "1cvW-stEH8oVjF5B44vG6J1YDt4LHZKyxLndiHeENIKg",
    "task2": "1H1YmqcnrQbUlvM5mJC_IeKDLXhvJ0AK4AfnbXamMWpo",
    "task3": "1ZzGYSUbzVjO3P9RiHUBoDtVtAsCSBXHJ6SLpwVq1w6Q",
    "post": "1oyd1trPWn1_JnCLnM48MpPediEaYSfdxfhNZPfDCCOM",
}


def _sheet_id(key: str) -> str:
    return os.getenv(f"STUDY_SHEET_{key.upper()}_ID", DEFAULT_SHEETS[key]).strip()


def _credentials() -> service_account.Credentials:
    raw = os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        raise RuntimeError(
            "Google Sheets is not configured. Add GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON "
            "to the backend environment and share each study response sheet with the service account email."
        )
    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON is not valid JSON.") from exc
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def _first_worksheet_values(session: AuthorizedSession, spreadsheet_id: str) -> list[list[str]]:
    meta_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?fields=sheets.properties.title"
    meta = session.get(meta_url, timeout=20)
    if meta.status_code >= 400:
        raise RuntimeError(f"Could not read Google Sheet {spreadsheet_id}: HTTP {meta.status_code}")
    sheets = meta.json().get("sheets") or []
    if not sheets:
        return []
    title = sheets[0]["properties"]["title"]
    values_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{title}"
    response = session.get(values_url, timeout=20)
    if response.status_code >= 400:
        raise RuntimeError(f"Could not read Google Sheet values for {spreadsheet_id}: HTTP {response.status_code}")
    return response.json().get("values") or []


def _clean_header(value: Any) -> str:
<<<<<<< HEAD
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text
=======
    return re.sub(r"\s+", " ", str(value or "")).strip()
>>>>>>> e45c667 (Finalize admin study evidence dashboard)


def _rows(values: list[list[str]]) -> list[dict[str, Any]]:
    if not values:
        return []
    headers = [_clean_header(item) for item in values[0]]
    result: list[dict[str, Any]] = []
    for raw_row in values[1:]:
        row = {headers[i]: (raw_row[i] if i < len(raw_row) else "") for i in range(len(headers))}
        if any(str(value).strip() for value in row.values()):
            result.append(row)
    return result


def _participant(row: dict[str, Any]) -> str:
    for key, value in row.items():
        normalized = key.lower()
        if "participant id" in normalized or "participant username" in normalized:
            if str(value).strip():
                return str(value).strip()
    return ""


<<<<<<< HEAD
=======
def _participant_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


>>>>>>> e45c667 (Finalize admin study evidence dashboard)
def _timestamp(row: dict[str, Any]) -> str:
    for key, value in row.items():
        if key.lower() == "timestamp":
            return str(value or "").strip()
    return ""


def _number(value: Any) -> float | None:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if 1 <= number <= 10 else None


def _question_map(row: dict[str, Any]) -> dict[int, Any]:
    questions: dict[int, Any] = {}
    for header, value in row.items():
        match = re.match(r"^\s*(\d+)\.\s*", header)
        if match:
            questions[int(match.group(1))] = value
    return questions


def _avg(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return round(mean(clean), 2) if clean else None


def _tam_record(row: dict[str, Any], task: str) -> dict[str, Any]:
    q = _question_map(row)
    if task == "task1":
        ease = [_number(q.get(1)), _number(q.get(2))]
        usefulness = [_number(q.get(i)) for i in (3, 4, 5, 6, 7)]
        awareness = [_number(q.get(3)), _number(q.get(4))]
        utilization = [_number(q.get(6))]
        intention = [_number(q.get(8))]
    elif task == "task2":
        ease = [_number(q.get(1)), _number(q.get(2))]
        usefulness = [_number(q.get(i)) for i in (3, 5, 6, 7)]
        awareness = [_number(q.get(4))]
        utilization = [_number(q.get(6))]
        intention = [_number(q.get(8))]
<<<<<<< HEAD
    else:  # task3
=======
    else:
>>>>>>> e45c667 (Finalize admin study evidence dashboard)
        ease = [_number(q.get(1)), _number(q.get(2))]
        usefulness = [_number(q.get(i)) for i in (3, 4, 5, 6, 7)]
        awareness = [_number(q.get(3)), _number(q.get(4))]
        utilization = [_number(q.get(4)), _number(q.get(6))]
        intention = [_number(q.get(8))]

    return {
        "participant": _participant(row),
        "timestamp": _timestamp(row),
        "ease_of_use": _avg(ease),
        "perceived_usefulness": _avg(usefulness),
        "behavioral_intention": _avg(intention),
        "pantry_awareness": _avg(awareness),
        "ingredient_utilization": _avg(utilization),
        "ratings": {str(i): _number(q.get(i)) for i in range(1, 9)},
        "worked_well": str(q.get(9, "") or ""),
        "confusing_or_missing": str(q.get(10, "") or ""),
        "make_more_useful": str(q.get(11, "") or ""),
    }


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "responses": len(records),
        "ease_of_use": _avg([item.get("ease_of_use") for item in records]),
        "perceived_usefulness": _avg([item.get("perceived_usefulness") for item in records]),
        "behavioral_intention": _avg([item.get("behavioral_intention") for item in records]),
        "pantry_awareness": _avg([item.get("pantry_awareness") for item in records]),
        "ingredient_utilization": _avg([item.get("ingredient_utilization") for item in records]),
    }


<<<<<<< HEAD
def _basic_survey_rows(rows: list[dict[str, Any]], include_open_text: bool = True) -> list[dict[str, Any]]:
=======
def _basic_survey_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
>>>>>>> e45c667 (Finalize admin study evidence dashboard)
    output = []
    for row in rows:
        q = _question_map(row)
        numeric = {str(i): _number(value) for i, value in q.items() if _number(value) is not None}
<<<<<<< HEAD
        text = {str(i): str(value or "") for i, value in q.items() if _number(value) is None and str(value or "").strip()}
        item = {"participant": _participant(row), "timestamp": _timestamp(row), "ratings": numeric}
        if include_open_text:
            item["text"] = text
        output.append(item)
    return output


def load_study_evidence() -> dict[str, Any]:
    credentials = _credentials()
    session = AuthorizedSession(credentials)

    raw: dict[str, list[dict[str, Any]]] = {}
    for key in DEFAULT_SHEETS:
        raw[key] = _rows(_first_worksheet_values(session, _sheet_id(key)))
=======
        text = {
            str(i): str(value or "")
            for i, value in q.items()
            if _number(value) is None and str(value or "").strip()
        }
        output.append({
            "participant": _participant(row),
            "timestamp": _timestamp(row),
            "ratings": numeric,
            "text": text,
        })
    return output


def _matched_awareness(pre_rows: list[dict[str, Any]], post_rows: list[dict[str, Any]]) -> dict[str, Any]:
    pre_map: dict[str, float] = {}
    post_map: dict[str, float] = {}

    for row in pre_rows:
        q = _question_map(row)
        score = _avg([_number(q.get(1)), _number(q.get(2))])
        key = _participant_key(_participant(row))
        if key and score is not None:
            pre_map[key] = score

    for row in post_rows:
        q = _question_map(row)
        score = _avg([_number(q.get(6)), _number(q.get(7))])
        key = _participant_key(_participant(row))
        if key and score is not None:
            post_map[key] = score

    matched = sorted(set(pre_map) & set(post_map))
    pre_average = _avg([pre_map[key] for key in matched])
    post_average = _avg([post_map[key] for key in matched])
    change = None
    if pre_average is not None and post_average is not None:
        change = round(post_average - pre_average, 2)

    return {
        "matched_participants": len(matched),
        "pre_average": pre_average,
        "post_average": post_average,
        "change": change,
    }


def load_study_evidence() -> dict[str, Any]:
    session = AuthorizedSession(_credentials())
    raw = {
        key: _rows(_first_worksheet_values(session, _sheet_id(key)))
        for key in DEFAULT_SHEETS
    }
>>>>>>> e45c667 (Finalize admin study evidence dashboard)

    task1 = [_tam_record(row, "task1") for row in raw["task1"]]
    task2 = [_tam_record(row, "task2") for row in raw["task2"]]
    task3 = [_tam_record(row, "task3") for row in raw["task3"]]

    consent = []
    for row in raw["consent"]:
<<<<<<< HEAD
        agreed = ""
        for header, value in row.items():
            if "agree to participate" in header.lower():
                agreed = str(value or "")
                break
=======
        agreed = next(
            (str(value or "") for header, value in row.items() if "agree to participate" in header.lower()),
            "",
        )
>>>>>>> e45c667 (Finalize admin study evidence dashboard)
        consent.append({
            "participant": _participant(row),
            "timestamp": _timestamp(row),
            "consented": agreed.lower().startswith("yes"),
        })

<<<<<<< HEAD
=======
    tam_summary = {
        "task1": _summary(task1),
        "task2": _summary(task2),
        "task3": _summary(task3),
    }

>>>>>>> e45c667 (Finalize admin study evidence dashboard)
    return {
        "status": "ok",
        "sources": {
            "consent": len(raw["consent"]),
            "pre": len(raw["pre"]),
            "task1": len(task1),
            "task2": len(task2),
            "task3": len(task3),
            "post": len(raw["post"]),
        },
        "consent": consent,
        "pre": _basic_survey_rows(raw["pre"]),
        "task1": task1,
        "task2": task2,
        "task3": task3,
        "post": _basic_survey_rows(raw["post"]),
<<<<<<< HEAD
        "tam_summary": {
            "task1": _summary(task1),
            "task2": _summary(task2),
            "task3": _summary(task3),
        },
        "notes": [
            "TAM scores use 1-10 survey ratings.",
            "Task 2 usefulness uses questions 3, 5, 6, and 7; question 4 is shown separately as pantry-awareness evidence.",
            "The current Post-Study response sheet contains duplicate wording for questions 13 and 14; the dashboard keeps the source data unchanged.",
=======
        "tam_summary": tam_summary,
        "pre_post_awareness": _matched_awareness(raw["pre"], raw["post"]),
        "notes": [
            "Scores are descriptive while the participant study is in progress.",
            "Post-Study questions 13 and 14 currently have duplicate wording in the source form.",
>>>>>>> e45c667 (Finalize admin study evidence dashboard)
        ],
    }
