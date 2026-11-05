"""Temperature target reported by the cloud, in Celsius."""
from homeassistant.components.number import NumberEntity, NumberMode, NumberDeviceClass
from homeassistant.const import UnitOfTemperature
from .api import in_celsius
from .entity import MyHouseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MyHouseSetpoint(entry.runtime_data)])


class MyHouseSetpoint(MyHouseEntity, NumberEntity):
    _attr_translation_key = "setpoint"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 5.0
    _attr_native_max_value = 35.0
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator):
        super().__init__(coordinator, "setpoint")

    @property
    def native_value(self):
        return in_celsius(self.coordinator.data, "e_tempera")

    async def async_set_native_value(self, value):
        await self.coordinator.command(temperature=value)
