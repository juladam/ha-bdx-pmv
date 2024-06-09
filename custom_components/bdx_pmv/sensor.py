from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
import requests

from .const import (
    CONF_KEY, CONF_IDENT, ATTR_PAGE)

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'bdx_pmv'
SCAN_INTERVAL = timedelta(seconds=30*60)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_KEY): cv.string,
    vol.Required(CONF_IDENT, default='Z40P115'): cv.string,
})



def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the PMV platform."""
    pages = ['page1', 'page2']
    entities = [PMVEntity(config, page) for page in pages]
    add_entities(entities, True)


class PMVEntity(Entity):
    """PMV Entity."""

    def __init__(self, config, page):
        """Init the PMV Entity."""
        self._attr = {
            ATTR_PAGE: {}
        }

        self.bdx_key = config[CONF_KEY]
        self.ident = config[CONF_IDENT]
        self.page = page

    def update(self):
        """Update data."""
        self._attr = {
            ATTR_PAGE: {}
        }

        url = "https://data.bordeaux-metropole.fr/geojson?key={}&typename=pc_pmv_p".format(self.bdx_key)
        response = requests.get(url)
        data = response.json()
        _LOGGER.debug(f'json data: {data}')
        for feature in data['features']:
            if feature['properties']['ident'] == self.ident:
                self._attr[ATTR_PAGE] = feature['properties'][self.page]
                break

        _LOGGER.debug(f'ATTR_PAGE: {self._attr[ATTR_PAGE]}')

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'pmv_{}_{}'.format(self.ident, self.page)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._attr[ATTR_PAGE]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attr

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return 'mdi:message-text-outline'
