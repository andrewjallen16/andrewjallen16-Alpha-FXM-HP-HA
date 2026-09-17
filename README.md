# Alpha FXM HP UPS — Home Assistant integration

Custom Home Assistant integration for the **Alpha® (EnerSys) FXM HP** outdoor UPS
modules (650 / 1100 / 2000). Note: this is an outdoor UPS/rectifier product line,
not a solar inverter — Alpha/EnerSys don't publish a Modbus register map for it.
The only documented network monitoring interface is **SNMP**, and Alpha's own
manuals state the FXM HP implements the standard `UPS-MIB` (RFC 1628). This
integration polls that standard MIB, so it doesn't depend on Alpha's large
proprietary Resource MIB and should work across FXM HP firmware/model revisions.

Supports **any number of units** — each FXM HP you add becomes its own config
entry / device in Home Assistant, each polled independently.

## What it does

- Read-only monitoring over SNMP (v1 / v2c / v3, including authPriv).
- One device per UPS with sensors for: battery status/charge/runtime/voltage/
  current/temperature, input voltage/frequency/current/power, output source/
  voltage/frequency/current/power/load%, bypass voltage/frequency, and active
  alarm count.
- Binary sensors: **On battery**, **On bypass**, **Problem** (set when alarms
  are present or the battery is low/depleted).
- Config flow (UI-based setup, no YAML) — add as many units as you like via
  **Settings → Devices & Services → Add Integration → Alpha FXM HP UPS**.
- Options flow to change the polling interval per device.

This integration is **monitoring only** — it does not attempt to control the
UPS (e.g. forcing self-test or shutdown) since those functions on Alpha
controllers require the proprietary Resource MIB with device-specific,
undocumented OIDs, and getting a write wrong on a UPS can cut power to
whatever it protects. If you need control, please open an issue and share the
compiled `ALPHA-RESOURCE-MIB` for your controller firmware.

## Requirements

- Home Assistant 2024.x or newer.
- SNMP enabled on the FXM HP controller (LCD or web UI → SNMP setup), with a
  user/community that has at least **read** access.
- `pysnmp` (declared in `manifest.json`; Home Assistant installs it
  automatically the first time the integration loads).

## Installation

### Via HACS (custom repository)

1. In Home Assistant, go to **HACS → Integrations → ⋮ (top right) → Custom
   repositories**.
2. Add `https://github.com/andrewjallen16/Alpha-FXM-HP-HA`, category
   **Integration**, click **Add**.
3. Find **Alpha FXM HP UPS** in HACS and click **Download**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & Services → Add Integration**, search for
   **Alpha FXM HP UPS**.

### Manual install

1. Copy the `custom_components/alpha_fxm_hp` folder from this package into
   your Home Assistant `config/custom_components/` folder, so you end up with:
   ```
   config/custom_components/alpha_fxm_hp/__init__.py
   config/custom_components/alpha_fxm_hp/manifest.json
   ...
   ```
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**, search for
   **Alpha FXM HP UPS**.
4. Enter a name, the host/IP, SNMP port (default 161), and pick SNMP version
   `v3`. On the next screen enter your username, auth protocol + password,
   and privacy protocol + password.
5. Repeat step 3 for every additional FXM HP unit — each one is added
   separately with its own IP and gets its own device/entities.

## Verifying SNMP before adding a unit

It's worth confirming the controller answers SNMP before configuring it in
Home Assistant. From any machine on the same network (with `net-snmp` tools
installed):

```bash
snmpget -v3 -l authPriv \
  -u YOUR_USERNAME \
  -a SHA -A YOUR_AUTH_PASSWORD \
  -x AES -X YOUR_PRIV_PASSWORD \
  <controller-ip> 1.3.6.1.2.1.33.1.1.2.0
```

That OID is `upsIdentModel` — if it returns a string back, the integration's
credentials/settings will work too. Adjust `-a`/`-x` to match whatever
auth/privacy protocol you configured on the controller.

## Diagnostics

Each device gets a diagnostic **Dump SNMP diagnostics** button
(`button.<name>_dump_snmp_diagnostics`). Pressing it walks the entire
UPS-MIB tree on that unit and writes the raw OID/value pairs to the Home
Assistant log (**Settings → System → Logs**, look for `alpha_fxm_hp`) at
warning level so it's visible without turning on debug logging. This is the
easiest way to see exactly which optional UPS-MIB fields your specific
firmware implements, and at what scale, without installing separate SNMP
command-line tools.

Not everything a UPS-MIB *could* expose is required to be implemented —
the standard defines "basic" and "advanced" conformance groups, and several
vendors (this one included, on some units) only implement the basic group.
`upsInputCurrent`, `upsInputTruePower`, and `upsOutputPercentLoad` are
advanced-only fields; if the dump shows `<NoSuchObject>` or `<NoSuchInstance>`
for those, your firmware just doesn't publish them over SNMP — that's a
device limitation, not something the integration can fix.

## Notes / troubleshooting

- **"Could not reach the UPS over SNMP"** during setup usually means: wrong
  IP/port, SNMP not enabled on the controller, a firewall blocking UDP/161,
  or mismatched SNMPv3 auth/priv protocol vs. what's configured on the unit.
- Bypass voltage/frequency sensors are disabled by default (many FXM HP
  configurations don't run a bypass line) — enable them from the entity list
  if your setup uses bypass.
- The integration reuses one SNMP engine per device and polls a handful of
  batched GET requests every interval (60s by default, adjustable in the
  integration's **Configure** options) rather than one request per value.
