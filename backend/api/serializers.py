from django.core.files.base import ContentFile
from django.urls import reverse
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer,
)
from rest_framework import serializers
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
            'first_name': { 'required': True },
            'last_name': { 'required': True },
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
        fields = '__all__'


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
        fields = '__all__'
        read_only_fields = ('created_at',)

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
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **ingredient_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        new_ingredients_dict = {x['ingredient'].id: x for x in ingredients_data}
        old_ingredients_dict = {x.ingredient.id: x
                                for x in instance.ingredients.all()}

        # Удалим старые ингредиенты
        for id, ingredient in old_ingredients_dict.items():
            if id not in new_ingredients_dict:
                ingredient.delete()

        # Добавим новые, либо обновим старые
        for ingredient_data in new_ingredients_dict.values():
            RecipeIngredient.objects.update_or_create(
                recipe=instance,
                ingredient=ingredient_data['ingredient'],
                defaults=ingredient_data)

        return instance

    def validate_ingredients(self, value):
        seen = set()
        if any(x['ingredient'].id in seen or seen.add(x['ingredient'].id)
               for x in value):
            raise serializers.ValidationError(
                'This list may not contain duplicate items.')
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
        short_link = obj[0].short_link
        return reverse('short-link-redirect', args=(short_link,))


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
