from typing import Any
import logging
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework import status

from config.exceptions import DomainException

logger = logging.getLogger("cardio-trace-backend-api")


def custom_exception_handler(
    exc: Exception, context: dict[str, Any]
) -> Response | None:
    if isinstance(exc, DomainException):
        logger.log(
            exc.log_level,
            exc.message,
            extra={
                "error_code": exc.code,
                "exception": exc.__class__.__name__,
                "view": context.get("view").__class__.__name__,
                **exc.extra,
            },
            exc_info=exc.log_level >= logging.ERROR,
        )

        return Response(
            {"error": {"code": exc.code, "message": exc.message}},
            status=exc.status_code,
        )

    response = exception_handler(exc, context)
    if response is not None:
        return response

    logger.exception(
        "Unhandled exception",
        extra={
            "exception": exc.__class__.__name__,
            "view": context.get("view").__class__.__name__,
        },
    )

    return Response(
        {
            "error": {
                "code": "internal_server_error",
                "message": "Unexpected server error",
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
