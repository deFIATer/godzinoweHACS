"""Config flow for TGE ENEA integration."""
import logging
from typing import Any, Dict, Optional

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEFAULT_API_URL, CONF_API_URL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): str,
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
                        "name": api_info.get("name", "TGE ENEA API"),
                        "version": api_info.get("version", "unknown"),
                    }
        finally:
            await session.close()
            
    except aiohttp.ClientError as err:
        _LOGGER.error("Network error connecting to API: %s", err)
        raise CannotConnect("Cannot connect to API")
    except Exception as err:
        _LOGGER.error("Unexpected error validating API: %s", err)
        raise InvalidAPI(f"Unexpected error: {err}")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TGE ENEA."""

    VERSION = 1

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
                    title=f"TGE ENEA - {api_info['name']}",
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