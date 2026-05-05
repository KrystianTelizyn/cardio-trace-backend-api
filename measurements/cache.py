from typing import Protocol

import redis

import config.redis as redis_config


class IngestionRoutingStore(Protocol):
    def set_device_session(
        self, *, tenant_id: int, device_uid: str, session_uid: str
    ) -> None: ...

    def delete_device_session(self, *, tenant_id: int, device_uid: str) -> None: ...

    def set_device_map(
        self, *, tenant_id: int, brand: str, serial_number: str, device_uid: str
    ) -> None: ...


class RedisIngestionRoutingStore:
    def __init__(self, *, client: redis.Redis) -> None:
        self.client = client

    def set_device_session(
        self, *, tenant_id: int, device_uid: str, session_uid: str
    ) -> None:
        key = f"device_session:{tenant_id}:{device_uid}"
        self.client.set(key, session_uid)

    def delete_device_session(self, *, tenant_id: int, device_uid: str) -> None:
        key = f"device_session:{tenant_id}:{device_uid}"
        self.client.delete(key)

    def set_device_map(
        self, *, tenant_id: int, brand: str, serial_number: str, device_uid: str
    ) -> None:
        key = f"device_map:{tenant_id}:{brand}:{serial_number}"
        self.client.set(key, device_uid)


def build_ingestion_routing_store() -> IngestionRoutingStore:
    return RedisIngestionRoutingStore(client=redis_config.get_client())
