"""The TGE ENEA integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    UPDATE_INTERVAL_CURRENT,
    SERVICE_UPDATE_PRICES,
    SERVICE_GET_CHEAP_HOURS,
)
from .coordinator import TGEEneaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TGE ENEA from a config entry."""
    _LOGGER.debug("Setting up TGE ENEA integration")

    # Create data update coordinator
    coordinator = TGEEneaDataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=UPDATE_INTERVAL_CURRENT),
        api_url=entry.data.get("api_url", "https://godzinowe.pl/api"),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await _async_register_services(hass, coordinator)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading TGE ENEA integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _async_register_services(
    hass: HomeAssistant, coordinator: TGEEneaDataUpdateCoordinator
) -> None:
    """Register services for the integration."""

    async def update_prices_service(call):
        """Service to manually update prices."""
        await coordinator.async_request_refresh()

    async def get_cheap_hours_service(call):
        """Service to get cheap hours for planning."""
        hours_needed = call.data.get("hours_needed", 1)
        date = call.data.get("date")
        
        try:
            cheap_hours = await coordinator.async_get_cheap_hours(hours_needed, date)
            hass.bus.async_fire(
                f"{DOMAIN}_cheap_hours_response",
                {
                    "hours_needed": hours_needed,
                    "date": date,
                    "cheap_hours": cheap_hours,
                }
            )
        except Exception as err:
            _LOGGER.error("Error getting cheap hours: %s", err)

    # Register services
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_PRICES, update_prices_service
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_GET_CHEAP_HOURS, get_cheap_hours_service
    )