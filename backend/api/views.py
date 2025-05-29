from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from djoser.permissions import CurrentUserOrAdmin
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from foodgram.models import Ingredient, Recipe, Subscription, User

from .exceptions import AlreadySubscribed, NotSubscribed
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrReadOnly, IsCurrentUser
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeSerializer,
    UserSerializer,
)


class UserViewSet(BaseUserViewSet):
    pagination_class = PageLimitPagination
    
    @action(['post', 'delete'],
            detail=True,
            permission_classes=[CurrentUserOrAdmin])
    def subscribe(self, request, id=None):
        subscribe_to = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            subscription = Subscription(user=request.user,
                                        subscribed_to=subscribe_to)
            try:
                subscription.save()
            except IntegrityError:
                raise AlreadySubscribed()
            return Response(UserSerializer(subscription.subscribed_to).data)
        else:
            subscription = Subscription.objects.filter(
                user=request.user, subscribed_to=subscribe_to).first()
            if subscription:
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise NotSubscribed()


class CurrentUserViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

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


class SubscriptionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    pagination_class = PageLimitPagination
    permission_classes = (IsCurrentUser,)
    serializer_class = UserSerializer

    def get_queryset(self):
        return [x.subscribed_to for x in
                self.request.user.subscriptions.select_related('subscribed_to')]


class NameSearchFilter(filters.SearchFilter):
    search_param = 'name'


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [NameSearchFilter]
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageLimitPagination

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            self.permission_classes = (IsAuthorOrReadOnly,)
        else:
            self.permission_classes = (IsAuthenticatedOrReadOnly,)
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
