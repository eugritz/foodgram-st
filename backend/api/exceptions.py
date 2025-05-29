from rest_framework.exceptions import APIException


class AlreadySubscribed(APIException):
    status_code = 400
    default_detail = 'You are already subscribed to this user.'
    default_code = 'already_subscribed'


class NotSubscribed(APIException):
    status_code = 400
    default_detail = 'You are not subscribed to this user.'
    default_code = 'not_subscribed'
