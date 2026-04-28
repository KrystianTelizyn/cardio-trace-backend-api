from rest_framework import serializers


class DeviceCreateInputSerializer(serializers.Serializer):
    serial_number = serializers.CharField(required=True)
    brand = serializers.CharField(required=True)
    name = serializers.CharField(required=True)


class DeviceCreateOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    serial_number = serializers.CharField(read_only=True)
    brand = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class DeviceAssignmentInputSerializer(serializers.Serializer):
    device_id = serializers.IntegerField(required=True)
    patient_profile_id = serializers.IntegerField(required=True)


class DeviceAssignmentOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    device_id = serializers.IntegerField(read_only=True)
    patient_profile_id = serializers.IntegerField(read_only=True)
