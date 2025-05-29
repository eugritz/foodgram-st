from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        extra_kwargs = {
            'first_name': { 'required': True },
            'last_name': { 'required': True },
        }
