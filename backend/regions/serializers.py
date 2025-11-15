from rest_framework import serializers
from .models import Region


class RegionSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = Region
        fields = [
            'id', 'organization', 'organization_name', 'name', 'code', 
            'location', 'client_endpoint', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True}
        }
