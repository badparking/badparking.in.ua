from rest_framework_jwt.utils import jwt_payload_handler


def extended_jwt_payload_handler(user):
    """
    Extends default JWT payload with user profile completion state and full name.
    """
    payload = jwt_payload_handler(user)
    payload['is_complete'] = user.is_complete()
    payload['full_name'] = user.get_full_name()
    return payload
