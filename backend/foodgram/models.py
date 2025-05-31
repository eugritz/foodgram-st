from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
import random
import string


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
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)


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
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited',
    )

    class Meta:
        unique_together = ['user', 'recipe']


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_carts',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_carts',
    )

    class Meta:
        unique_together = ['user', 'recipe']


def random_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=3))


class ShortLink(models.Model):
    short_link = models.TextField(primary_key=True, default=random_id)
    destination = models.TextField(unique=True)
