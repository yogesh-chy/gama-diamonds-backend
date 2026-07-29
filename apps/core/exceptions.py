import logging
import traceback

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):

    response = exception_handler(exc, context)

    if response is not None:
        details = response.data
        message = "Request failed."

        if isinstance(details, dict) and "detail" in details:
            message = str(details.pop("detail"))
            details = details or None

        response.data = {
            "error": {
                "code": response.status_code,
                "message": message,
                "details": details,
            }
        }
        return response

    # Log the full traceback so unhandled errors (SMTP, DB, etc.) are visible
    logger.error(
        "Unhandled exception in %s: %s\n%s",
        context.get("view", "unknown view"),
        exc,
        traceback.format_exc(),
    )

    return Response(
        {
            "error": {
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error.",
                "details": None,
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
