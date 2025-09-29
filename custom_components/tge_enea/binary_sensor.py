"""Binary sensor platform for TGE ENEA integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    BINARY_SENSOR_TYPES,
    ATTR_CURRENT_HOUR_RANGE,
    ATTR_DATE,
    ATTR_CLASSIFICATION_ENEA,
    ATTR_CHEAP_HOURS,
    ATTR_EXPENSIVE_HOURS,
)
from .coordinator import TGEEneaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TGE ENEA binary sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for sensor_type in BINARY_SENSOR_TYPES:
        entities.append(TGEEneaBinarySensor(coordinator, sensor_type))

    async_add_entities(entities, True)


class TGEEneaBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a TGE ENEA binary sensor."""

    def __init__(
        self,
        coordinator: TGEEneaDataUpdateCoordinator,
        sensor_type: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._sensor_config = BINARY_SENSOR_TYPES[sensor_type]
        
        # Entity identification
        self._attr_unique_id = f"{DOMAIN}_{sensor_type}"
        self._attr_name = self._sensor_config["name"]
        self._attr_icon = self._sensor_config.get("icon")
        
        # Device class
        device_class = self._sensor_config.get("device_class")
        if device_class:
            self._attr_device_class = getattr(BinarySensorDeviceClass, device_class.upper())

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if self._sensor_type == "is_cheap":
            return self.coordinator.is_cheap
            
        elif self._sensor_type == "is_expensive":
            return self.coordinator.is_expensive
        
        return False

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        attributes = {}
        
        if not self.coordinator.data:
            return attributes
        
        current_data = self.coordinator.data.get("current", {})
        
        # Add common attributes
        if current_data:
            attributes[ATTR_CURRENT_HOUR_RANGE] = current_data.get("current_hour_range")
            attributes[ATTR_DATE] = current_data.get("date")
            attributes[ATTR_CLASSIFICATION_ENEA] = current_data.get("classification_enea")
            attributes["current_price"] = current_data.get("price_per_kwh_enea")
        
        # Add cheap/expensive hours for context
        attributes[ATTR_CHEAP_HOURS] = self.coordinator.cheap_hours_today
        attributes[ATTR_EXPENSIVE_HOURS] = self.coordinator.expensive_hours_today
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success