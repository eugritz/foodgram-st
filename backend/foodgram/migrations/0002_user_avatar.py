# Generated by Django 5.2.1 on 2025-05-29 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodgram', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar',
            field=models.ImageField(default=None, null=True, upload_to='users/avatars/'),
        ),
    ]
