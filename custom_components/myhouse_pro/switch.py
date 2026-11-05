"""On/off only: does not infer or change heat/cool mode."""
from homeassistant.components.switch import SwitchEntity
from .entity import MyHouseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MyHousePower(entry.runtime_data)])


class MyHousePower(MyHouseEntity, SwitchEntity):
    _attr_translation_key = "power"
    _attr_icon = "mdi:power"

    def __init__(self, coordinator):
        super().__init__(coordinator, "power")

    @property
    def is_on(self):
        return str(self.coordinator.data.get("state")) == "1"

    async def async_turn_on(self, **kwargs):
        await self.coordinator.command(power=True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.command(power=False)
