from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from apps.common.enums import ValidationStatus


@dataclass
class ValidationResult:
    status: ValidationStatus = ValidationStatus.PASSED
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    def add_error(self, field_name: str, code: str, message: str) -> None:
        self.errors.append({"field": field_name, "code": code, "message": message})
        self.status = ValidationStatus.FAILED

    def add_warning(self, field_name: str, code: str, message: str) -> None:
        self.warnings.append({"field": field_name, "code": code, "message": message})
        if self.status == ValidationStatus.PASSED:
            self.status = ValidationStatus.WARNING

    @property
    def passed(self) -> bool:
        return self.status == ValidationStatus.PASSED

    @property
    def all_issues(self) -> List[Dict[str, Any]]:
        return self.errors + self.warnings


@dataclass
class ValidationRule:
    name: str
    check: Callable[[Dict[str, Any]], Optional[str]]
    field: str
    severity: ValidationStatus
    code: str


class ValidationEngine:
    def __init__(self):
        self._rules: List[ValidationRule] = []

    def register(self, rule: ValidationRule) -> None:
        self._rules.append(rule)

    def run(self, record: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        for rule in self._rules:
            message = rule.check(record)
            if message:
                if rule.severity == ValidationStatus.FAILED:
                    result.add_error(rule.field, rule.code, message)
                else:
                    result.add_warning(rule.field, rule.code, message)
        return result
