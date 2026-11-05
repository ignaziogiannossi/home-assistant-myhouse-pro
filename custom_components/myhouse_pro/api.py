"""MyHouse Pro Android 1.1.9 protocol. Unofficial; live validation required.

The vendor uses HTTP and a fixed AES key. This reproduces that legacy protocol;
it does not provide TLS security. Never log credentials, IDs or response bodies.
"""
from __future__ import annotations

import asyncio
import base64
import binascii
from dataclasses import dataclass
import json
import math
from typing import Any

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad

BASE_URL = "http://www.mycomforthouse.com:8080/iotfront/api.php/"
# Public protocol constant embedded in the vendor APK; not a user credential.
PROTOCOL_KEY = b"www.brande.commc6mqtt_aes256ecb7"
MAX_RESPONSE = 1024 * 1024
TIMEOUT = 20


class MyHouseError(Exception):
    """Sanitized error, safe for Home Assistant logs."""


class AuthenticationError(MyHouseError):
    """The cloud rejected authentication."""


class ProtocolError(MyHouseError):
    """Unexpected cloud response; do not guess values."""


class CommandNotConfirmed(MyHouseError):
    """The cloud did not report the requested state after a command."""


def encrypt(value: str) -> str:
    cipher = AES.new(PROTOCOL_KEY, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(value.encode("utf-8"), 16))).decode("ascii")


def decrypt(value: bytes) -> str:
    try:
        raw = base64.b64decode(b"".join(value.split()), validate=True)
        return unpad(AES.new(PROTOCOL_KEY, AES.MODE_ECB).decrypt(raw), 16).decode("utf-8")
    except (ValueError, UnicodeError, binascii.Error):
        raise ProtocolError("Risposta cloud non decifrabile") from None


def identifier(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)) or not str(value).strip():
        raise ProtocolError("Identificativo cloud mancante")
    return str(value)


def number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def in_celsius(detail: dict, field: str) -> float | None:
    value = number(detail.get(field))
    if value is None or str(detail.get("temper_type")) not in ("0", "1"):
        return None
    return round((value - 32) / 1.8, 2) if str(detail["temper_type"]) == "1" else value


@dataclass(frozen=True)
class Device:
    account_id: str
    home_id: str
    device_id: str
    name: str
    home_name: str


