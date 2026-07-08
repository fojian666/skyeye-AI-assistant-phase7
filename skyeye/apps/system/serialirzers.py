from rest_framework import serializers
from .models import Region

class RegionSerializer(serializers.ModelSerializer):
    """行政区划序列化器"""
    class Meta:
        model = Region
        fields = '__all__'  # 序列化所有字段
        read_only_fields = ['region_id', 'create_time']  # 主键和创建时间只读（后端自动生成）

    # 字段验证：经度范围（-180 ~ 180）
    def validate_longitude(self, value):
        if not (-180 <= value <= 180):
            raise serializers.ValidationError("经度范围必须在 -180 到 180 之间")
        return value

    # 字段验证：纬度范围（-90 ~ 90）
    def validate_latitude(self, value):
        if not (-90 <= value <= 90):
            raise serializers.ValidationError("纬度范围必须在 -90 到 90 之间")
        return value

    # 可选：创建时自动填充父级名称和父级代码（若前端未传）
    def create(self, validated_data):
        parent_id = validated_data.get('parent_id', 0)
        if parent_id != 0:
            try:
                parent_region = Region.objects.get(region_id=parent_id)
                validated_data['parent_name'] = parent_region.region_name
                validated_data['parent_code'] = parent_region.region_code
            except Region.DoesNotExist:
                raise serializers.ValidationError(f"父级区域 ID {parent_id} 不存在")
        return super().create(validated_data)

    # 可选：更新时自动更新父级名称和父级代码（若父级 ID 改变）
    def update(self, instance, validated_data):
        parent_id = validated_data.get('parent_id', instance.parent_id)
        if parent_id != instance.parent_id:
            if parent_id == 0:
                validated_data['parent_name'] = ''
                validated_data['parent_code'] = ''
            else:
                try:
                    parent_region = Region.objects.get(region_id=parent_id)
                    validated_data['parent_name'] = parent_region.region_name
                    validated_data['parent_code'] = parent_region.region_code
                except Region.DoesNotExist:
                    raise serializers.ValidationError(f"父级区域 ID {parent_id} 不存在")
        return super().update(instance, validated_data)