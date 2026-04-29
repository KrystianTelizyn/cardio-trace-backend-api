from rest_framework import serializers


class MeasurementIngestInputSerializer(serializers.Serializer):
    serial_number = serializers.CharField(required=True)
    brand = serializers.CharField(required=True)
    timestamp = serializers.DateTimeField(required=True)
    heart_rate = serializers.FloatField(required=True)
    hrv = serializers.FloatField(required=True)


class MeasurementIngestOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    device_id = serializers.IntegerField(read_only=True)
    patient_id = serializers.IntegerField(read_only=True)
    tenant_id = serializers.IntegerField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    heart_rate = serializers.FloatField(read_only=True)
    hrv = serializers.FloatField(read_only=True)
