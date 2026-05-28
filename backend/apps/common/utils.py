import hashlib
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
from zoneinfo import ZoneInfo

from django.utils import timezone


def generate_file_hash(file_obj) -> str:
    sha256 = hashlib.sha256()
    for chunk in file_obj.chunks():
        sha256.update(chunk)
    file_obj.seek(0)
    return sha256.hexdigest()


def safe_decimal(value: Any, default: Optional[Decimal] = None) -> Optional[Decimal]:
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return default


def safe_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, (date, datetime)):
        return value.date() if isinstance(value, datetime) else value

    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
        "%d.%m.%Y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y",
        "%b %d, %Y", "%B %d, %Y",
    ]
    cleaned = str(value).strip()
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def normalize_column_name(name: str) -> str:
    if not name:
        return ""
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = name.strip("_")
    return name


def slugify_org_name(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:50]


def truncate_string(value: str, max_length: int, suffix: str = "...") -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - len(suffix)] + suffix


def current_utc() -> datetime:
    return timezone.now()


def to_utc(dt: datetime, tz_name: str = "UTC") -> datetime:
    tz = ZoneInfo(tz_name)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(ZoneInfo("UTC"))
