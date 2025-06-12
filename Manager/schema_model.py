# Manager/schema_model.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class FieldRule:
    allowed_values: Optional[List[str]] = field(default_factory=list)
    regex: Optional[str] = None
    type: Optional[str] = None


@dataclass
class ColumnMetadata:
    required: bool
    type: str


@dataclass
class ValidationSchema:
    required_fields: List[str]
    unique_fields: List[str]
    field_rules: Dict[str, FieldRule]
    column_mapping: Dict[str, ColumnMetadata]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            required_fields=data.get("required_fields", []),
            unique_fields=data.get("unique_fields", []),
            field_rules={k: FieldRule(**v) for k, v in data.get("field_rules", {}).items()},
            column_mapping={k: ColumnMetadata(**v) for k, v in data.get("column_mapping", {}).items()}
        )

    def to_dict(self):
        return {
            "required_fields": self.required_fields,
            "unique_fields": self.unique_fields,
            "field_rules": {k: vars(v) for k, v in self.field_rules.items()},
            "column_mapping": {k: vars(v) for k, v in self.column_mapping.items()}
        }

@dataclass
class ValidationSchema:
    required_fields: List[str]
    unique_fields: List[str]
    field_rules: Dict[str, FieldRule]
    column_mapping: Dict[str, ColumnMetadata]
    rules_enabled: Dict[str, bool] = field(default_factory=dict)  # ✅ Add this

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            required_fields=data.get("required_fields", []),
            unique_fields=data.get("unique_fields", []),
            field_rules={k: FieldRule(**v) for k, v in data.get("field_rules", {}).items()},
            column_mapping={k: ColumnMetadata(**v) for k, v in data.get("column_mapping", {}).items()},
            rules_enabled=data.get("rules_enabled", {})  # ✅ Include this
        )

    def to_dict(self):
        return {
            "required_fields": self.required_fields,
            "unique_fields": self.unique_fields,
            "field_rules": {k: vars(v) for k, v in self.field_rules.items()},
            "column_mapping": {k: vars(v) for k, v in self.column_mapping.items()},
            "rules_enabled": self.rules_enabled  # ✅ Add this too
        }
