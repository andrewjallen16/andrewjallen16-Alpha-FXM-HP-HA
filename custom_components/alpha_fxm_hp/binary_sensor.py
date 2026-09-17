"""Binary sensor platform for Alpha FXM HP UPS."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AlphaFxmHpCoordinator
from .entity import AlphaFxmHpEntity

DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="on_battery",
        translation_key="on_battery",
        device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:battery-alert",
    ),
    BinarySensorEntityDescription(
        key="problem",
        translation_key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="on_bypass",
        translation_key="on_bypass",
        icon="mdi:transmission-tower-off",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors for one Alpha FXM HP UPS config entry."""
    coordinator: AlphaFxmHpCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AlphaFxmHpBinarySensor(coordinator, description) for description in DESCRIPTIONS
    )


class AlphaFxmHpBinarySensor(AlphaFxmHpEntity, BinarySensorEntity):
    """Derived boolean states from the polled UPS-MIB data."""

    def __init__(
        self, coordinator: AlphaFxmHpCoordinator, description: BinarySensorEntityDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        if data is None:
            return None
        if self.entity_description.key == "on_battery":
            return data.output_source == "battery"
        if self.entity_description.key == "on_bypass":
            return data.output_source == "bypass"
        if self.entity_description.key == "problem":
            return bool(data.alarms_present) or data.battery_status in ("low", "depleted")
        return None
