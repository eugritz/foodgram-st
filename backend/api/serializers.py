from django.core.files.base import ContentFile
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer,
)
from rest_framework import serializers
import base64
import uuid

from foodgram.models import Ingredient, Recipe, RecipeIngredient, User


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
    ingredients = RecipeIngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = '__all__'

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

        # Найдем ингредиенты которые требуется удалить, т.е. которых нет в новом
        # списке
        delete_ids = set(old_ingredients_dict.keys()).difference(
            set(new_ingredients_dict.keys()))

        # Удалим старые ингредиенты
        for delete_id in delete_ids:
            old_ingredients_dict[delete_id].delete()

        # Добавим новые, либо обновим старые
        for ingredient_data in new_ingredients_dict.values():
            RecipeIngredient.objects.update_or_create(
                recipe=instance,
                ingredient=ingredient_data['ingredient'],
                defaults=ingredient_data)
            
        return instance
