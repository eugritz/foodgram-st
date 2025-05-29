from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Ingredient, User


class IngredientResource(resources.ModelResource):
    class Meta:
        model = Ingredient


class IngredientAdmin(ImportExportModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('user',)
    empty_value_display = '-пусто-'
    resource_classes = [IngredientResource]


admin.site.register(User, UserAdmin)
admin.site.register(Ingredient, IngredientAdmin)
