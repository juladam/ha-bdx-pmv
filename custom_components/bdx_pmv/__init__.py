"""Bordeaux PMV integration."""
import logging
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_KEY, CONF_IDENT

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bdx_pmv"
PLATFORMS = ["sensor"]
API_URL = "https://data.bordeaux-metropole.fr/geojson?key={}&typename=pc_pmv_p"
DEFAULT_SCAN_INTERVAL = 1800


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bordeaux PMV from a config entry."""
    api_key = entry.data[CONF_KEY]
    ident = entry.data[CONF_IDENT]
    scan_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    async def _async_fetch_data() -> dict:
        """Fetch properties for the configured PMV sign."""
        url = API_URL.format(api_key)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        for feature in data.get("features", []):
            props = feature.get("properties", {})
            if props.get("ident") == ident:
                return props

        raise UpdateFailed(f"PMV sign '{ident}' not found in API response.")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"bdx_pmv_{ident}",
        update_method=_async_fetch_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    # Initial fetch so sensors have data before being added.
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
