"""Domain exceptions shared by all modules.

Services raise these; a single handler in main.py maps them to HTTP
responses so service code stays framework-independent and unit-testable.
"""


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class PermissionDeniedError(AppError):
    status_code = 403


class AuthError(AppError):
    status_code = 401


class ValidationFailed(AppError):
    status_code = 422
