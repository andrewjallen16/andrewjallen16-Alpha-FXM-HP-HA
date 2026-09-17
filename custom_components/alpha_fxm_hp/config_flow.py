"""Config flow for Alpha FXM HP UPS (SNMP)."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from . import snmp_client
from .const import (
    AUTH_PROTOCOLS,
    CONF_AUTH_KEY,
    CONF_AUTH_PROTOCOL,
    CONF_COMMUNITY,
    CONF_PRIV_KEY,
    CONF_PRIV_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_SNMP_VERSION,
    CONF_USERNAME,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    PRIV_PROTOCOLS,
    SNMP_V1,
    SNMP_V2C,
    SNMP_V3,
    SNMP_VERSIONS,
)

_LOGGER = logging.getLogger(__name__)


def _base_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required("name", default=defaults.get("name", DEFAULT_NAME)): str,
            vol.Required("host", default=defaults.get("host", "")): str,
            vol.Required("port", default=defaults.get("port", DEFAULT_PORT)): int,
            vol.Required(
                CONF_SNMP_VERSION, default=defaults.get(CONF_SNMP_VERSION, SNMP_V3)
            ): SelectSelector(
                SelectSelectorConfig(options=SNMP_VERSIONS, mode=SelectSelectorMode.DROPDOWN)
            ),
        }
    )


def _community_schema() -> vol.Schema:
    return vol.Schema({vol.Required(CONF_COMMUNITY, default="public"): str})


def _v3_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME): str,
            vol.Required(
                CONF_AUTH_PROTOCOL, default="sha"
            ): SelectSelector(
                SelectSelectorConfig(options=AUTH_PROTOCOLS, mode=SelectSelectorMode.DROPDOWN)
            ),
            vol.Optional(CONF_AUTH_KEY, default=""): str,
            vol.Required(
                CONF_PRIV_PROTOCOL, default="aes128"
            ): SelectSelector(
                SelectSelectorConfig(options=PRIV_PROTOCOLS, mode=SelectSelectorMode.DROPDOWN)
            ),
            vol.Optional(CONF_PRIV_KEY, default=""): str,
        }
    )


async def _async_test_connection(hass, data: dict[str, Any]) -> str | None:
    """Try one SNMP GET. Returns an error code string, or None on success."""
    try:
        auth_data = snmp_client.build_auth_data(data)
        engine = await snmp_client.async_create_engine(hass)
        await snmp_client.async_poll(hass, engine, auth_data, data["host"], data["port"])
    except snmp_client.SnmpConnectionError:
        _LOGGER.debug("SNMP connection test failed", exc_info=True)
        return "cannot_connect"
    except Exception:  # noqa: BLE001 - surface any unexpected failure as a form error
        _LOGGER.exception("Unexpected error testing Alpha FXM HP connection")
        return "unknown"
    return None


class AlphaFxmHpConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow. Each entry represents one FXM HP unit."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            if user_input[CONF_SNMP_VERSION] in (SNMP_V1, SNMP_V2C):
                return await self.async_step_community()
            return await self.async_step_v3()

        return self.async_show_form(step_id="user", data_schema=_base_schema(), errors=errors)

    async def async_step_community(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self._async_finish()

        return self.async_show_form(
            step_id="community", data_schema=_community_schema(), errors=errors
        )

    async def async_step_v3(self, user_input: dict[str, Any] | None = None) -> Any:
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_AUTH_PROTOCOL] == "none":
                user_input[CONF_AUTH_KEY] = ""
            elif not user_input.get(CONF_AUTH_KEY):
                errors[CONF_AUTH_KEY] = "auth_key_required"

            if user_input[CONF_PRIV_PROTOCOL] == "none":
                user_input[CONF_PRIV_KEY] = ""
            elif not user_input.get(CONF_PRIV_KEY) and not errors:
                errors[CONF_PRIV_KEY] = "priv_key_required"

            if not errors:
                self._data.update(user_input)
                return await self._async_finish()

        return self.async_show_form(step_id="v3", data_schema=_v3_schema(), errors=errors)

    async def _async_finish(self) -> Any:
        await self.async_set_unique_id(f"{self._data['host']}:{self._data['port']}")
        self._abort_if_unique_id_configured()

        error = await _async_test_connection(self.hass, self._data)
        if error:
            step_id = "community" if self._data[CONF_SNMP_VERSION] in (SNMP_V1, SNMP_V2C) else "v3"
            schema = _community_schema() if step_id == "community" else _v3_schema()
            return self.async_show_form(
                step_id=step_id, data_schema=schema, errors={"base": error}
            )

        return self.async_create_entry(title=self._data["name"], data=self._data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return AlphaFxmHpOptionsFlow()


class AlphaFxmHpOptionsFlow(OptionsFlow):
    """Options: polling interval only. Credentials are edited by re-adding."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL)
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
