from rest_framework import permissions


class IsCurrentUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.user
    

class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS:
            return request.user == obj.author
        return True
