from fastapi import HTTPException, status


class UnauthorizedException(HTTPException):
    """Exception for unauthorized access."""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
