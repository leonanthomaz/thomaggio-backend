from fastapi import HTTPException
from typing import Optional, Any


class AppHttpException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        solution: Optional[str] = None,
        errors: Optional[Any] = None,
    ):
        content = {
            "detail": detail,
        }
        if solution:
            content["solution"] = solution
        if errors:
            content["errors"] = errors

        super().__init__(status_code=status_code, detail=detail)
        self.status_code = status_code
        self.detail = detail
        self.solution = solution
        self.errors = errors
        self.content = content
