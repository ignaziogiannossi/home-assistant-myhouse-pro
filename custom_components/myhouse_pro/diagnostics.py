"""Allowlist only: exclude IDs, names, credentials and raw responses."""
from .api import number, in_celsius


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    data = coordinator.data or {}
    return {
        "version": "0.2.1",
        "last_update_success": coordinator.last_update_success,
        "state": str(data.get("state")) if str(data.get("state")) in ("1", "2", "3") else "unknown",
        "temperature_c": in_celsius(data, "tempera"),
        "target_c": in_celsius(data, "e_tempera"),
        "humidity": number(data.get("humidity")),
        "source": "cloud_readback_not_physical_confirmation",
    }
