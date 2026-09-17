"""Thin async wrapper around pysnmp for polling Alpha FXM HP UPS-MIB data.

The Alpha FXM HP does not publish a Modbus register map; its only network
monitoring interface is SNMP, implementing the standard UPS-MIB (RFC 1628)
plus a proprietary Alpha Resource MIB. This client only relies on the
standard UPS-MIB, which the Alpha FXM HP documentation explicitly states
the unit implements, so it works across firmware/model revisions without
needing the proprietary MIB compiled in.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    AUTH_PROTOCOL_MD5,
    AUTH_PROTOCOL_NONE,
    AUTH_PROTOCOL_SHA,
    AUTH_PROTOCOL_SHA224,
    AUTH_PROTOCOL_SHA256,
    AUTH_PROTOCOL_SHA384,
    AUTH_PROTOCOL_SHA512,
    BATTERY_STATUS_MAP,
    OID_ALARMS_PRESENT,
    OID_BATTERY_CURRENT,
    OID_BATTERY_STATUS,
    OID_BATTERY_TEMPERATURE,
    OID_BATTERY_VOLTAGE,
    OID_BYPASS_FREQUENCY,
    OID_BYPASS_VOLTAGE,
    OID_ESTIMATED_CHARGE_REMAINING,
    OID_ESTIMATED_MINUTES_REMAINING,
    OID_IDENT_MANUFACTURER,
    OID_IDENT_MODEL,
    OID_IDENT_NAME,
    OID_IDENT_UPS_SOFTWARE_VERSION,
    OID_INPUT_CURRENT,
    OID_INPUT_FREQUENCY,
    OID_INPUT_LINE_BADS,
    OID_INPUT_TRUE_POWER,
    OID_INPUT_VOLTAGE,
    OID_OUTPUT_CURRENT,
    OID_OUTPUT_FREQUENCY,
    OID_OUTPUT_PERCENT_LOAD,
    OID_OUTPUT_POWER,
    OID_OUTPUT_SOURCE,
    OID_OUTPUT_VOLTAGE,
    OID_SECONDS_ON_BATTERY,
    OUTPUT_SOURCE_MAP,
    PRIV_PROTOCOL_3DES,
    PRIV_PROTOCOL_AES128,
    PRIV_PROTOCOL_AES192,
    PRIV_PROTOCOL_AES256,
    PRIV_PROTOCOL_DES,
    PRIV_PROTOCOL_NONE,
    SNMP_V1,
    SNMP_V2C,
)

_LOGGER = logging.getLogger(__name__)

# All scalar OIDs we care about, grouped into batches. Grouping keeps each
# SNMP GET request comfortably under typical UDP payload limits while still
# minimising the number of round trips per poll.
_IDENTITY_OIDS = [
    OID_IDENT_MANUFACTURER,
    OID_IDENT_MODEL,
    OID_IDENT_UPS_SOFTWARE_VERSION,
    OID_IDENT_NAME,
]

_BATTERY_OIDS = [
    OID_BATTERY_STATUS,
    OID_SECONDS_ON_BATTERY,
    OID_ESTIMATED_MINUTES_REMAINING,
    OID_ESTIMATED_CHARGE_REMAINING,
    OID_BATTERY_VOLTAGE,
    OID_BATTERY_CURRENT,
    OID_BATTERY_TEMPERATURE,
]

_INPUT_OUTPUT_OIDS = [
    OID_INPUT_LINE_BADS,
    OID_INPUT_FREQUENCY,
    OID_INPUT_VOLTAGE,
    OID_INPUT_CURRENT,
    OID_INPUT_TRUE_POWER,
    OID_OUTPUT_SOURCE,
    OID_OUTPUT_FREQUENCY,
    OID_OUTPUT_VOLTAGE,
    OID_OUTPUT_CURRENT,
    OID_OUTPUT_POWER,
    OID_OUTPUT_PERCENT_LOAD,
]

_BYPASS_ALARM_OIDS = [
    OID_BYPASS_FREQUENCY,
    OID_BYPASS_VOLTAGE,
    OID_ALARMS_PRESENT,
]

ALL_OID_BATCHES = [_IDENTITY_OIDS, _BATTERY_OIDS, _INPUT_OUTPUT_OIDS, _BYPASS_ALARM_OIDS]


class SnmpConnectionError(HomeAssistantError):
    """Raised when the UPS cannot be reached or credentials are rejected."""


@dataclass
class UpsData:
    """Parsed, typed snapshot of one poll."""

    manufacturer: str | None = None
    model: str | None = None
    software_version: str | None = None
    name: str | None = None

    battery_status: str | None = None
    seconds_on_battery: int | None = None
    minutes_remaining: int | None = None
    charge_remaining: int | None = None
    battery_voltage: float | None = None
    battery_current: float | None = None
    battery_temperature: int | None = None

    input_line_bads: int | None = None
    input_frequency: float | None = None
    input_voltage: int | None = None
    input_current: float | None = None
    input_true_power: int | None = None

    output_source: str | None = None
    output_frequency: float | None = None
    output_voltage: int | None = None
    output_current: float | None = None
    output_power: int | None = None
    output_percent_load: int | None = None

    bypass_frequency: float | None = None
    bypass_voltage: int | None = None

    alarms_present: int | None = None

    raw: dict[str, Any] = field(default_factory=dict)


def _resolve_auth_protocol(name: str):
    """Map a config string to a pysnmp auth protocol object."""
    from pysnmp.hlapi.v3arch.asyncio import (
        usmHMACMD5AuthProtocol,
        usmHMACSHAAuthProtocol,
        usmHMAC128SHA224AuthProtocol,
        usmHMAC192SHA256AuthProtocol,
        usmHMAC256SHA384AuthProtocol,
        usmHMAC384SHA512AuthProtocol,
        usmNoAuthProtocol,
    )

    return {
        AUTH_PROTOCOL_NONE: usmNoAuthProtocol,
        AUTH_PROTOCOL_MD5: usmHMACMD5AuthProtocol,
        AUTH_PROTOCOL_SHA: usmHMACSHAAuthProtocol,
        AUTH_PROTOCOL_SHA224: usmHMAC128SHA224AuthProtocol,
        AUTH_PROTOCOL_SHA256: usmHMAC192SHA256AuthProtocol,
        AUTH_PROTOCOL_SHA384: usmHMAC256SHA384AuthProtocol,
        AUTH_PROTOCOL_SHA512: usmHMAC384SHA512AuthProtocol,
    }[name]


def _resolve_priv_protocol(name: str):
    """Map a config string to a pysnmp privacy protocol object."""
    from pysnmp.hlapi.v3arch.asyncio import (
        usm3DESEDEPrivProtocol,
        usmAesCfb128Protocol,
        usmAesCfb192Protocol,
        usmAesCfb256Protocol,
        usmDESPrivProtocol,
        usmNoPrivProtocol,
    )

    return {
        PRIV_PROTOCOL_NONE: usmNoPrivProtocol,
        PRIV_PROTOCOL_DES: usmDESPrivProtocol,
        PRIV_PROTOCOL_3DES: usm3DESEDEPrivProtocol,
        PRIV_PROTOCOL_AES128: usmAesCfb128Protocol,
        PRIV_PROTOCOL_AES192: usmAesCfb192Protocol,
        PRIV_PROTOCOL_AES256: usmAesCfb256Protocol,
    }[name]


def build_auth_data(config: dict[str, Any]):
    """Build a pysnmp CommunityData/UsmUserData object from stored config."""
    from pysnmp.hlapi.v3arch.asyncio import CommunityData, UsmUserData

    version = config["snmp_version"]

    if version == SNMP_V1:
        return CommunityData(config["community"], mpModel=0)
    if version == SNMP_V2C:
        return CommunityData(config["community"], mpModel=1)

    # SNMPv3
    auth_protocol_name = config.get("auth_protocol", AUTH_PROTOCOL_NONE)
    priv_protocol_name = config.get("priv_protocol", PRIV_PROTOCOL_NONE)
    auth_key = config.get("auth_key") or None
    priv_key = config.get("priv_key") or None

    kwargs: dict[str, Any] = {}
    if auth_protocol_name != AUTH_PROTOCOL_NONE and auth_key:
        kwargs["authKey"] = auth_key
        kwargs["authProtocol"] = _resolve_auth_protocol(auth_protocol_name)
        if priv_protocol_name != PRIV_PROTOCOL_NONE and priv_key:
            kwargs["privKey"] = priv_key
            kwargs["privProtocol"] = _resolve_priv_protocol(priv_protocol_name)

    return UsmUserData(config["username"], **kwargs)


def _create_engine():
    """Create a pysnmp SnmpEngine.

    This does blocking file I/O the first time it runs (MIB builder paths),
    so callers must invoke this via hass.async_add_executor_job.
    """
    from pysnmp.hlapi.v3arch.asyncio import SnmpEngine

    return SnmpEngine()


async def async_create_engine(hass: HomeAssistant):
    """Create the SNMP engine off the event loop."""
    return await hass.async_add_executor_job(_create_engine)


def _decode_value(value: Any) -> Any:
    """Convert a pysnmp value object into a plain Python int/str."""
    type_name = type(value).__name__
    if type_name in ("NoSuchInstance", "NoSuchObject", "NoSuchInstanceOrObject"):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        text = str(value).strip()
        return text or None


async def _async_get_batch(
    hass: HomeAssistant,
    engine,
    auth_data,
    host: str,
    port: int,
    oids: list[str],
    timeout: float,
    retries: int,
) -> dict[str, Any]:
    from pysnmp.hlapi.v3arch.asyncio import (
        ContextData,
        ObjectIdentity,
        ObjectType,
        UdpTransportTarget,
        get_cmd,
    )

    transport = await UdpTransportTarget.create(
        (host, port), timeout=timeout, retries=retries
    )
    var_binds = [ObjectType(ObjectIdentity(oid)) for oid in oids]

    error_indication, error_status, error_index, response_var_binds = await get_cmd(
        engine,
        auth_data,
        transport,
        ContextData(),
        *var_binds,
    )

    if error_indication:
        raise SnmpConnectionError(str(error_indication))
    if error_status:
        # errorStatus can legitimately fire on some devices if a single OID
        # in the batch is unsupported (e.g. no bypass line). Log and continue
        # with whatever came back rather than failing the whole poll.
        _LOGGER.debug(
            "SNMP errorStatus %s from %s at index %s",
            error_status.prettyPrint(),
            host,
            error_index,
        )

    result: dict[str, Any] = {}
    for oid, var_bind in zip(oids, response_var_binds):
        result[oid] = _decode_value(var_bind[1])
    return result


def _diagnostic_repr(value: Any) -> str:
    """Human-readable representation for the diagnostic walk (keeps type info)."""
    type_name = type(value).__name__
    if type_name in ("NoSuchInstance", "NoSuchObject", "NoSuchInstanceOrObject"):
        return f"<{type_name}>"
    return f"{value.prettyPrint()} (SNMP type: {type_name})"


async def async_walk(
    hass: HomeAssistant,
    engine,
    auth_data,
    host: str,
    port: int,
    base_oid: str,
    timeout: float = 5.0,
    retries: int = 1,
) -> list[tuple[str, Any]]:
    """Walk an entire OID subtree and return (oid, value) pairs in order.

    Used only by the diagnostic "Dump SNMP data" button, so a person can see
    exactly what their specific unit's SNMP agent actually implements
    without needing external tools like net-snmp installed.
    """
    from pysnmp.hlapi.v3arch.asyncio import (
        ContextData,
        ObjectIdentity,
        ObjectType,
        UdpTransportTarget,
        walk_cmd,
    )

    transport = await UdpTransportTarget.create(
        (host, port), timeout=timeout, retries=retries
    )

    results: list[tuple[str, Any]] = []
    async for error_indication, error_status, error_index, var_binds in walk_cmd(
        engine,
        auth_data,
        transport,
        ContextData(),
        ObjectType(ObjectIdentity(base_oid)),
        lexicographicMode=False,
    ):
        if error_indication:
            raise SnmpConnectionError(str(error_indication))
        if error_status:
            _LOGGER.debug(
                "SNMP walk errorStatus %s from %s at index %s",
                error_status.prettyPrint(),
                host,
                error_index,
            )
            break
        for oid, value in var_binds:
            results.append((str(oid), _diagnostic_repr(value)))
    return results


async def async_poll(
    hass: HomeAssistant,
    engine,
    auth_data,
    host: str,
    port: int,
    timeout: float = 5.0,
    retries: int = 1,
) -> UpsData:
    """Poll all OID batches and return a parsed UpsData snapshot."""
    raw: dict[str, Any] = {}
    for batch in ALL_OID_BATCHES:
        batch_result = await _async_get_batch(
            hass, engine, auth_data, host, port, batch, timeout, retries
        )
        raw.update(batch_result)

    def _scaled(oid: str, factor: float = 1.0) -> float | None:
        value = raw.get(oid)
        return None if value is None else round(value * factor, 2)

    def _enum(oid: str, mapping: dict[int, str]) -> str | None:
        value = raw.get(oid)
        return None if value is None else mapping.get(value, f"unknown ({value})")

    return UpsData(
        manufacturer=raw.get(OID_IDENT_MANUFACTURER),
        model=raw.get(OID_IDENT_MODEL),
        software_version=raw.get(OID_IDENT_UPS_SOFTWARE_VERSION),
        name=raw.get(OID_IDENT_NAME),
        battery_status=_enum(OID_BATTERY_STATUS, BATTERY_STATUS_MAP),
        seconds_on_battery=raw.get(OID_SECONDS_ON_BATTERY),
        minutes_remaining=raw.get(OID_ESTIMATED_MINUTES_REMAINING),
        charge_remaining=raw.get(OID_ESTIMATED_CHARGE_REMAINING),
        battery_voltage=_scaled(OID_BATTERY_VOLTAGE, 0.1),
        battery_current=_scaled(OID_BATTERY_CURRENT, 0.1),
        battery_temperature=raw.get(OID_BATTERY_TEMPERATURE),
        input_line_bads=raw.get(OID_INPUT_LINE_BADS),
        input_frequency=_scaled(OID_INPUT_FREQUENCY, 0.1),
        input_voltage=raw.get(OID_INPUT_VOLTAGE),
        input_current=_scaled(OID_INPUT_CURRENT, 0.1),
        input_true_power=raw.get(OID_INPUT_TRUE_POWER),
        output_source=_enum(OID_OUTPUT_SOURCE, OUTPUT_SOURCE_MAP),
        output_frequency=_scaled(OID_OUTPUT_FREQUENCY, 0.1),
        output_voltage=raw.get(OID_OUTPUT_VOLTAGE),
        output_current=_scaled(OID_OUTPUT_CURRENT, 0.1),
        output_power=raw.get(OID_OUTPUT_POWER),
        output_percent_load=raw.get(OID_OUTPUT_PERCENT_LOAD),
        bypass_frequency=_scaled(OID_BYPASS_FREQUENCY, 0.1),
        bypass_voltage=raw.get(OID_BYPASS_VOLTAGE),
        alarms_present=raw.get(OID_ALARMS_PRESENT),
        raw=raw,
    )
