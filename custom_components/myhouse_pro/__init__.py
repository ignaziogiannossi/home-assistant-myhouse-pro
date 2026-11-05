"""Experimental cloud integration for MyHouse Pro."""
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MyHouseClient, DeviceController, AuthenticationError, MyHouseError
from .const import CONF_DEVICE, PLATFORMS
from .coordinator import MyHouseCoordinator


async def async_setup_entry(hass, entry):
    client = MyHouseClient(async_get_clientsession(hass))
    try:
        await client.login(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
        await client.discover()
        device = client.devices.get(entry.data[CONF_DEVICE])
        if device is None:
            raise MyHouseError("Il termostato selezionato non è più presente nell'account")
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed(str(err)) from None
    except MyHouseError as err:
        raise ConfigEntryNotReady(str(err)) from None
    coordinator = MyHouseCoordinator(hass, entry, DeviceController(client, device))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
