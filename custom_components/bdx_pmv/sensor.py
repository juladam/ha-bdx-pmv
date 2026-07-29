"""Bordeaux PMV sensor platform."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import CONF_IDENT, CONF_NO_DATA

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bdx_pmv"
DEFAULT_NO_DATA = "***"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the combined PMV sensor from a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    ident = entry.data[CONF_IDENT]
    no_data = entry.options.get(CONF_NO_DATA, DEFAULT_NO_DATA)

    async_add_entities([PMVCombinedEntity(coordinator, ident, no_data)])


class PMVCombinedEntity(CoordinatorEntity, SensorEntity):
    """Sensor combining page1 and page2 of a PMV sign."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        ident: str,
        no_data: str,
    ) -> None:
        """Initialise the combined PMV sensor."""
        super().__init__(coordinator)
        self._ident = ident
        self._no_data = no_data

        self._attr_unique_id = f"{ident}_combined"
        self._attr_name = f"pmv_{ident}"
        self._attr_icon = "mdi:message-text-outline"

    def _page_value(self, page: str) -> str:
        """Return the value for a given page, falling back to no_data."""
        if self.coordinator.data is None:
            return self._no_data
        value = self.coordinator.data.get(page)
        return self._no_data if value is None else value

    @property
    def native_value(self) -> str:
        """Return page1 and page2 joined with a newline."""
        page1 = self._page_value("page1")
        page2 = self._page_value("page2")
        return f"{page1}\n{page2}"

    @property
    def extra_state_attributes(self) -> dict:
        """Expose page1 and page2 as individual attributes."""
        return {
            "page1": self._page_value("page1"),
            "page2": self._page_value("page2"),
        }
