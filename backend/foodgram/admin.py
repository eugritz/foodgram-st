from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import (
    Favorite,
    Ingredient,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    User,
)


class IngredientResource(resources.ModelResource):
    class Meta:
        model = Ingredient


class BaseModelAdmin(admin.ModelAdmin):
    empty_value_display = '-пусто-'


class IngredientAdmin(ImportExportModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('user',)
    empty_value_display = '-пусто-'
    resource_classes = [IngredientResource]


class SubscriptionAdmin(BaseModelAdmin):
    list_display = ('pk', 'user', 'subscribed_to')
    search_fields = ('user', 'subscribed_to')


class RecipeAdmin(BaseModelAdmin):
    list_display = (
        'pk',
        'author',
        'name',
        'image',
        'text',
        'cooking_time',
        'created_at',
    )
    search_fields = ('author', 'name')


class RecipeIngredientAdmin(BaseModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe', 'ingredient')


class FavoriteAdmin(BaseModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')


class ShoppingCartAdmin(BaseModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')


admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(User, UserAdmin)
