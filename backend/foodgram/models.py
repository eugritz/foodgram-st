from django.contrib.auth.models import AbstractUser
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
