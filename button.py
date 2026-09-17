"""Diagnostic button for Alpha FXM HP UPS.

Presses trigger a full SNMP walk of the UPS-MIB subtree and log the raw
OID/value pairs, so a person can see exactly what their unit's SNMP agent
actually supports without needing to install net-snmp tools separately.
"""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import snmp_client
from .const import DOMAIN, OID_UPS_MIB_BASE
from .coordinator import AlphaFxmHpCoordinator
from .entity import AlphaFxmHpEntity

_LOGGER = logging.getLogger(__name__)

DESCRIPTION = ButtonEntityDescription(
    key="dump_snmp_data",
    translation_key="dump_snmp_data",
    entity_category=EntityCategory.DIAGNOSTIC,
    icon="mdi:file-search-outline",
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the diagnostic dump button for one Alpha FXM HP UPS."""
    coordinator: AlphaFxmHpCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AlphaFxmHpDumpButton(coordinator, DESCRIPTION)])


class AlphaFxmHpDumpButton(AlphaFxmHpEntity, ButtonEntity):
    """Walks the whole UPS-MIB tree on demand and logs the raw result."""

    def __init__(
        self, coordinator: AlphaFxmHpCoordinator, description: ButtonEntityDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        coordinator = self.coordinator
        if coordinator._engine is None:  # noqa: SLF001 - internal reuse within integration
            await coordinator.async_setup()

        try:
            results = await snmp_client.async_walk(
                coordinator.hass,
                coordinator._engine,  # noqa: SLF001
                coordinator._auth_data,  # noqa: SLF001
                coordinator.host,
                coordinator.port,
                OID_UPS_MIB_BASE,
            )
        except snmp_client.SnmpConnectionError as err:
            _LOGGER.error(
                "Alpha FXM HP (%s): SNMP walk failed: %s", coordinator.host, err
            )
            return

        if not results:
            _LOGGER.warning(
                "Alpha FXM HP (%s): SNMP walk returned no data at all under %s. "
                "Check that SNMP is enabled and the credentials/security level match.",
                coordinator.host,
                OID_UPS_MIB_BASE,
            )
            return

        lines = "\n".join(f"{oid} = {value}" for oid, value in results)
        _LOGGER.warning(
            "Alpha FXM HP (%s) full SNMP walk of %s (%d OIDs):\n%s",
            coordinator.host,
            OID_UPS_MIB_BASE,
            len(results),
            lines,
        )
