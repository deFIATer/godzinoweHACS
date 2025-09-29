"""Data update coordinator for TGE ENEA integration."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CLASSIFICATION_TANIUTKO,
    CLASSIFICATION_NISKA,
    CLASSIFICATION_SREDNIA, 
    CLASSIFICATION_WYSOKA,
)

_LOGGER = logging.getLogger(__name__)


class TGEEneaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching TGE ENEA data from API."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        name: str,
        update_interval: timedelta,
        api_url: str,
    ) -> None:
        """Initialize the data update coordinator."""
        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
        )
        self.api_url = api_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from TGE ENEA API."""
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession()

            # Fetch current price data
            current_data = await self._fetch_current_data()
            
            # Fetch today's classified data
            today_data = await self._fetch_today_classified()
            
            # Combine data
            combined_data = {
                "current": current_data,
                "today": today_data,
                "last_updated": dt_util.utcnow(),
            }
            
            _LOGGER.debug("Successfully updated TGE ENEA data")
            return combined_data

        except Exception as err:
            _LOGGER.error("Error updating TGE ENEA data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def _fetch_current_data(self) -> Dict[str, Any]:
        """Fetch current hour price data."""
        url = f"{self.api_url}?action=current"
        
        try:
            async with async_timeout.timeout(30):
                async with self._session.get(url) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"API returned status {response.status}")
                    
                    data = await response.json()
                    if not data.get("success"):
                        raise UpdateFailed(f"API error: {data.get('error', 'Unknown error')}")
                    
                    return data.get("data", {})
        
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching current data: {err}")

    async def _fetch_today_classified(self) -> Dict[str, Any]:
        """Fetch today's classified price data."""
        url = f"{self.api_url}?action=today_classified"
        
        try:
            async with async_timeout.timeout(30):
                async with self._session.get(url) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"API returned status {response.status}")
                    
                    data = await response.json()
                    if not data.get("success"):
                        raise UpdateFailed(f"API error: {data.get('error', 'Unknown error')}")
                    
                    return data.get("data", {})
        
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching today's data: {err}")

    async def async_get_cheap_hours(
        self, hours_needed: int = 1, date: Optional[str] = None
    ) -> List[str]:
        """Get cheap hours for a specific date or today."""
        url = f"{self.api_url}?action=price_ranges"
        if date:
            url += f"&date={date}"
        
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession()
                
            async with async_timeout.timeout(30):
                async with self._session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"API returned status {response.status}")
                    
                    data = await response.json()
                    if not data.get("success"):
                        raise Exception(f"API error: {data.get('error', 'Unknown error')}")
                    
                    price_ranges = data.get("data", {}).get("price_ranges", {})
                    
                    # Get cheap hours (taniutko + low)
                    cheap_hours = []
                    
                    # Add taniutko hours first (highest priority)
                    taniutko_hours = price_ranges.get("taniutko", {}).get("hours", [])
                    for hour_data in taniutko_hours:
                        cheap_hours.append(hour_data.get("hour"))
                    
                    # Add low price hours if we need more
                    if len(cheap_hours) < hours_needed:
                        low_hours = price_ranges.get("low", {}).get("hours", [])
                        for hour_data in low_hours:
                            if len(cheap_hours) >= hours_needed:
                                break
                            hour = hour_data.get("hour")
                            if hour not in cheap_hours:
                                cheap_hours.append(hour)
                    
                    return cheap_hours[:hours_needed]
        
        except Exception as err:
            _LOGGER.error("Error getting cheap hours: %s", err)
            return []

    @property
    def current_price(self) -> Optional[float]:
        """Get current ENEA price."""
        if self.data and "current" in self.data:
            return self.data["current"].get("price_per_kwh_enea")
        return None

    @property
    def current_classification(self) -> Optional[str]:
        """Get current price classification."""
        if self.data and "current" in self.data:
            return self.data["current"].get("classification_enea")
        return None

    @property
    def tge_price(self) -> Optional[float]:
        """Get current TGE price."""
        if self.data and "current" in self.data:
            return self.data["current"].get("price_per_kwh")
        return None

    @property
    def is_cheap(self) -> bool:
        """Check if current price is cheap."""
        classification = self.current_classification
        return classification in [CLASSIFICATION_TANIUTKO, CLASSIFICATION_NISKA]

    @property
    def is_expensive(self) -> bool:
        """Check if current price is expensive."""
        classification = self.current_classification
        return classification == CLASSIFICATION_WYSOKA

    @property
    def cheap_hours_today(self) -> List[str]:
        """Get list of cheap hours today."""
        if self.data and "today" in self.data:
            summary = self.data["today"].get("summary", {})
            cheap_hours = []
            cheap_hours.extend(summary.get("taniutko_hours", []))
            cheap_hours.extend(summary.get("low_price_hours", []))
            return cheap_hours
        return []

    @property
    def expensive_hours_today(self) -> List[str]:
        """Get list of expensive hours today."""
        if self.data and "today" in self.data:
            summary = self.data["today"].get("summary", {})
            return summary.get("high_price_hours", [])
        return []

    async def async_close(self) -> None:
        """Close the session."""
        if self._session:
            await self._session.close()
            self._session = None