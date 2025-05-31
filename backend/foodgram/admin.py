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
    search_fields = ('name',)
    empty_value_display = '-пусто-'
    resource_classes = [IngredientResource]


class SubscriptionAdmin(BaseModelAdmin):
    list_display = ('pk', 'user', 'subscribed_to')
    search_fields = ('user__email', 'subscribed_to__email')


@admin.display(description='Author')
def author(obj):
    return f'{obj.author.email} ({obj.author.first_name} {obj.author.last_name})'


@admin.display(description='Author')
def author(obj):
    return 'test'


@admin.display(description='Favorites count')
def favorites_count(obj):
    return obj.favorited.count()


class RecipeAdmin(BaseModelAdmin):
    readonly_fields = (favorites_count,)
    list_display = (
        'pk',
        author,
        'name',
        'image',
        'text',
        'cooking_time',
        'created_at',
    )
    search_fields = (
        'author__email',
        'author__first_name',
        'author__last_name',
        'name'
    )


class RecipeIngredientAdmin(BaseModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')


class FavoriteAdmin(BaseModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user__email', 'recipe__name')


class ShoppingCartAdmin(BaseModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user__email', 'recipe__name')


admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(User, UserAdmin)
