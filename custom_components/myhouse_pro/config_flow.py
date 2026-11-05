"""Login and explicit selection of one thermostat per config entry."""
try:
    import probatio as vol
except ImportError:
    import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType, SelectSelector

from .api import MyHouseClient, AuthenticationError, MyHouseError
from .const import DOMAIN, CONF_DEVICE


class MyHouseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._client = None
        self._credentials = {}
        self._reauth_entry = None

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._credentials = {
                CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }
            self._client = MyHouseClient(async_get_clientsession(self.hass))
            try:
                await self._client.login(self._credentials[CONF_USERNAME], self._credentials[CONF_PASSWORD])
                devices = await self._client.discover()
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except MyHouseError:
                errors["base"] = "cannot_connect"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                elif self._reauth_entry is not None:
                    entry = self._reauth_entry
                    expected = f"{self._client.account_id}_{entry.data[CONF_DEVICE]}"
                    if expected != entry.unique_id:
                        errors["base"] = "wrong_account"
                    elif entry.data[CONF_DEVICE] not in self._client.devices:
                        errors["base"] = "no_devices"
                    else:
                        return self.async_update_reload_and_abort(entry, data_updates=self._credentials)
                else:
                    return await self.async_step_device()
        return self.async_show_form(
            step_id="user", errors=errors,
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): TextSelector(TextSelectorConfig(type=TextSelectorType.EMAIL)),
                vol.Required(CONF_PASSWORD): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            }))

    async def async_step_device(self, user_input=None):
        if self._client is None:
            return await self.async_step_user()
        errors = {}
        if user_input is not None:
            device = self._client.devices.get(user_input[CONF_DEVICE])
            if device is None:
                errors["base"] = "no_devices"
            else:
                try:
                    await self._client.read(device)
                except MyHouseError:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(f"{device.account_id}_{device.device_id}")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=device.name,
                        data={**self._credentials, CONF_DEVICE: device.device_id})
        options = [{"value": d.device_id, "label": f"{d.name} ({d.home_name})"}
                   for d in self._client.devices.values()]
        return self.async_show_form(step_id="device", errors=errors,
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): SelectSelector({"options": options, "mode": "dropdown"})}))

    async def async_step_reauth(self, entry_data):
        self._reauth_entry = self._get_reauth_entry()
        return await self.async_step_user()
