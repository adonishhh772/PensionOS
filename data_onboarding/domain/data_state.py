from enum import Enum


class DataState(str, Enum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONFLICTING = "CONFLICTING"
    DERIVED = "DERIVED"
    CONFIRMED_NULL = "CONFIRMED_NULL"
    PENDING_REVIEW = "PENDING_REVIEW"

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]
