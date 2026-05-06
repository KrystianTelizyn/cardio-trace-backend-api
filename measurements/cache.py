from typing import Protocol

import redis

import config.redis as redis_config

DEVICE_NOT_FOUND_SENTINEL = "NONE"


class IngestionRoutingStore(Protocol):
    def set_device_session(
        self, *, tenant_id: int, device_uid: str, session_uid: str, ttl: int
    ) -> None: ...

    def set_device_session_not_found(
        self, *, tenant_id: int, device_uid: str, ttl: int
    ) -> None: ...

    def set_device_map(
        self,
        *,
        tenant_id: str,
        brand: str,
        serial_number: str,
        device_uid: str,
        ttl: int,
    ) -> None: ...

    def set_device_map_not_found(
        self, *, tenant_id: str, brand: str, serial_number: str, ttl: int
    ) -> None: ...


class RedisIngestionRoutingStore:
    def __init__(self, *, client: redis.Redis) -> None:
        self.client = client

    def _set(self, *, key: str, value: str, ttl: int) -> None:
        if ttl > 0:
            self.client.set(key, value, ex=ttl)
            return

        self.client.set(key, value)

    def set_device_session(
        self, *, tenant_id: int, device_uid: str, session_uid: str, ttl: int
    ) -> None:
        key = f"device_session:{tenant_id}:{device_uid}"
        self._set(key=key, value=session_uid, ttl=ttl)

    def set_device_session_not_found(
        self, *, tenant_id: int, device_uid: str, ttl: int
    ) -> None:
        key = f"device_session:{tenant_id}:{device_uid}"
        self._set(key=key, value=DEVICE_NOT_FOUND_SENTINEL, ttl=ttl)

    def set_device_map(
        self,
        *,
        tenant_id: str,
        brand: str,
        serial_number: str,
        device_uid: str,
        ttl: int,
    ) -> None:
        key = f"device_map:{tenant_id}:{brand}:{serial_number}"
        self._set(key=key, value=device_uid, ttl=ttl)

    def set_device_map_not_found(
        self, *, tenant_id: str, brand: str, serial_number: str, ttl: int
    ) -> None:
        key = f"device_map:{tenant_id}:{brand}:{serial_number}"
        self._set(key=key, value=DEVICE_NOT_FOUND_SENTINEL, ttl=ttl)


def build_ingestion_routing_store() -> IngestionRoutingStore:
    return RedisIngestionRoutingStore(client=redis_config.get_client())
