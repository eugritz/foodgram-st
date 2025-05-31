from foodgram.models import (
    Ingredient,
    Recipe,
    RecipeIngredient as RecipeIngredientModel,
)
from functools import lru_cache


class RecipeIngredient:
    ingredient: Ingredient
    amount: int

    def __init__(self, model: RecipeIngredientModel):
        self.ingredient = model.ingredient
        self.amount = model.amount


class ShoppingCartGenerator():
    def __init__(self, recipes: Recipe):
        self.recipes = recipes

    def render_ingredient(self, ingredient: RecipeIngredient):
        return (
            f'- {ingredient.ingredient.name.capitalize()} —'
            f' {ingredient.amount}'
            f' {ingredient.ingredient.measurement_unit}'
        )

    @lru_cache
    def __str__(self):
        ingredients_dict = {}  # type: dict[int, RecipeIngredient]

        non_empty_recipes_count = 0
        recipes_contents_render = ''
        recipes_list_render = ''

        for recipe in self.recipes:
            ingredients = list(recipe.ingredients.all())

            if len(ingredients) > 0:
                non_empty_recipes_count += 1
                if recipes_contents_render != '':
                    recipes_contents_render += '\n'
                recipes_contents_render += (
                    f'{non_empty_recipes_count}. {recipe.name}'
                )
                recipes_list_render += f'### {recipe.name}\n'

            for ingredient in ingredients:
                ingredient2 = RecipeIngredient(ingredient)
                recipes_list_render += \
                    self.render_ingredient(ingredient2) + '\n'

                id = ingredient.ingredient.id
                if id in ingredients_dict:
                    ingredients_dict[id].amount += ingredient2.amount
                else:
                    ingredients_dict[id] = ingredient2

            recipes_list_render += '\n'

        ingredient_list_render = '\n'.join(map(
            self.render_ingredient,
            sorted(ingredients_dict.values(), key=lambda x: x.ingredient.name)
        ))

        if non_empty_recipes_count > 0:
            recipes_contents_render = recipes_contents_render + '\n'
            ingredient_list_render = ingredient_list_render + '\n'
            recipes_list_render = recipes_list_render + '\n'

        render = f'''# Список покупок

## Ингредиенты
{ingredient_list_render}
## Рецепты
{recipes_contents_render}
{recipes_list_render}
'''

        return render.rstrip() + '\n'
