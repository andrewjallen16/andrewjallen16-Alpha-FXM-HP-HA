"""Coordinator for a single Alpha FXM HP UPS SNMP endpoint."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import snmp_client
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AlphaFxmHpCoordinator(DataUpdateCoordinator[snmp_client.UpsData]):
    """Polls one Alpha FXM HP UPS over SNMP on a fixed interval."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.host: str = entry.data["host"]
        self.port: int = entry.data.get("port", 161)
        self._auth_data = snmp_client.build_auth_data(entry.data)
        self._engine = None

        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({self.host})",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def async_setup(self) -> None:
        """Create the SNMP engine (off the event loop) before first refresh."""
        self._engine = await snmp_client.async_create_engine(self.hass)

    async def _async_update_data(self) -> snmp_client.UpsData:
        if self._engine is None:
            await self.async_setup()
        try:
            return await snmp_client.async_poll(
                self.hass,
                self._engine,
                self._auth_data,
                self.host,
                self.port,
            )
        except snmp_client.SnmpConnectionError as err:
            raise UpdateFailed(f"Error communicating with {self.host}: {err}") from err
