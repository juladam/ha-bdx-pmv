"""Config flow for Bordeaux PMV integration."""
import logging

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import CONF_KEY, CONF_IDENT, CONF_NO_DATA

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bdx_pmv"

DEFAULT_IDENT = "Z40P115"
DEFAULT_NO_DATA = "***"
DEFAULT_SCAN_INTERVAL = 1800

API_URL = "https://data.bordeaux-metropole.fr/geojson?key={}&typename=pc_pmv_p"


async def _validate_api_key(api_key: str) -> str | None:
    """Test the API key against the Bordeaux Métropole API.

    Returns None on success, or an error string key on failure.
    """
    url = API_URL.format(api_key)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 401 or resp.status == 403:
                    return "invalid_auth"
                if resp.status != 200:
                    return "cannot_connect"
                data = await resp.json(content_type=None)
                if "features" not in data:
                    return "cannot_connect"
    except aiohttp.ClientError:
        return "cannot_connect"
    except Exception:  # pylint: disable=broad-except
        return "unknown"
    return None


class BdxPmvConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial config flow for Bordeaux PMV."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return BdxPmvOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the user step."""
        errors = {}

        if user_input is not None:
            api_key = user_input[CONF_KEY].strip()
            ident = user_input[CONF_IDENT].strip()

            # Prevent duplicate entries for the same PMV sign.
            await self.async_set_unique_id(ident)
            self._abort_if_unique_id_configured()

            error = await _validate_api_key(api_key)
            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title=f"PMV {ident}",
                    data={
                        CONF_KEY: api_key,
                        CONF_IDENT: ident,
                    },
                    options={
                        CONF_NO_DATA: user_input.get(CONF_NO_DATA, DEFAULT_NO_DATA),
                        "scan_interval": DEFAULT_SCAN_INTERVAL,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_KEY): str,
                vol.Required(CONF_IDENT, default=DEFAULT_IDENT): str,
                vol.Optional(CONF_NO_DATA, default=DEFAULT_NO_DATA): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )


class BdxPmvOptionsFlow(config_entries.OptionsFlow):
    """Handle options for an existing Bordeaux PMV entry."""

    def __init__(self, config_entry):
        """Store the config entry."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NO_DATA,
                    default=current_options.get(CONF_NO_DATA, DEFAULT_NO_DATA),
                ): str,
                vol.Optional(
                    "scan_interval",
                    default=current_options.get("scan_interval", DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=60)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
