from djoser.views import UserViewSet as BaseUserViewSet

from .pagination import PageLimitPagination


class UserViewSet(BaseUserViewSet):
    pagination_class = PageLimitPagination
