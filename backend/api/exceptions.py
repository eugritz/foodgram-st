from rest_framework.exceptions import APIException


class AlreadySubscribed(APIException):
    status_code = 400
    default_detail = 'You are already subscribed to this user.'
    default_code = 'already_subscribed'


class NotSubscribed(APIException):
    status_code = 400
    default_detail = 'You are not subscribed to this user.'
    default_code = 'not_subscribed'


class SelfSubscribe(APIException):
    status_code = 400
    default_detail = 'You can\'t subscribe or unsubscribe from yourself.'
    default_code = 'self_subscribed'


class AlreadyFavorited(APIException):
    status_code = 400
    default_detail = 'You have already favorited this recipe.'
    default_code = 'already_favorited'


class NotFavorited(APIException):
    status_code = 400
    default_detail = 'You haven\'t favorited this recipe.'
    default_code = 'not_favorited'


class AlreadyInShoppingCart(APIException):
    status_code = 400
    default_detail = 'You have already added this recipe to your cart.'
    default_code = 'already_in_cart'


class NotInShoppingCart(APIException):
    status_code = 400
    default_detail = 'You haven\'t added this recipe to your cart.'
    default_code = 'not_in_cart'
