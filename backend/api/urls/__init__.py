from django.urls import include, path
from rest_framework import routers

from ..views import (
    CurrentUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    SubscriptionViewSet,
    UserViewSet,
)


router = routers.DefaultRouter()
router.register(
    'users/subscriptions',
    SubscriptionViewSet,
    basename='user-subscriptions'
)
router.register('users', UserViewSet)
router.register('users/me', CurrentUserViewSet, basename='current-user')
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)

urlpatterns = [
    # path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
