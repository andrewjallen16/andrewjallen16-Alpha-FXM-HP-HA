"""Shared base entity for Alpha FXM HP entities."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AlphaFxmHpCoordinator


class AlphaFxmHpEntity(CoordinatorEntity[AlphaFxmHpCoordinator]):
    """Base entity tying a sensor/binary_sensor to one UPS device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AlphaFxmHpCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data
        model = data.model if data else None
        manufacturer = data.manufacturer if data else None
        sw_version = data.software_version if data else None
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=self.coordinator.entry.title,
            manufacturer=manufacturer or "Alpha Technologies",
            model=model or "FXM HP",
            sw_version=sw_version,
            configuration_url=f"http://{self.coordinator.host}/",
        )
