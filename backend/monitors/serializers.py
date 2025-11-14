from rest_framework import serializers
from .models import Monitor
from regions.serializers import RegionSerializer


class MonitorSerializer(serializers.ModelSerializer):
    regions = RegionSerializer(many=True, read_only=True)
    region_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=None,
        write_only=True,
        required=False,
        source='regions'
    )
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = Monitor
        fields = [
            'id', 'organization', 'organization_name', 'name', 'check_type', 'target',
            'expected_status_code', 'expected_keyword', 'expected_dns_record', 'dns_record_type',
            'check_interval', 'timeout', 'high_latency_threshold', 'regions', 'region_ids',
            'is_active', 'is_paused', 'created_at', 'updated_at', 'created_by', 'created_by_email'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('request'):
            # Filter regions by user's organizations
            user = self.context['request'].user
            from regions.models import Region
            self.fields['region_ids'].queryset = Region.objects.filter(
                organization__members__user=user,
                organization__members__is_active=True
            ).distinct()

    def validate(self, attrs):
        check_type = attrs.get('check_type', self.instance.check_type if self.instance else None)
        
        if check_type == 'custom' and not attrs.get('expected_keyword'):
            raise serializers.ValidationError({
                'expected_keyword': 'Expected keyword is required for custom check type'
            })
        
        if check_type == 'dns' and not attrs.get('expected_dns_record'):
            raise serializers.ValidationError({
                'expected_dns_record': 'Expected DNS record is required for DNS check type'
            })
        
        return attrs

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
