from enum import Enum

class CompanyStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    MAINTENANCE = "maintenance"