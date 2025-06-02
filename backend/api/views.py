from django.db import IntegrityError
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseRedirect
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
from rest_framework.views import APIView
from urllib.parse import urljoin

from foodgram.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    ShortLink,
    Subscription,
    User,
)

from . import shopping_cart_generator
from .exceptions import (
    AlreadyFavorited,
    AlreadyInShoppingCart,
    AlreadySubscribed,
    NotFavorited,
    NotInShoppingCart,
    NotSubscribed,
    SelfSubscribe,
)
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrReadOnly, IsCurrentUser
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    PartialUpdateRecipeSerializer,
    RecipeMinifiedSerializer,
    RecipeSerializer,
    RecipesQuerySerializer,
    ShortLinkSerializer,
    UserSubscribeQuerySerializer,
    UserSubscriptionsQuerySerializer,
    UserWithRecipesSerializer,
)


class UserViewSet(BaseUserViewSet):
    pagination_class = PageLimitPagination

    def get_permissions(self):
        # В настройках PERMISSIONS Djoser нет current_user
        if self.action == 'me':
            self.permission_classes = (CurrentUserOrAdmin,)
        return super().get_permissions()

    @action(['post', 'delete'],
            detail=True,
            permission_classes=[CurrentUserOrAdmin])
    def subscribe(self, request, id=None):
        subscribe_to = get_object_or_404(User, pk=id)
        if request.user == subscribe_to:
            raise SelfSubscribe()

        if request.method == 'POST':
            query_params_serializer = UserSubscribeQuerySerializer(
                data=request.query_params)
            query_params_serializer.is_valid(raise_exception=True)
            query_params = query_params_serializer.validated_data

            try:
                subscription = Subscription.objects.create(
                    user=request.user, subscribed_to=subscribe_to)

                serializer = UserWithRecipesSerializer(
                    subscription.subscribed_to,
                    recipes_limit=query_params.get('recipes_limit', None),
                )

                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            except IntegrityError:
                raise AlreadySubscribed()
        else:
            subscription = request.user.subscriptions.filter(
                subscribed_to=subscribe_to).first()
            if subscription:
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise NotSubscribed()


class CurrentUserViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @action(['put', 'delete'], detail=False)
    def avatar(self, request):
        if request.method == 'PUT':
            return self.set_avatar(request)
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
    serializer_class = UserWithRecipesSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        query_params_serializer = UserSubscriptionsQuerySerializer(
            data=self.request.query_params)
        query_params_serializer.is_valid(raise_exception=True)

        self.limit = query_params_serializer.validated_data.get('limit', None)
        self.recipes_limit = query_params_serializer.validated_data.get(
            'recipes_limit', None)

    def get_serializer(self, *args, **kwargs):
        kwargs['recipes_limit'] = self.recipes_limit
        serializer = super().get_serializer(*args, **kwargs)
        return serializer

    def get_queryset(self):
        subscriptions = self.request.user.subscriptions.select_related(
            'subscribed_to')[:self.limit]
        return [x.subscribed_to for x in subscriptions]


class NameSearchFilter(filters.SearchFilter):
    search_param = 'name'


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [NameSearchFilter]
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer  # см. get_serializer_class
    pagination_class = PageLimitPagination
    http_method_names = ['get', 'post', 'patch', 'delete', 'head']

    def partial_update(self, request, *args, **kwargs):
        # Отключим свойство partial. Вместо этого будем вручную подбирать,
        # какие поля должны быть необязательными
        # kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return PartialUpdateRecipeSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        query = super().get_queryset()

        #
        # NOTE: DjangoFilterBackend не работает с вычисляемыми полями, поэтому
        # фильтрацию надо делать вручную
        #

        query_params_serializer = RecipesQuerySerializer(
            data=self.request.query_params)
        query_params_serializer.is_valid(raise_exception=True)
        query_params = query_params_serializer.validated_data

        is_favorited = query_params.get('is_favorited', None)
        if is_favorited:
            if self.request.user.is_authenticated:
                query = query.filter(favorited__user=self.request.user)
            else:
                return []
        # is_favorited может быть None
        elif is_favorited == False:  # noqa: E712
            if self.request.user.is_authenticated:
                query = query.filter(~Q(favorited__user=self.request.user))

        is_in_shopping_cart = query_params.get('is_in_shopping_cart', None)
        if is_in_shopping_cart:
            if self.request.user.is_authenticated:
                query = query.filter(recipe_carts__user=self.request.user)
            else:
                return []
        # is_in_shopping_cart может быть None
        elif is_in_shopping_cart == False:  # noqa: E712
            if self.request.user.is_authenticated:
                query = query.filter(~Q(recipe_carts__user=self.request.user))

        author = query_params.get('author', None)
        if author is not None:
            query = query.filter(author__pk=author)

        return query

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            self.permission_classes = (IsAuthorOrReadOnly,)
        else:
            self.permission_classes = (IsAuthenticatedOrReadOnly,)
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            try:
                favorite = Favorite.objects.create(user=request.user,
                                                   recipe=recipe)
                return Response(RecipeMinifiedSerializer(favorite.recipe).data,
                                status=status.HTTP_201_CREATED)
            except IntegrityError:
                raise AlreadyFavorited()

        # DELETE
        favorite = request.user.favorites.filter(recipe=recipe).first()
        if favorite:
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise NotFavorited()

    @action(['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            try:
                cart = ShoppingCart.objects.create(user=request.user,
                                                   recipe=recipe)
                return Response(RecipeMinifiedSerializer(cart.recipe).data,
                                status=status.HTTP_201_CREATED)
            except IntegrityError:
                raise AlreadyInShoppingCart()

        # DELETE
        cart = request.user.user_carts.filter(recipe=recipe).first()
        if cart:
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise NotInShoppingCart()

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        cart = (
            request.user.user_carts.filter()
            .select_related('recipe')
            .prefetch_related('recipe__ingredients__ingredient')
            # Не работает как хотелось бы
            # .prefetch_related(Prefetch(
            #     'recipe__ingredients__ingredient',
            #     queryset=Ingredient.objects.order_by(Lower('name')),
            # ))
            .order_by(Lower('recipe__name'))
        )

        recipes = [shopping_cart_generator.Recipe(x.recipe) for x in cart]
        gen = shopping_cart_generator.ShoppingCartGenerator(recipes)
        return HttpResponse(
            str(gen),
            content_type='text/plain',
            headers={
                'Content-Disposition': 'attachment;'
                'filename="shopping_cart.txt"',
            },
        )

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        get_object_or_404(Recipe, pk=pk)
        short_link = ShortLink.objects.update_or_create(
            destination=f'/recipes/{pk}')
        context = self.get_serializer_context()
        return Response(ShortLinkSerializer(short_link, context=context).data)


class ShortLinkRedirect(APIView):
    def get(self, request, id=None):
        short_link = get_object_or_404(ShortLink, pk=id)
        base_uri = request.build_absolute_uri('/')
        destination = urljoin(base_uri, short_link.destination)
        return HttpResponseRedirect(redirect_to=destination)