class MyHouseClient:
    """Session injected by HA. Requests are sequential, with no automatic writes."""

    def __init__(self, session: Any):
        self.session = session
        self.account_id: str | None = None
        self.devices: dict[str, Device] = {}
        self._request_lock = asyncio.Lock()

    async def _post(self, path: str, fields: dict[str, str]) -> Any:
        body = {key: encrypt(str(value)) for key, value in fields.items()}

        async def request():
            # Do not redirect login/password data to any other destination.
            async with self.session.post(BASE_URL + path + "?", data=body, allow_redirects=False) as response:
                if response.status != 200:
                    raise MyHouseError(f"Cloud non disponibile (HTTP {response.status})")
                chunks = bytearray()
                while True:
                    chunk = await response.content.read(min(65536, MAX_RESPONSE + 1 - len(chunks)))
                    if not chunk:
                        break
                    chunks.extend(chunk)
                    if len(chunks) > MAX_RESPONSE:
                        raise ProtocolError("Risposta cloud troppo grande")
                try:
                    result = json.loads(decrypt(bytes(chunks)))
                except json.JSONDecodeError:
                    raise ProtocolError("Risposta cloud non valida") from None
                if not isinstance(result, dict) or not isinstance(result.get("result"), str):
                    raise ProtocolError("Formato risposta cloud sconosciuto")
                if result["result"] != "succ":
                    if path == "User/login":
                        raise AuthenticationError("Accesso MyHouse Pro non riuscito")
                    raise MyHouseError("Il cloud ha rifiutato la richiesta")
                return result.get("info")

        async with self._request_lock:
            try:
                return await asyncio.wait_for(request(), TIMEOUT)
            except MyHouseError:
                raise
            except asyncio.TimeoutError:
                raise MyHouseError("Tempo di risposta MyHouse Pro scaduto") from None
            except Exception:
                # Keep transport exceptions and their potentially sensitive payloads out of logs.
                raise MyHouseError("Connessione MyHouse Pro non riuscita") from None

    async def login(self, username: str, password: str) -> str:
        self.account_id = None
        self.devices = {}
        info = await self._post("User/login", {"name": username, "password": password, "language": "2"})
        if not isinstance(info, dict):
            raise ProtocolError("Dati account non validi")
        self.account_id = identifier(info.get("u_id"))
        return self.account_id

    async def discover(self) -> list[Device]:
        if self.account_id is None:
            raise AuthenticationError("Accedere prima a MyHouse Pro")
        homes = await self._post("Index/my_address", {"u_id": self.account_id})
        if not isinstance(homes, list):
            raise ProtocolError("Elenco case non valido")
        discovered = {}
        for home in homes:
            if not isinstance(home, dict):
                raise ProtocolError("Dati casa non validi")
            home_id = identifier(home.get("a_id"))
            entries = await self._post("Index/my_eq_list", {"u_id": self.account_id, "a_id": home_id})
            if not isinstance(entries, list):
                raise ProtocolError("Elenco dispositivi non valido")
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ProtocolError("Dati dispositivo non validi")
                # APK DeviceBean: type 1 conditioner, 2 heating; exclude plugs etc.
                if str(entry.get("e_id")) not in ("1", "2"):
                    continue
                eq_id = identifier(entry.get("eq_id"))
                discovered[eq_id] = Device(self.account_id, home_id, eq_id,
                    str(entry.get("eq_name") or "Termostato MyHouse Pro"), str(home.get("a_name") or "Casa"))
        self.devices = discovered
        return list(discovered.values())

    def _owned(self, device: Device) -> None:
        if self.account_id != device.account_id or self.devices.get(device.device_id) != device:
            raise MyHouseError("Dispositivo non presente nell'account autenticato")

    async def read(self, device: Device) -> dict:
        self._owned(device)
        # Despite the field name e_id, the app passes eq_id here, not the type ID.
        info = await self._post("Index/eq_read", {"a_id": device.home_id, "e_id": device.device_id})
        if not isinstance(info, dict) or str(info.get("eq_id")) != device.device_id:
            raise ProtocolError("Dettaglio dispositivo non valido")
        return info

    async def set_temperature(self, device: Device, celsius: float, current: dict) -> None:
        self._owned(device)
        if str(current.get("eq_id")) != device.device_id or str(current.get("state")) not in ("1", "2"):
            raise MyHouseError("Termostato non disponibile per il comando")
        value = number(celsius)
        if value is None or not 5 <= value <= 35 or not math.isclose(value * 2, round(value * 2), abs_tol=1e-6):
            raise MyHouseError("Usare una temperatura tra 5 e 35 °C, a passi di 0,5 °C")
        if str(current.get("temper_type")) not in ("0", "1"):
            raise ProtocolError("Unità di temperatura sconosciuta")
        target = value * 1.8 + 32 if str(current["temper_type"]) == "1" else value
        await self._post("Index/edit_temper", {"eq_id": device.device_id, "temperature": f"{target:.1f}"})

    async def set_power(self, device: Device, on: bool) -> None:
        self._owned(device)
        if not isinstance(on, bool):
            raise MyHouseError("Stato di accensione non valido")
        await self._post("Index/edit_switch", {"eq_id": device.device_id, "state": "1" if on else "2"})


class DeviceController:
    """Serialize reads and commands. Confirmation refers to cloud readback only."""

    def __init__(self, client: MyHouseClient, device: Device, delay: float = 2, attempts: int = 5):
        self.client = client
        self.device = device
        self.delay = delay
        self.attempts = attempts
        self._lock = asyncio.Lock()

    async def read(self) -> dict:
        async with self._lock:
            return await self.client.read(self.device)

    async def command(self, *, temperature: float | None = None, power: bool | None = None) -> dict:
        if (temperature is None) == (power is None):
            raise MyHouseError("Specificare esattamente un comando")
        async with self._lock:
            current = await self.client.read(self.device)
            if str(current.get("state")) not in ("1", "2"):
                raise MyHouseError("Termostato non disponibile per il comando")
            if temperature is not None:
                await self.client.set_temperature(self.device, temperature, current)
            else:
                await self.client.set_power(self.device, power)
            for _ in range(self.attempts):
                await asyncio.sleep(self.delay)
                result = await self.client.read(self.device)
                if temperature is not None:
                    actual = in_celsius(result, "e_tempera")
                    matches = actual is not None and math.isclose(actual, temperature, abs_tol=0.06)
                else:
                    matches = str(result.get("state")) == ("1" if power else "2")
                if matches and str(result.get("state")) in ("1", "2"):
                    return result
            raise CommandNotConfirmed("Il cloud non conferma il nuovo valore; verificare app e display prima di riprovare")
