from djoser.permissions import CurrentUserOrAdmin
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .pagination import PageLimitPagination
from .serializers import AvatarSerializer


class UserViewSet(BaseUserViewSet):
    pagination_class = PageLimitPagination


class CurrentUserViewSet(viewsets.ViewSet):
    permission_classes = (CurrentUserOrAdmin,)

    @action(['put', 'delete'], detail=False)
    def avatar(self, request):
        if request.method == 'PUT':
            return self.set_avatar(request)
        else:
            return self.delete_avatar(request)

    def set_avatar(self, request):
        serializer = AvatarSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_avatar(self, request):
        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
