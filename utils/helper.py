"""Shared helper functions for validation, dates, and search filters."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_

from models.visitor import Visitor


def sanitize_text(value: str | None, fallback: str = "") -> str:
    """Trim user input and collapse missing values to a safe fallback."""
    return (value or fallback).strip()


def required_fields_present(data: dict, fields: list[str]) -> tuple[bool, str]:
    """Validate required form fields and return a readable error."""
    for field in fields:
        if not sanitize_text(data.get(field)):
            return False, f"{field.replace('_', ' ').title()} is required."
    return True, ""


def date_range_for_filter(history_filter: str) -> tuple[datetime, datetime]:
    """Return UTC date boundaries for manager history filters."""
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    if history_filter == "yesterday":
        start = today_start - timedelta(days=1)
        end = today_start
    elif history_filter == "weekly":
        start = today_start - timedelta(days=7)
        end = now + timedelta(seconds=1)
    elif history_filter == "monthly":
        start = today_start - timedelta(days=30)
        end = now + timedelta(seconds=1)
    else:
        start = today_start
        end = now + timedelta(seconds=1)
    return start, end


def apply_visitor_search(query, search_text: str):
    """Apply manager search across visitor name, company, purpose, and date."""
    term = sanitize_text(search_text)
    if not term:
        return query

    like_term = f"%{term}%"
    filters = [
        Visitor.name.ilike(like_term),
        Visitor.company.ilike(like_term),
        Visitor.purpose.ilike(like_term),
        Visitor.person_to_meet.ilike(like_term),
    ]

    parsed_date = _parse_search_date(term)
    if parsed_date:
        start = datetime(parsed_date.year, parsed_date.month, parsed_date.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        filters.append(Visitor.arrival_time.between(start, end))

    return query.filter(or_(*filters))


def _parse_search_date(value: str) -> datetime | None:
    """Parse common date search formats used on the manager dashboard."""
    for date_format in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y"):
        try:
            return datetime.strptime(value, date_format).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None
