"""Config flow for godzinowe.pl integration."""
import logging
from typing import Any, Dict, Optional

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_API_URL,
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
    DEFAULT_API_URL,
    DEFAULT_TARIFF_OPTIONS,
    DOMAIN,
    TARIFF_TYPES,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): str,
    }
)


def _options_schema(options: Dict[str, Any]) -> vol.Schema:
    """Build options schema with current values as defaults."""
    values = dict(DEFAULT_TARIFF_OPTIONS)
    values.update(options or {})

    return vol.Schema(
        {
            vol.Optional(
                CONF_TARIFF_TYPE, default=values[CONF_TARIFF_TYPE]
            ): vol.In(TARIFF_TYPES),
            vol.Optional(
                CONF_MARKET_VAT_MULTIPLIER,
                default=values[CONF_MARKET_VAT_MULTIPLIER],
            ): vol.Coerce(float),
            vol.Optional(
                CONF_FIXED_RATE, default=values[CONF_FIXED_RATE]
            ): vol.Coerce(float),
            vol.Optional(
                CONF_G11_RATE, default=values[CONF_G11_RATE]
            ): vol.Coerce(float),
            vol.Optional(
                CONF_G12_DAY_RATE, default=values[CONF_G12_DAY_RATE]
            ): vol.Coerce(float),
            vol.Optional(
                CONF_G12_NIGHT_RATE, default=values[CONF_G12_NIGHT_RATE]
            ): vol.Coerce(float),
            vol.Optional(
                CONF_G13_MORNING_RATE, default=values[CONF_G13_MORNING_RATE]
            ): vol.Coerce(float),
            vol.Optional(
                CONF_G13_AFTERNOON_RATE, default=values[CONF_G13_AFTERNOON_RATE]
            ): vol.Coerce(float),
            vol.Optional(
                CONF_G13_OFFPEAK_RATE, default=values[CONF_G13_OFFPEAK_RATE]
            ): vol.Coerce(float),
            vol.Optional(
                CONF_G12_DAY_START, default=values[CONF_G12_DAY_START]
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            vol.Optional(
                CONF_G12_DAY_END, default=values[CONF_G12_DAY_END]
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=24)),
            vol.Optional(
                CONF_G12_NIGHT_START, default=values[CONF_G12_NIGHT_START]
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            vol.Optional(
                CONF_G12_NIGHT_END, default=values[CONF_G12_NIGHT_END]
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=24)),
        }
    )


async def validate_api(hass: HomeAssistant, api_url: str) -> Dict[str, Any]:
    """Validate the API URL by making a test request."""
    try:
        session = aiohttp.ClientSession()
        
        try:
            async with async_timeout.timeout(10):
                async with session.get(f"{api_url}?action=info") as response:
                    if response.status != 200:
                        raise CannotConnect(f"API returned status {response.status}")
                    
                    data = await response.json()
                    if not data.get("success"):
                        raise InvalidAPI("API response indicates failure")
                    
                    api_info = data.get("data", {})
                    return {
                        "name": api_info.get("name", "godzinowe.pl API"),
                        "version": api_info.get("version", "unknown"),
                    }
        finally:
            await session.close()
            
    except aiohttp.ClientError as err:
        _LOGGER.error("Network error connecting to API: %s", err)
        raise CannotConnect("Cannot connect to API")
    except HomeAssistantError:
        raise
    except Exception as err:
        _LOGGER.error("Unexpected error validating API: %s", err)
        raise InvalidAPI(f"Unexpected error: {err}")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for godzinowe.pl."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate the API
                api_info = await validate_api(self.hass, user_input[CONF_API_URL])
                
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_API_URL])
                self._abort_if_unique_id_configured()
                
                # Create entry
                return self.async_create_entry(
                    title=api_info["name"],
                    data=user_input,
                )
                
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAPI:
                errors["base"] = "invalid_api"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAPI(HomeAssistantError):
    """Error to indicate the API is invalid."""


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for tariff additions."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage tariff options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(self._config_entry.options),
        )
