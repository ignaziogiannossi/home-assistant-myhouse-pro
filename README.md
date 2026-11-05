# MyHouse Pro Cloud

Unofficial community integration for Home Assistant, tested with two **MAXA MC6** thermostats using the MyHouse Pro cloud service. Maintained by Ignazio Giannossi; not affiliated with or endorsed by the device or app manufacturer.

[Italiano](README.it.md) · [Report an issue](https://github.com/ignaziogiannossi/home-assistant-myhouse-pro/issues)

## Status

Current release: **0.2.2**, based on the 0.2.0 installation used with two MC6 thermostats. Compatibility with other devices/accounts is not yet established. The integration is distributed through its GitHub link; inclusion in the searchable Marketplace/HACS catalog is a separate review process.

## Features

| Feature | Behavior |
| --- | --- |
| Room temperature and humidity | Read from the cloud, refreshed every 60 seconds per thermostat |
| Power | Explicit on/off command, followed by cloud readback |
| Target temperature | Number entity, 5–35 °C in 0.5 °C steps; cloud readback confirms the reported value |
| Additional cloud fields | Read-only differential, frost/hold temperatures, mode, schedule, keypad, standby, fan and other available fields |
| Multiple thermostats | Repeat setup for each thermostat; one device per config entry |
| Diagnostics | Allowlisted numeric status only; no credentials, account/device IDs, names or raw API responses |

Some extra fields are undocumented vendor codes or durations with unverified units. Their labels and attributes explicitly say so. Missing fields are unavailable. HA displays temperatures in the user's preferred units; the number entity's native value is Celsius.

**Cloud readback is not physical confirmation.** The cloud can report stale or different values from the display. The integration does not report a measured heating relay state and does not supply a `climate` entity. A household-specific hysteresis calculation or dashboard is not part of this package. Power on does not mean the boiler is currently heating. Heat/cool mode, schedules, keypad settings and fan commands are not implemented.

## Cloud transport and credentials

All login, reading and command requests use **HTTPS with certificate and hostname verification** at `https://www.mycomforthouse.com/iotfront/api.php/`. Requests never fall back to HTTP and never follow redirects. If TLS verification fails, the connection fails closed. The fixed-key AES layer remains only for vendor protocol compatibility; TLS provides transport protection.

**Upgrade older versions:** 0.2.1 and earlier used an HTTP endpoint and should be replaced with 0.2.2. The protocol's fixed AES key did not protect those connections against interception. This change secures this integration's connection to the cloud; it does not change the vendor app or thermostat firmware.

Your MyHouse Pro credentials are stored locally in Home Assistant's config entry, like other password-based integrations, and are sent to the MyHouse Pro service to sign in. Protect your Home Assistant instance and backups. No credentials, logs, household configuration or analytics are included in this repository. No telemetry is sent to the project maintainer. Internet and the vendor cloud are required; vendor changes may break the integration.

## Installation

Requires **Home Assistant 2026.11 or newer** (the currently targeted version).

### Marketplace / HACS

1. In Home Assistant 2026.11, open **Settings → Marketplace → Add from link**.
2. Add `https://github.com/ignaziogiannossi/home-assistant-myhouse-pro`, choose **Integration** if asked, and install.
3. Restart Home Assistant.
4. Open **Settings → Devices & services → Add integration → MyHouse Pro Cloud**.
5. Read the transport notice, enter your own MyHouse Pro email/password, and select a thermostat. Repeat to add another.

With HACS, use **Custom repositories**, the same URL and category **Integration**.

[![Open in Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=ignaziogiannossi&repository=home-assistant-myhouse-pro&category=integration)

### Manual installation

Copy `custom_components/myhouse_pro` from a repository archive into your Home Assistant configuration directory's `custom_components` directory, restart, and follow steps 4–5 above. Keep the folder name `myhouse_pro`.

The thermostat must already work in the MyHouse Pro app and use its Wi-Fi/cloud mode. Do not switch it to Modbus TCP for this integration. Setup performs reads only. Nothing automatically changes temperatures, power or schedules.

## Updating an existing prototype

Make a Home Assistant backup first. Version 0.2.2 keeps the `myhouse_pro` domain, config-entry format and entity unique IDs from 0.2.0. Replace the component folder or let Marketplace/HACS manage the same domain, then restart. Check readings and existing dashboards afterwards. Entity labels now support English and Italian; user-assigned names remain under HA's entity registry. This release does not deploy or modify household dashboards or automations.

## Troubleshooting and removal

- Sign-in rejected: confirm the same email/password works in MyHouse Pro. Reauthentication must use the same account.
- Device absent: check cloud mode, account ownership and app visibility. Discovery accepts the thermostat/heating device types used by the protocol; other device types are excluded.
- Unavailable: wait for the next poll and check the app, Internet access and vendor service. Unknown response structures are rejected rather than guessed.
- Command not confirmed: check the app and physical display before retrying. A timeout does not prove a command failed. Writes are never automatically resent.
- Odd extra values: report the field name, model and an anonymized example; don't assume raw codes or times have known meanings.
- To remove: delete the integration entry in **Devices & services**, uninstall from Marketplace/HACS (or remove the component directory for a manual install), and restart. The physical thermostat remains usable independently.

When reporting a bug, include Home Assistant/integration versions, model, expected and observed behavior, and sanitized diagnostics. **Do not post passwords, tokens, IDs, household names, unredacted screenshots or complete HA backups.**

## Development and maintenance

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python -m compileall -q custom_components
```

Tests use synthetic accounts and fake transports, never the vendor's live service or your home. GitHub Actions also runs HACS validation and hassfest. These tests cover protocol handling, command serialization/readback and packaging; they do not replace testing setup and controls on physical devices. See [CHANGELOG](CHANGELOG.md) and [release checklist](docs/RELEASE_CHECKLIST.md).

MIT license. Names and trademarks belong to their respective owners; the package icon is an original generic thermostat symbol.
