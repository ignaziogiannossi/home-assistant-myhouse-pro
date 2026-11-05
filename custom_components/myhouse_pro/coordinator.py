"""Shared polling for the selected thermostat."""
from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import HomeAssistantError

from .api import DeviceController, MyHouseError
from .const import DOMAIN


class MyHouseCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, controller: DeviceController):
        super().__init__(hass, logging.getLogger(__name__), config_entry=entry,
                         name=DOMAIN, update_interval=timedelta(seconds=60))
        self.controller = controller
        self.device = controller.device

    async def _async_update_data(self):
        try:
            return await self.controller.read()
        except MyHouseError as err:
            raise UpdateFailed(str(err)) from None

    async def command(self, **kwargs):
        try:
            result = await self.controller.command(**kwargs)
        except MyHouseError as err:
            # A timeout is not proof that a write failed: never retry a write automatically.
            await self.async_request_refresh()
            raise HomeAssistantError(str(err)) from None
        self.async_set_updated_data(result)
