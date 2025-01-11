from rest_framework import serializers
from .models import Project, Building, RawData

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class ProjectSerializer(serializers.ModelSerializer):
    buildings = BuildingSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class RawDataSerializer(serializers.ModelSerializer):
    project_number = serializers.CharField(source='project.project_number', read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    building_name = serializers.CharField(source='building.building_name', read_only=True)

    class Meta:
        model = RawData
        fields = '__all__'

class RawDataUploadSerializer(serializers.Serializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    building = serializers.PrimaryKeyRelatedField(queryset=Building.objects.all())
    file = serializers.FileField()

class LogDesignationSerializer(serializers.ModelSerializer):
    project_number = serializers.CharField(source='project.project_number', read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    building_name = serializers.CharField(source='building.building_name', read_only=True)

    class Meta:
        model = RawData
        fields = (
            'id', 'log_designation', 'project', 'project_number', 'project_name',
            'building', 'building_name', 'part_mark', 'quantity', 'profile',
            'grade', 'length', 'single_part_weight'
        )
