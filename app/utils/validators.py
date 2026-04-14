import re
from typing import Any


class ValidationError(ValueError):
    pass


def validate_non_empty(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValidationError(f'Поле "{field_name}" не должно быть пустым.')
    return value


def validate_slug(value: str) -> str:
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{1,62}', value):
        raise ValidationError('Slug должен содержать только латиницу, цифры, дефис и подчёркивание.')
    return value


def validate_positive_int(value: str, field_name: str) -> int:
    if not value.isdigit() or int(value) <= 0:
        raise ValidationError(f'Поле "{field_name}" должно быть положительным числом.')
    return int(value)


def validate_price(value: str) -> str:
    normalized = value.replace(',', '.').strip()
    if not re.fullmatch(r'\d+(\.\d{1,2})?', normalized):
        raise ValidationError('Цена должна быть числом, например 199 или 199.99.')
    return normalized


def validate_dynamic_field(field_schema: dict[str, Any], value: str) -> Any:
    field_type = field_schema.get('type', 'text')
    required = field_schema.get('required', False)
    if required and not value.strip():
        raise ValidationError(f'Поле "{field_schema.get("label", "value")}" обязательно для заполнения.')
    if field_type == 'number':
        return validate_positive_int(value, field_schema.get('label', 'value'))
    if field_type == 'email':
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', value.strip()):
            raise ValidationError('Введите корректный email.')
        return value.strip()
    if field_type == 'text':
        return value.strip()
    return value.strip()
