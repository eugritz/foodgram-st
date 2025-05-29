from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    email = models.EmailField('email address', unique=True)
    avatar = models.ImageField(
        upload_to='users/avatars/',
        null=True,  
        default=None,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    subscribed_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
    )

    class Meta:
        unique_together = ['user', 'subscribed_to']

    def clean(self):
        if self.user == self.subscribed_to:
            raise ValidationError('user must not be equal to subscribed_to')


class Ingredient(models.Model):
    name = models.TextField(max_length=128)
    measurement_unit = models.TextField(max_length=64)


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.TextField(max_length=256)
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,  
        default=None,
    )
    text = models.TextField()
    cooking_time = models.PositiveIntegerField(validators=[
        validators.MinValueValidator(1)
    ])


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(validators=[
        validators.MinValueValidator(1)
    ])


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['user', 'recipe']


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_recipes',
    )
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['user', 'recipe']
