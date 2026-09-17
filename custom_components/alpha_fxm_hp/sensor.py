"""Sensor platform for Alpha FXM HP UPS."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AlphaFxmHpCoordinator
from .entity import AlphaFxmHpEntity


@dataclass(frozen=True, kw_only=True)
class AlphaFxmHpSensorDescription(SensorEntityDescription):
    """Sensor description that also points at a UpsData attribute."""

    value_key: str = ""


SENSOR_DESCRIPTIONS: tuple[AlphaFxmHpSensorDescription, ...] = (
    AlphaFxmHpSensorDescription(
        key="battery_status",
        value_key="battery_status",
        translation_key="battery_status",
        icon="mdi:battery-heart-variant",
    ),
    AlphaFxmHpSensorDescription(
        key="charge_remaining",
        value_key="charge_remaining",
        translation_key="charge_remaining",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AlphaFxmHpSensorDescription(
        key="minutes_remaining",
        value_key="minutes_remaining",
        translation_key="minutes_remaining",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-sand",
    ),
    AlphaFxmHpSensorDescription(
        key="seconds_on_battery",
        value_key="seconds_on_battery",
        translation_key="seconds_on_battery",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:timer-outline",
    ),
    AlphaFxmHpSensorDescription(
        key="battery_voltage",
        value_key="battery_voltage",
        translation_key="battery_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AlphaFxmHpSensorDescription(
        key="battery_current",
        value_key="battery_current",
        translation_key="battery_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AlphaFxmHpSensorDescription(
        key="battery_temperature",
        value_key="battery_temperature",
        translation_key="battery_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AlphaFxmHpSensorDescription(
        key="input_voltage",
        value_key="input_voltage",
        translation_key="input_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AlphaFxmHpSensorDescription(
        key="input_frequency",
        value_key="input_frequency",
        translation_key="input_frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AlphaFxmHpSensorDescription(
        key="input_current",
        value_key="input_current",
        translation_key="input_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AlphaFxmHpSensorDescription(
        key="input_true_power",
        value_key="input_true_power",
        translation_key="input_true_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AlphaFxmHpSensorDescription(
        key="input_line_bads",
        value_key="input_line_bads",
        translation_key="input_line_bads",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert-octagon-outline",
    ),
    AlphaFxmHpSensorDescription(
        key="output_source",
        value_key="output_source",
        translation_key="output_source",
        icon="mdi:transmission-tower",
    ),
    AlphaFxmHpSensorDescription(
        key="output_voltage",
        value_key="output_voltage",
        translation_key="output_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AlphaFxmHpSensorDescription(
        key="output_frequency",
        value_key="output_frequency",
        translation_key="output_frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AlphaFxmHpSensorDescription(
        key="output_current",
        value_key="output_current",
        translation_key="output_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AlphaFxmHpSensorDescription(
        key="output_power",
        value_key="output_power",
        translation_key="output_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AlphaFxmHpSensorDescription(
        key="output_percent_load",
        value_key="output_percent_load",
        translation_key="output_percent_load",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
    ),
    AlphaFxmHpSensorDescription(
        key="bypass_voltage",
        value_key="bypass_voltage",
        translation_key="bypass_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AlphaFxmHpSensorDescription(
        key="bypass_frequency",
        value_key="bypass_frequency",
        translation_key="bypass_frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AlphaFxmHpSensorDescription(
        key="alarms_present",
        value_key="alarms_present",
        translation_key="alarms_present",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:alert-circle-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors for one Alpha FXM HP UPS config entry."""
    coordinator: AlphaFxmHpCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AlphaFxmHpSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS
    )


class AlphaFxmHpSensor(AlphaFxmHpEntity, SensorEntity):
    """A single UPS-MIB derived measurement."""

    entity_description: AlphaFxmHpSensorDescription

    def __init__(
        self, coordinator: AlphaFxmHpCoordinator, description: AlphaFxmHpSensorDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        return getattr(self.coordinator.data, self.entity_description.value_key, None)
