from django.core.files.base import ContentFile
from django.urls import reverse
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer,
)
from rest_framework import serializers
from urllib.parse import urljoin
import base64
import uuid

from foodgram.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShortLink,
    User,
)


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class UserSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ('avatar', 'is_subscribed')

    def get_is_subscribed(self, obj: User):
        user = None
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
        if isinstance(user, User):
            return user.subscriptions.filter(subscribed_to=obj).exists()
        return False


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=str(uuid.uuid4()) + '.' + ext,
            )

        return super().to_internal_value(data)


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField()

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
    )
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault(),
    )
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(allow_empty=False, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('created_at',)

    def get_is_favorited(self, obj: Recipe):
        user = None
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
        if isinstance(user, User):
            return user.favorites.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj: Recipe):
        user = None
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
        if isinstance(user, User):
            return user.user_carts.filter(recipe=obj).exists()
        return False

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        instance = Recipe.objects.create(**validated_data)
        self.update_or_create(instance, ingredients_data)
        return instance

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        instance.ingredients.all().delete()
        self.update_or_create(instance, ingredients_data)
        return instance

    def update_or_create(self, instance, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(recipe=instance, **i) for i in ingredients_data])

    def validate_ingredients(self, value):
        seen = set()

        # Замечание к замечанию ревьюера: это не list comprehension, а
        # generator expression, что эквивалентно обычному for

        # if any(x['ingredient'].id in seen or seen.add(x['ingredient'].id)
        #        for x in value):
        #     raise serializers.ValidationError(
        #         'This list may not contain duplicate items.')

        for ingredient_data in value:
            id = ingredient_data['ingredient'].id
            if id in seen:
                raise serializers.ValidationError(
                    'This list may not contain duplicate items.')
            else:
                seen.add(id)
        return value


class PartialUpdateRecipeSerializer(RecipeSerializer):
    image = Base64ImageField(required=False)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserWithRecipesSerializer(UserSerializer):
    recipes_limit: int | None = None

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def __init__(self, *args, **kwargs):
        self.recipes_limit = kwargs.pop('recipes_limit', None)
        super().__init__(*args, **kwargs)

    def get_recipes(self, obj: User):
        recipes = obj.recipes.all().order_by('id')[:self.recipes_limit]
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj: User):
        return obj.recipes.count()


class ShortLinkSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = ShortLink
        fields = ('short_link',)

    @property
    def data(self):
        data = super().data
        data['short-link'] = data.pop('short_link')
        return data

    def get_short_link(self, obj: ShortLink):
        request = self.context['request']
        short_link = obj[0].short_link
        reversed_link = reverse('short-link-redirect', args=(short_link,))
        base_uri = request.build_absolute_uri('/')
        destination = urljoin(base_uri, reversed_link)
        return destination


class UserSubscribeQuerySerializer(serializers.Serializer):
    recipes_limit = serializers.IntegerField(required=False, min_value=0)


class UserSubscriptionsQuerySerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=0)
    recipes_limit = serializers.IntegerField(required=False, min_value=0)


class RecipesQuerySerializer(serializers.Serializer):
    is_favorited = serializers.BooleanField(
        required=False,
        allow_null=True
    )
    is_in_shopping_cart = serializers.BooleanField(
        required=False,
        allow_null=True
    )
    author = serializers.IntegerField(required=False)
