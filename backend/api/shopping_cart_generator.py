from foodgram.models import (
    Ingredient,
    Recipe as RecipeModel,
    RecipeIngredient as RecipeIngredientModel,
)
from functools import lru_cache
from typing import Iterable


class RecipeIngredient:
    ingredient: Ingredient
    amount: int

    def __init__(self, model: RecipeIngredientModel):
        self.ingredient = model.ingredient
        self.amount = model.amount


class Recipe:
    name: str
    ingredients: Iterable[RecipeIngredient]

    def __init__(self, model: RecipeModel):
        self.name = model.name
        self.ingredients = sorted(
            (RecipeIngredient(x) for x in model.ingredients.all()),
            key=lambda x: x.ingredient.name.lower(),
        )


class ShoppingCartGenerator:
    def __init__(self, recipes: Iterable[Recipe]):
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
            recipe_render = ''

            ingredient_count = 0
            for ingredient in recipe.ingredients:
                ingredient_count += 1

                recipe_render += self.render_ingredient(ingredient) + '\n'

                id = ingredient.ingredient.id
                if id in ingredients_dict:
                    ingredients_dict[id].amount += ingredient.amount
                else:
                    ingredients_dict[id] = ingredient

            if ingredient_count == 0:
                continue

            non_empty_recipes_count += 1
            if recipes_contents_render != '':
                recipes_contents_render += '\n'
            recipes_contents_render += (
                f'{non_empty_recipes_count}. {recipe.name}'
            )
            recipe_render = f'### {recipe.name}\n' + recipe_render
            recipes_list_render += recipe_render + '\n'

        ingredient_list_render = '\n'.join(map(
            self.render_ingredient,
            sorted(
                ingredients_dict.values(),
                key=lambda x: x.ingredient.name.lower(),
            ),
        ))

        if non_empty_recipes_count > 0:
            recipes_contents_render = recipes_contents_render + '\n'
            ingredient_list_render = ingredient_list_render + '\n'
            recipes_list_render = recipes_list_render + '\n'

        render = (
            '# Список покупок\n'
            '\n'
            '## Ингредиенты\n'
            f'{ingredient_list_render}\n'
            '## Рецепты\n'
            f'{recipes_contents_render}\n'
            f'{recipes_list_render}\n'
        )

        return render.rstrip() + '\n'
