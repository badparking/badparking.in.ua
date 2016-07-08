from rest_framework_jwt.utils import jwt_payload_handler as default_jwt_payload_handler


def extended_jwt_payload_handler(user):
    """
    Extends default JWT payload with user profile completion state and full name.
    """
    payload = default_jwt_payload_handler(user)
    payload['is_complete'] = user.is_complete()
    payload['full_name'] = user.get_full_name()
    return payload


def jwt_from_user(user):
    from rest_framework_jwt.settings import api_settings
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

    payload = jwt_payload_handler(user)
    return jwt_encode_handler(payload)
