"""Sensor platform for TGE ENEA integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_TYPES,
    ATTR_CURRENT_HOUR_RANGE,
    ATTR_DATE,
    ATTR_CLASSIFICATION_TGE,
    ATTR_CLASSIFICATION_ENEA,
    ATTR_VOLUME,
    ATTR_CHEAP_HOURS,
    ATTR_EXPENSIVE_HOURS,
    ATTR_THRESHOLDS,
    ATTR_STATISTICS,
)
from .coordinator import TGEEneaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TGE ENEA sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(TGEEneaSensor(coordinator, sensor_type))

    async_add_entities(entities, True)


class TGEEneaSensor(CoordinatorEntity, SensorEntity):
    """Representation of a TGE ENEA sensor."""

    def __init__(
        self,
        coordinator: TGEEneaDataUpdateCoordinator,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._sensor_config = SENSOR_TYPES[sensor_type]
        
        # Entity identification
        self._attr_unique_id = f"{DOMAIN}_{sensor_type}"
        self._attr_name = self._sensor_config["name"]
        self._attr_icon = self._sensor_config.get("icon")
        
        # Device class and units
        device_class = self._sensor_config.get("device_class")
        if device_class:
            self._attr_device_class = getattr(SensorDeviceClass, device_class.upper())
        
        state_class = self._sensor_config.get("state_class")
        if state_class:
            self._attr_state_class = getattr(SensorStateClass, state_class.upper())
        
        self._attr_native_unit_of_measurement = self._sensor_config.get("unit")

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self._sensor_type == "current_price":
            return self.coordinator.current_price
            
        elif self._sensor_type == "current_classification":
            return self.coordinator.current_classification
            
        elif self._sensor_type == "tge_price":
            return self.coordinator.tge_price
            
        elif self._sensor_type == "cheap_hours_count":
            return len(self.coordinator.cheap_hours_today)
            
        elif self._sensor_type == "expensive_hours_count":
            return len(self.coordinator.expensive_hours_today)
        
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        attributes = {}
        
        if not self.coordinator.data:
            return attributes
        
        current_data = self.coordinator.data.get("current", {})
        today_data = self.coordinator.data.get("today", {})
        
        # Add common attributes
        if current_data:
            attributes[ATTR_CURRENT_HOUR_RANGE] = current_data.get("current_hour_range")
            attributes[ATTR_DATE] = current_data.get("date")
            attributes[ATTR_CLASSIFICATION_TGE] = current_data.get("classification_tge")
            attributes[ATTR_CLASSIFICATION_ENEA] = current_data.get("classification_enea")
            attributes[ATTR_VOLUME] = current_data.get("volume")
        
        # Sensor-specific attributes
        if self._sensor_type == "current_price":
            if current_data:
                attributes["tge_price"] = current_data.get("price")
                attributes["tge_price_per_kwh"] = current_data.get("price_per_kwh")
                
        elif self._sensor_type in ["cheap_hours_count", "expensive_hours_count"]:
            if today_data:
                summary = today_data.get("summary", {})
                attributes[ATTR_CHEAP_HOURS] = (
                    summary.get("taniutko_hours", []) + 
                    summary.get("low_price_hours", [])
                )
                attributes[ATTR_EXPENSIVE_HOURS] = summary.get("high_price_hours", [])
                attributes[ATTR_THRESHOLDS] = summary.get("thresholds_enea", {})
                attributes[ATTR_STATISTICS] = today_data.get("statistics", {})
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success