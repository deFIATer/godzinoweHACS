"""Data update coordinator for godzinowe.pl integration."""
import logging
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CLASSIFICATION_UJEMNA,
    CLASSIFICATION_ZERO,
    CLASSIFICATION_BARDZO_NISKA,
    CLASSIFICATION_NISKA,
    CLASSIFICATION_SREDNIA,
    CLASSIFICATION_WYSOKA,
    CLASSIFICATION_BARDZO_WYSOKA,
    CLASSIFICATION_EKSTREMALNA,
    CONF_FIXED_RATE,
    CONF_G11_RATE,
    CONF_G12_DAY_END,
    CONF_G12_DAY_RATE,
    CONF_G12_DAY_START,
    CONF_G12_NIGHT_END,
    CONF_G12_NIGHT_RATE,
    CONF_G12_NIGHT_START,
    CONF_G13_AFTERNOON_RATE,
    CONF_G13_MORNING_RATE,
    CONF_G13_OFFPEAK_RATE,
    CONF_MARKET_VAT_MULTIPLIER,
    CONF_TARIFF_TYPE,
    DEFAULT_TARIFF_OPTIONS,
    TARIFF_G11,
    TARIFF_G12,
    TARIFF_G12W,
    TARIFF_G13,
)

_LOGGER = logging.getLogger(__name__)


class GodzinowePLDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching godzinowe.pl data from API."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        name: str,
        update_interval: timedelta,
        api_url: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the data update coordinator."""
        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
        )
        self.api_url = api_url
        self.options = self._normalize_options(options or {})
        self._session: Optional[aiohttp.ClientSession] = None

    def update_options(self, options: Dict[str, Any]) -> None:
        """Update tariff options used for calculated prices."""
        self.options = self._normalize_options(options)

    def _normalize_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Return options merged with defaults and coerced to useful types."""
        normalized = dict(DEFAULT_TARIFF_OPTIONS)
        normalized.update(options or {})

        for key in [
            CONF_MARKET_VAT_MULTIPLIER,
            CONF_FIXED_RATE,
            CONF_G11_RATE,
            CONF_G12_DAY_RATE,
            CONF_G12_NIGHT_RATE,
            CONF_G13_MORNING_RATE,
            CONF_G13_AFTERNOON_RATE,
            CONF_G13_OFFPEAK_RATE,
        ]:
            normalized[key] = float(normalized.get(key, DEFAULT_TARIFF_OPTIONS[key]) or 0)

        for key in [
            CONF_G12_DAY_START,
            CONF_G12_DAY_END,
            CONF_G12_NIGHT_START,
            CONF_G12_NIGHT_END,
        ]:
            normalized[key] = int(normalized.get(key, DEFAULT_TARIFF_OPTIONS[key]) or 0)

        return normalized

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from godzinowe.pl API."""
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession()

            # Fetch current price data
            current_data = await self._fetch_current_data()
            
            today_data = await self._fetch_today_classified()
            tomorrow_data = await self._fetch_tomorrow_classified()
            
            current_data = self._add_tariff_to_current(current_data)
            today_data = self._add_tariff_to_day(today_data)
            tomorrow_data = self._add_tariff_to_day(tomorrow_data)

            combined_data = {
                "current": current_data,
                "today": today_data,
                "tomorrow": tomorrow_data,
                "last_updated": dt_util.utcnow(),
                "tariff_options": self.options,
            }
            
            _LOGGER.debug("Successfully updated godzinowe.pl data")
            return combined_data

        except Exception as err:
            _LOGGER.error("Error updating godzinowe.pl data: %s", err)
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

    async def _fetch_tomorrow_classified(self) -> Dict[str, Any]:
        """Fetch tomorrow's classified price data."""
        url = f"{self.api_url}?action=tomorrow_classified"

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
            raise UpdateFailed(f"Error fetching tomorrow's data: {err}")

    def _get_hour_start(self, hour_range: Optional[str]) -> Optional[int]:
        """Extract the start hour from an API hour range."""
        if not hour_range or "-" not in hour_range:
            return None

        try:
            return int(hour_range.split("-", 1)[0])
        except (TypeError, ValueError):
            return None

    def _hour_in_range(self, hour: int, start: int, end: int) -> bool:
        """Return if hour is inside a potentially overnight range."""
        if start == end:
            return True
        if start < end:
            return start <= hour < end
        return hour >= start or hour < end

    def _is_g13_summer_season(self, date_str: Optional[str]) -> bool:
        """Return if date falls into the G13 summer afternoon-peak season."""
        if not date_str:
            return False

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return False

        return "04-01" <= date.strftime("%m-%d") <= "09-30"

    def _tariff_rate_for_hour(self, date_str: Optional[str], hour_range: Optional[str]) -> float:
        """Calculate configured tariff additions for a date and hour."""
        hour = self._get_hour_start(hour_range)
        if hour is None:
            return 0.0

        tariff_type = self.options[CONF_TARIFF_TYPE]
        fixed_rate = self.options[CONF_FIXED_RATE]

        if tariff_type == TARIFF_G11:
            return round(self.options[CONF_G11_RATE] + fixed_rate, 5)

        if tariff_type in (TARIFF_G12, TARIFF_G12W):
            is_weekend = False
            if date_str:
                try:
                    is_weekend = datetime.strptime(date_str, "%Y-%m-%d").weekday() >= 5
                except ValueError:
                    is_weekend = False

            if tariff_type == TARIFF_G12W and is_weekend:
                base_rate = self.options[CONF_G12_NIGHT_RATE]
            elif self._hour_in_range(
                hour,
                self.options[CONF_G12_NIGHT_START],
                self.options[CONF_G12_NIGHT_END],
            ):
                base_rate = self.options[CONF_G12_NIGHT_RATE]
            elif self._hour_in_range(
                hour,
                self.options[CONF_G12_DAY_START],
                self.options[CONF_G12_DAY_END],
            ):
                base_rate = self.options[CONF_G12_DAY_RATE]
            else:
                base_rate = self.options[CONF_G12_NIGHT_RATE]

            return round(base_rate + fixed_rate, 5)

        if tariff_type == TARIFF_G13:
            is_weekend = False
            if date_str:
                try:
                    is_weekend = datetime.strptime(date_str, "%Y-%m-%d").weekday() >= 5
                except ValueError:
                    is_weekend = False

            if is_weekend:
                base_rate = self.options[CONF_G13_OFFPEAK_RATE]
            elif self._hour_in_range(hour, 7, 13):
                base_rate = self.options[CONF_G13_MORNING_RATE]
            elif self._is_g13_summer_season(date_str) and self._hour_in_range(hour, 19, 22):
                base_rate = self.options[CONF_G13_AFTERNOON_RATE]
            elif not self._is_g13_summer_season(date_str) and self._hour_in_range(hour, 16, 21):
                base_rate = self.options[CONF_G13_AFTERNOON_RATE]
            else:
                base_rate = self.options[CONF_G13_OFFPEAK_RATE]

            return round(base_rate + fixed_rate, 5)

        return round(fixed_rate, 5)

    def _calculate_total_price(
        self, market_price: Optional[float], date_str: Optional[str], hour_range: Optional[str]
    ) -> Optional[float]:
        """Calculate market price with VAT multiplier and configured tariff additions."""
        if market_price is None:
            return None

        gross_market_price = market_price * self.options[CONF_MARKET_VAT_MULTIPLIER]
        return round(gross_market_price + self._tariff_rate_for_hour(date_str, hour_range), 5)

    def _add_tariff_to_current(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add calculated tariff fields to current price payload."""
        enriched = deepcopy(current_data or {})
        market_price = enriched.get("price_per_kwh")
        date_str = enriched.get("date")
        hour_range = enriched.get("current_hour_range")
        tariff_rate = self._tariff_rate_for_hour(date_str, hour_range)

        if market_price is not None:
            enriched["market_price_gross"] = round(
                float(market_price) * self.options[CONF_MARKET_VAT_MULTIPLIER], 5
            )
            enriched["tariff_rate"] = tariff_rate
            enriched["total_price"] = self._calculate_total_price(
                float(market_price), date_str, hour_range
            )

        return enriched

    def _add_tariff_to_day(self, day_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add calculated tariff fields to every hourly record."""
        enriched = deepcopy(day_data or {})
        records = enriched.get("records", [])
        date_str = enriched.get("date")

        for record in records:
            market_price = record.get("price_per_kwh")
            hour_range = record.get("hour")
            if market_price is None:
                continue

            record["market_price_gross"] = round(
                float(market_price) * self.options[CONF_MARKET_VAT_MULTIPLIER], 5
            )
            record["tariff_rate"] = self._tariff_rate_for_hour(date_str, hour_range)
            record["total_price"] = self._calculate_total_price(
                float(market_price), date_str, hour_range
            )

        total_prices = [
            record["total_price"]
            for record in records
            if record.get("total_price") is not None
        ]
        if total_prices:
            enriched["total_price_statistics"] = {
                "min_price": min(total_prices),
                "max_price": max(total_prices),
                "avg_price": round(sum(total_prices) / len(total_prices), 5),
            }

        return enriched

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
                    
                    # Get cheap hours in priority order, with fallback for older API keys.
                    cheap_hours = []

                    for range_key in ["negative", "zero", "very_low", "low", "taniutko"]:
                        for hour_data in price_ranges.get(range_key, {}).get("hours", []):
                            if len(cheap_hours) >= hours_needed:
                                break
                            hour = hour_data.get("hour")
                            if hour and hour not in cheap_hours:
                                cheap_hours.append(hour)

                        if len(cheap_hours) >= hours_needed:
                            break
                    
                    return cheap_hours[:hours_needed]
        
        except Exception as err:
            _LOGGER.error("Error getting cheap hours: %s", err)
            return []

    @property
    def current_price(self) -> Optional[float]:
        """Get current market price."""
        if self.data and "current" in self.data:
            return self.data["current"].get("price_per_kwh")
        return None

    @property
    def current_total_price(self) -> Optional[float]:
        """Get current price with configured tariff additions."""
        if self.data and "current" in self.data:
            return self.data["current"].get("total_price")
        return None

    @property
    def current_classification(self) -> Optional[str]:
        """Get current price classification."""
        if self.data and "current" in self.data:
            return self.data["current"].get("classification")
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
        return classification in [
            CLASSIFICATION_UJEMNA,
            CLASSIFICATION_ZERO,
            CLASSIFICATION_BARDZO_NISKA,
            CLASSIFICATION_NISKA,
            "TANIUTKO",
        ]

    @property
    def is_expensive(self) -> bool:
        """Check if current price is expensive."""
        classification = self.current_classification
        return classification in [
            CLASSIFICATION_WYSOKA,
            CLASSIFICATION_BARDZO_WYSOKA,
            CLASSIFICATION_EKSTREMALNA,
        ]

    @property
    def cheap_hours_today(self) -> List[str]:
        """Get list of cheap hours today."""
        if self.data and "today" in self.data:
            summary = self.data["today"].get("summary", {})
            cheap_hours = []
            cheap_hours.extend(summary.get("negative_hours", []))
            cheap_hours.extend(summary.get("zero_hours", []))
            cheap_hours.extend(summary.get("very_low_price_hours", []))
            cheap_hours.extend(summary.get("low_price_hours", []))
            cheap_hours.extend(summary.get("taniutko_hours", []))
            return cheap_hours
        return []

    @property
    def cheap_hours_tomorrow(self) -> List[str]:
        """Get list of cheap hours tomorrow."""
        return self._cheap_hours_for_day("tomorrow")

    @property
    def expensive_hours_today(self) -> List[str]:
        """Get list of expensive hours today."""
        if self.data and "today" in self.data:
            summary = self.data["today"].get("summary", {})
            expensive_hours = []
            expensive_hours.extend(summary.get("high_price_hours", []))
            expensive_hours.extend(summary.get("very_high_price_hours", []))
            expensive_hours.extend(summary.get("extreme_price_hours", []))
            return expensive_hours
        return []

    @property
    def expensive_hours_tomorrow(self) -> List[str]:
        """Get list of expensive hours tomorrow."""
        return self._expensive_hours_for_day("tomorrow")

    def _cheap_hours_for_day(self, day_key: str) -> List[str]:
        """Get list of cheap hours for a day payload."""
        if self.data and day_key in self.data:
            summary = self.data[day_key].get("summary", {})
            cheap_hours = []
            cheap_hours.extend(summary.get("negative_hours", []))
            cheap_hours.extend(summary.get("zero_hours", []))
            cheap_hours.extend(summary.get("very_low_price_hours", []))
            cheap_hours.extend(summary.get("low_price_hours", []))
            cheap_hours.extend(summary.get("taniutko_hours", []))
            return cheap_hours
        return []

    def cheap_hours_for_day(self, day_key: str) -> List[str]:
        """Get list of cheap hours for a named day payload."""
        return self._cheap_hours_for_day(day_key)

    def _expensive_hours_for_day(self, day_key: str) -> List[str]:
        """Get list of expensive hours for a day payload."""
        if self.data and day_key in self.data:
            summary = self.data[day_key].get("summary", {})
            expensive_hours = []
            expensive_hours.extend(summary.get("high_price_hours", []))
            expensive_hours.extend(summary.get("very_high_price_hours", []))
            expensive_hours.extend(summary.get("extreme_price_hours", []))
            return expensive_hours
        return []

    def expensive_hours_for_day(self, day_key: str) -> List[str]:
        """Get list of expensive hours for a named day payload."""
        return self._expensive_hours_for_day(day_key)

    def day_payload(self, day_key: str) -> Dict[str, Any]:
        """Return a day payload from coordinator data."""
        if self.data:
            return self.data.get(day_key, {})
        return {}

    def ranked_hours(self, day_key: str, reverse: bool = False, limit: int = 3) -> List[Dict[str, Any]]:
        """Return cheapest or most expensive hourly records by calculated total price."""
        records = self.day_payload(day_key).get("records", [])
        ranked = sorted(
            [record for record in records if record.get("total_price") is not None],
            key=lambda record: record["total_price"],
            reverse=reverse,
        )
        return ranked[:limit]

    async def async_close(self) -> None:
        """Close the session."""
        if self._session:
            await self._session.close()
            self._session = None
