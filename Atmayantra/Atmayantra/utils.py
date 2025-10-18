from rest_framework.response import Response
from django.http import FileResponse
from rest_framework import status

def api_response(success=True, message="", data=None, status_code=None, file=None):
    """
    A universal API response helper.

    Args:
        success (bool): True for success, False for error.
        message (str): A readable message about the result.
        data (dict, optional): The JSON payload. Defaults to None.
        status_code (int, optional): The HTTP status code. Auto-determined if not provided.
        file (file object, optional): A file object to be returned as a FileResponse.

    Returns:
        Response or FileResponse: A Django REST Framework Response or a Django FileResponse.
    """
    if file:
        # When returning a file, we use FileResponse.
        # The browser will handle it as a download or display it if possible.
        return FileResponse(file)

    # For JSON responses, we build a consistent structure.
    response_data = {
        "status": "success" if success else "error",
        "message": message,
    }
    if data is not None:
        response_data["data"] = data

    # Auto-determine status code if not provided.
    if status_code is None:
        if success:
            status_code = status.HTTP_200_OK
        else:
            # Default to 400 for client errors.
            status_code = status.HTTP_400_BAD_REQUEST

    return Response(response_data, status=status_code)
