from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.test import TestCase

from measurements.cache import DEVICE_NOT_FOUND_SENTINEL
from measurements.use_cases import (
    EnrichIngestionContext,
    StartMeasurementSession,
    StopMeasurementSession,
)
from tests.mixins import (
    DevicesFixtureMixin,
    FakeRedisMixin,
    MeasurementFixturesMixin,
    TenantUsersMixin,
)


class StartMeasurementSessionRedisCacheTests(
    FakeRedisMixin,
    TenantUsersMixin,
    DevicesFixtureMixin,
    MeasurementFixturesMixin,
    TestCase,
):
    def test_sets_device_session_key_on_start(self) -> None:
        assignment = self.create_active_assignment(
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC")),
        )

        session = StartMeasurementSession().execute(
            device_assignment_id=assignment.id,
            tenant=self.tenant,
            started_at=datetime(2026, 1, 10, 11, 0, tzinfo=ZoneInfo("UTC")),
        )

        key = f"device_session:{self.tenant.auth0_organization_id}:{self.device.uid}"
        self.assertEqual(self.fake_redis.get(key), session.id)
        self.assertGreater(self.fake_redis.ttl(key), 0)
        self.assertLessEqual(
            self.fake_redis.ttl(key), settings.CACHE_TTL_DEVICE_SESSION_ACTIVE
        )

    def test_supports_unlimited_ttl_for_active_device_session(self) -> None:
        assignment = self.create_active_assignment(
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC")),
        )

        with self.settings(CACHE_TTL_DEVICE_SESSION_ACTIVE=0):
            session = StartMeasurementSession().execute(
                device_assignment_id=assignment.id,
                tenant=self.tenant,
                started_at=datetime(2026, 1, 10, 11, 0, tzinfo=ZoneInfo("UTC")),
            )

        key = f"device_session:{self.tenant.auth0_organization_id}:{self.device.uid}"
        self.assertEqual(self.fake_redis.get(key), session.id)
        self.assertEqual(self.fake_redis.ttl(key), -1)


class StopMeasurementSessionRedisCacheTests(
    FakeRedisMixin,
    TenantUsersMixin,
    DevicesFixtureMixin,
    MeasurementFixturesMixin,
    TestCase,
):
    def test_sets_none_sentinel_for_device_session_key_on_stop(self) -> None:
        assignment = self.create_active_assignment(
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC")),
        )
        session = self.create_measurement_session(
            device_assignment=assignment,
            started_at=datetime(2026, 1, 10, 11, 0, tzinfo=ZoneInfo("UTC")),
        )
        key = f"device_session:{self.tenant.auth0_organization_id}:{self.device.uid}"
        self.fake_redis.set(key, session.id)

        StopMeasurementSession().execute(
            measurement_session_id=session.id,
            tenant=self.tenant,
            stopped_at=datetime(2026, 1, 10, 12, 0, tzinfo=ZoneInfo("UTC")),
        )

        self.assertEqual(self.fake_redis.get(key), DEVICE_NOT_FOUND_SENTINEL)
        self.assertGreater(self.fake_redis.ttl(key), 0)
        self.assertLessEqual(
            self.fake_redis.ttl(key), settings.CACHE_TTL_SESSION_NOT_FOUND
        )

    def test_does_not_touch_redis_when_session_already_stopped(self) -> None:
        assignment = self.create_active_assignment(
            assigned_at=datetime(2026, 1, 10, 10, 0, tzinfo=ZoneInfo("UTC")),
        )
        session = self.create_measurement_session(
            device_assignment=assignment,
            started_at=datetime(2026, 1, 10, 11, 0, tzinfo=ZoneInfo("UTC")),
            stopped_at=datetime(2026, 1, 10, 11, 30, tzinfo=ZoneInfo("UTC")),
        )
        key = f"device_session:{self.tenant.auth0_organization_id}:{self.device.uid}"
        self.fake_redis.set(key, "preserved-value")

        StopMeasurementSession().execute(
            measurement_session_id=session.id,
            tenant=self.tenant,
            stopped_at=datetime(2026, 1, 10, 12, 0, tzinfo=ZoneInfo("UTC")),
        )

        self.assertEqual(self.fake_redis.get(key), "preserved-value")


class EnrichIngestionContextRedisCacheTests(
    FakeRedisMixin,
    TenantUsersMixin,
    DevicesFixtureMixin,
    MeasurementFixturesMixin,
    TestCase,
):
    def test_sets_device_map_and_device_session_when_active_session_exists(
        self,
    ) -> None:
        assignment = self.create_active_assignment()
        session = self.create_measurement_session(device_assignment=assignment)

        EnrichIngestionContext().execute(
            tenant=self.tenant,
            serial_number=self.device.serial_number,
            brand=self.device.brand,
        )

        device_map_key = (
            f"device_map:{self.tenant.auth0_organization_id}:{self.device.brand}:"
            f"{self.device.serial_number}"
        )
        device_session_key = (
            f"device_session:{self.tenant.auth0_organization_id}:{self.device.uid}"
        )
        self.assertEqual(self.fake_redis.get(device_map_key), self.device.uid)
        self.assertEqual(self.fake_redis.get(device_session_key), session.id)

    def test_sets_device_map_and_none_device_session_when_no_active_session(
        self,
    ) -> None:
        device_session_key = (
            f"device_session:{self.tenant.auth0_organization_id}:{self.device.uid}"
        )
        self.fake_redis.set(device_session_key, "stale-session-id")

        EnrichIngestionContext().execute(
            tenant=self.tenant,
            serial_number=self.device.serial_number,
            brand=self.device.brand,
        )

        device_map_key = (
            f"device_map:{self.tenant.auth0_organization_id}:{self.device.brand}:"
            f"{self.device.serial_number}"
        )
        self.assertEqual(self.fake_redis.get(device_map_key), self.device.uid)
        self.assertEqual(
            self.fake_redis.get(device_session_key), DEVICE_NOT_FOUND_SENTINEL
        )
        self.assertGreater(self.fake_redis.ttl(device_map_key), 0)
        self.assertLessEqual(
            self.fake_redis.ttl(device_map_key),
            settings.CACHE_TTL_DEVICE_SESSION_ACTIVE,
        )
        self.assertGreater(self.fake_redis.ttl(device_session_key), 0)
        self.assertLessEqual(
            self.fake_redis.ttl(device_session_key),
            settings.CACHE_TTL_SESSION_NOT_FOUND,
        )
