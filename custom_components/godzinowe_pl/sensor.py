"""Sensor platform for godzinowe.pl integration."""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_TYPES,
    ATTR_CURRENT_HOUR_RANGE,
    ATTR_DATE,
    ATTR_CLASSIFICATION,
    ATTR_VOLUME,
    ATTR_CHEAP_HOURS,
    ATTR_EXPENSIVE_HOURS,
    ATTR_THRESHOLDS,
    ATTR_STATISTICS,
    ATTR_AVAILABLE,
    ATTR_CHEAPEST_HOURS,
    ATTR_COMPLETENESS,
    ATTR_MARKET_PRICE_GROSS,
    ATTR_MESSAGE,
    ATTR_MOST_EXPENSIVE_HOURS,
    ATTR_RECORDS,
    ATTR_TARIFF_OPTIONS,
    ATTR_TARIFF_RATE,
    ATTR_TOTAL_PRICE,
)
from .coordinator import GodzinowePLDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up godzinowe.pl sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(GodzinowePLSensor(coordinator, sensor_type))

    async_add_entities(entities, True)


class GodzinowePLSensor(CoordinatorEntity, SensorEntity):
    """Representation of a godzinowe.pl sensor."""

    def __init__(
        self,
        coordinator: GodzinowePLDataUpdateCoordinator,
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

        elif self._sensor_type == "current_total_price":
            return self.coordinator.current_total_price
            
        elif self._sensor_type == "current_classification":
            return self.coordinator.current_classification
            
        elif self._sensor_type == "tge_price":
            return self.coordinator.tge_price
            
        elif self._sensor_type == "cheap_hours_count":
            return len(self.coordinator.cheap_hours_today)
            
        elif self._sensor_type == "expensive_hours_count":
            return len(self.coordinator.expensive_hours_today)

        elif self._sensor_type == "tomorrow_cheap_hours_count":
            return len(self.coordinator.cheap_hours_tomorrow)

        elif self._sensor_type == "tomorrow_expensive_hours_count":
            return len(self.coordinator.expensive_hours_tomorrow)

        elif self._sensor_type == "today_schedule":
            return "available" if self.coordinator.day_payload("today").get("available") else "unavailable"

        elif self._sensor_type == "tomorrow_schedule":
            return "available" if self.coordinator.day_payload("tomorrow").get("available") else "unavailable"
        
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        attributes = {}
        
        if not self.coordinator.data:
            return attributes
        
        current_data = self.coordinator.data.get("current", {})
        today_data = self.coordinator.data.get("today", {})
        tomorrow_data = self.coordinator.data.get("tomorrow", {})
        
        # Add common attributes
        if current_data:
            attributes[ATTR_CURRENT_HOUR_RANGE] = current_data.get("current_hour_range")
            attributes[ATTR_DATE] = current_data.get("date")
            attributes[ATTR_CLASSIFICATION] = current_data.get("classification")
            attributes[ATTR_VOLUME] = current_data.get("volume")
            attributes[ATTR_MARKET_PRICE_GROSS] = current_data.get("market_price_gross")
            attributes[ATTR_TARIFF_RATE] = current_data.get("tariff_rate")
            attributes[ATTR_TOTAL_PRICE] = current_data.get("total_price")
        
        # Sensor-specific attributes
        if self._sensor_type in ["current_price", "current_total_price"]:
            if current_data:
                attributes["tge_price"] = current_data.get("price")
                attributes["tge_price_per_kwh"] = current_data.get("price_per_kwh")
                attributes[ATTR_TARIFF_OPTIONS] = self.coordinator.data.get("tariff_options", {})
                
        elif self._sensor_type in ["cheap_hours_count", "expensive_hours_count"]:
            if today_data:
                summary = today_data.get("summary", {})
                attributes[ATTR_CHEAP_HOURS] = (
                    summary.get("negative_hours", []) +
                    summary.get("zero_hours", []) +
                    summary.get("very_low_price_hours", []) +
                    summary.get("low_price_hours", []) +
                    summary.get("taniutko_hours", [])
                )
                attributes[ATTR_EXPENSIVE_HOURS] = (
                    summary.get("high_price_hours", []) +
                    summary.get("very_high_price_hours", []) +
                    summary.get("extreme_price_hours", [])
                )
                attributes[ATTR_THRESHOLDS] = summary.get("thresholds", {}) or summary.get("thresholds_enea", {})
                attributes[ATTR_STATISTICS] = today_data.get("statistics", {})

        elif self._sensor_type in ["tomorrow_cheap_hours_count", "tomorrow_expensive_hours_count"]:
            if tomorrow_data:
                summary = tomorrow_data.get("summary", {})
                attributes[ATTR_AVAILABLE] = tomorrow_data.get("available")
                attributes[ATTR_MESSAGE] = tomorrow_data.get("message")
                attributes[ATTR_CHEAP_HOURS] = self.coordinator.cheap_hours_tomorrow
                attributes[ATTR_EXPENSIVE_HOURS] = self.coordinator.expensive_hours_tomorrow
                attributes[ATTR_THRESHOLDS] = summary.get("thresholds", {})
                attributes[ATTR_STATISTICS] = tomorrow_data.get("statistics", {})

        elif self._sensor_type == "today_schedule":
            attributes.update(self._day_attributes("today", today_data))

        elif self._sensor_type == "tomorrow_schedule":
            attributes.update(self._day_attributes("tomorrow", tomorrow_data))
        
        return attributes

    def _day_attributes(self, day_key: str, day_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return attributes for a full-day schedule sensor."""
        if not day_data:
            return {}

        summary = day_data.get("summary", {})
        return {
            ATTR_DATE: day_data.get("date"),
            ATTR_AVAILABLE: day_data.get("available"),
            ATTR_MESSAGE: day_data.get("message"),
            ATTR_RECORDS: day_data.get("records", []),
            ATTR_CHEAP_HOURS: self.coordinator.cheap_hours_for_day(day_key),
            ATTR_EXPENSIVE_HOURS: self.coordinator.expensive_hours_for_day(day_key),
            ATTR_CHEAPEST_HOURS: self.coordinator.ranked_hours(day_key, reverse=False),
            ATTR_MOST_EXPENSIVE_HOURS: self.coordinator.ranked_hours(day_key, reverse=True),
            ATTR_THRESHOLDS: summary.get("thresholds", {}),
            ATTR_STATISTICS: day_data.get("statistics", {}),
            "total_price_statistics": day_data.get("total_price_statistics", {}),
            ATTR_COMPLETENESS: day_data.get("completeness", {}),
            "classification_legend": day_data.get("classification_legend", []),
            ATTR_TARIFF_OPTIONS: self.coordinator.data.get("tariff_options", {}),
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
