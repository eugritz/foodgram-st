from django.db import migrations
from import_export import resources
from pathlib import Path
import os
import tablib


def import_ingredients(apps, schema_editor):
    Ingredient = apps.get_model('foodgram', 'Ingredient')

    base_dir = Path(__file__).resolve().parent.parent.parent
    data_file = os.path.join(base_dir, 'data/ingredients.json')
    imported_data = tablib.Dataset().load(
        open(data_file, encoding='utf-8').read())
    ingredient_resource = resources.modelresource_factory(model=Ingredient)()
    ingredient_resource.import_data(imported_data)


class Migration(migrations.Migration):
    dependencies = [
        ('foodgram', '0010_alter_recipe_options_recipe_created_at'),
    ]

    operations = [
        migrations.RunPython(import_ingredients),
    ]
