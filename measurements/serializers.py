from rest_framework import serializers


class MeasurementIngestInputSerializer(serializers.Serializer):
    measurement_session_id = serializers.CharField(required=True)
    timestamp = serializers.DateTimeField(required=True)
    heart_rate = serializers.FloatField(required=True)
    hrv = serializers.FloatField(required=True)


class MeasurementIngestOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    measurement_session_id = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    heart_rate = serializers.FloatField(read_only=True)
    hrv = serializers.FloatField(read_only=True)


class MeasurementSessionStartInputSerializer(serializers.Serializer):
    device_assignment_id = serializers.IntegerField(required=True)
    started_at = serializers.DateTimeField(required=False)


class MeasurementSessionStartOutputSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)


class MeasurementSessionStopInputSerializer(serializers.Serializer):
    stopped_at = serializers.DateTimeField(required=False)


class MeasurementSessionStopOutputSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    stopped_at = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)
