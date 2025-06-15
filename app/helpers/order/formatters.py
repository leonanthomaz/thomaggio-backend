import locale
from datetime import datetime

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def format_currency(value: float) -> str:
    return locale.currency(value, grouping=True)

def format_brazilian_date(date: datetime, fmt: str = "%d/%m/%Y %H:%M") -> str:
    return date.strftime(fmt)
