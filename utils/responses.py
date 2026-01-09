from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

def list_response(data):
    return {"success": True, "message": "records displayed", "data": data}

# def list_response(**kwargs):
#     return {**kwargs}


def create_response(data):
    return {"success": True, "message": "record created", "data": data}


def update_response(data):
    return {"success": True, "message": "record updated", "data": data}


def delete_response(data):
    return {"success": True, "message": "record deleted", "data": data}


def serializer_errors_response(err):
    return {"success": False, "message": err, "data": {}}


def other_errors_response(err):
    return {"success": False, "message": err, "data": {}}


def id_require_for_delete():
    return {"success": False, "message": "Id is required for deleting record", "data": {}}


# Auth Response functions
def login_success(data):
    return {"success": True, "message": "Login success", "data": data}


class HTTPCODE:
    OK = status.HTTP_200_OK
    CREATED = status.HTTP_201_CREATED
    NO_CONTENT = status.HTTP_204_NO_CONTENT
    BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
    FORBIDDEN = status.HTTP_403_FORBIDDEN
    NOT_FOUND = status.HTTP_404_NOT_FOUND
    METHOD_NOT_ALLOWED = status.HTTP_405_METHOD_NOT_ALLOWED
    SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR


# JWT Token generator
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }