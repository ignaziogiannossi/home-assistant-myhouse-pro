"""Common entity metadata; no inferred heating-relay state."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN


class MyHouseEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key):
        super().__init__(coordinator)
        device = coordinator.device
        self._attr_unique_id = f"{device.account_id}_{device.device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{device.account_id}_{device.device_id}")},
            name=device.name, manufacturer="MyHouse Pro / JTY Controls",
            model="Cloud thermostat")

    @property
    def available(self):
        return super().available and str((self.coordinator.data or {}).get("state")) in ("1", "2")
