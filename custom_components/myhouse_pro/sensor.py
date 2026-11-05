"""Measured temperature and humidity, without extra cloud calls."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from .api import in_celsius, number
from .entity import MyHouseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MyHouseSensor(entry.runtime_data, key) for key in ("temperature", "humidity")] + [MyHouseCloudField(entry.runtime_data, field) for field in CLOUD_FIELDS])


class MyHouseSensor(MyHouseEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, key):
        super().__init__(coordinator, key)
        self.key = key
        self._attr_translation_key = key
        self._attr_device_class = SensorDeviceClass.TEMPERATURE if key == "temperature" else SensorDeviceClass.HUMIDITY
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS if key == "temperature" else PERCENTAGE

    @property
    def native_value(self):
        if self.key == "temperature":
            return in_celsius(self.coordinator.data, "tempera")
        value = number(self.coordinator.data.get("humidity"))
        return value if value is not None and 0 <= value <= 100 else None


# Additional read-only fields from the same coordinator response.
# Do not expose identifiers, account data or keyboards_pass.
CLOUD_FIELDS = (
    ("temperature_difference", "Differenziale di regolazione", "delta", "mdi:thermometer-lines"),
    ("antifreeze", "Temperatura antigelo", "temperature", "mdi:snowflake-thermometer"),
    ("holding_temperature", "Temperatura di mantenimento", "temperature", "mdi:thermometer"),
    ("delay_time", "Ritardo accensione valore cloud", "raw_time", "mdi:timer-outline"),
    ("holding_time", "Durata mantenimento valore cloud", "raw_time", "mdi:timer-outline"),
    ("pattern_name", "Modalita cloud", "text", "mdi:home-thermometer"),
    ("pattern", "Modalita operativa codice cloud", "code", "mdi:tune"),
    ("program_mode", "Programmazione codice cloud", "code", "mdi:calendar-clock"),
    ("keyboards", "Blocco tastiera codice cloud", "code", "mdi:lock-outline"),
    ("standbys", "Standby codice cloud", "code", "mdi:monitor"),
    ("speed", "Ventola codice cloud", "code", "mdi:fan"),
    ("holiday", "Vacanza valore cloud", "text", "mdi:beach"),
    ("holiday_startime", "Inizio vacanza cloud", "text", "mdi:calendar-start"),
    ("holiday_endtime", "Fine vacanza cloud", "text", "mdi:calendar-end"),
    ("leave_days", "Durata assenza valore cloud", "raw_time", "mdi:calendar-range"),
    ("leavestate", "Fuori casa codice cloud", "code", "mdi:home-export-outline"),
    ("temper_type", "Unita temperatura cloud", "unit", "mdi:temperature-celsius"),
    ("time_zone", "Fuso orario codice cloud", "code", "mdi:clock-outline"),
    ("versions", "Versione codice cloud", "code", "mdi:information-outline"),
    ("e_id", "Tipo dispositivo codice cloud", "code", "mdi:thermostat"),
)


def cloud_field_value(data, key, kind):
    value = data.get(key)
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    if kind in ("temperature", "delta"):
        if str(data.get("temper_type")) not in ("0", "1"):
            return None
        if kind == "temperature":
            return in_celsius(data, key)
        numeric = number(value)
        if numeric is None:
            return None
        return round(numeric / 1.8 if str(data["temper_type"]) == "1" else numeric, 2)
    if kind == "unit":
        return {"0": "Celsius", "1": "Fahrenheit"}.get(str(value))
    if kind == "raw_time":
        return number(value)
    if not isinstance(value, (str, int, float)):
        return None
    text = str(value).strip()
    return text[:255] if text else None


class MyHouseCloudField(MyHouseEntity, SensorEntity):
    def __init__(self, coordinator, description):
        key, name, kind, icon = description
        super().__init__(coordinator, "cloud_" + key)
        self.key = key
        self.kind = kind
        self._attr_translation_key = key
        self._attr_icon = icon
        self._attr_state_class = None
        if kind == "temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        elif kind == "delta":
            self._attr_device_class = getattr(SensorDeviceClass, "TEMPERATURE_DELTA", None)
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        elif kind in ("code", "unit", "raw_time"):
            from homeassistant.helpers.entity import EntityCategory
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self):
        return super().available and self.key in (self.coordinator.data or {})

    @property
    def native_value(self):
        return cloud_field_value(self.coordinator.data or {}, self.key, self.kind)

    @property
    def extra_state_attributes(self):
        attributes = {"origine": "MyHouse Pro Cloud", "campo_cloud": self.key}
        if self.kind == "code":
            attributes["interpretazione"] = "Codice restituito dal servizio; significato non ancora convalidato"
        elif self.kind == "raw_time":
            attributes["unita"] = "Da verificare; valore originale del servizio"
        return attributes
