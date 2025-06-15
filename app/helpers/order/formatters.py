from datetime import datetime
from babel.numbers import format_currency as babel_format_currency
from babel.dates import format_datetime as babel_format_datetime

def format_currency(value: float, locale_str: str = 'pt_BR') -> str:
    return babel_format_currency(value, 'BRL', locale=locale_str)

def format_brazilian_date(date: datetime, locale_str: str = 'pt_BR') -> str:
    return babel_format_datetime(date, "dd/MM/yyyy HH:mm", locale=locale_str)
