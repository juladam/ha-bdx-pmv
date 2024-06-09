from datetime import timedelta, date
import logging
import re
import json

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
import requests

from .const import (
    DOMAIN, CONF_KEY, CONF_GID, CONF_SCAN_INTERVAL,
    ATTR_PAGE1, ATTR_PAGE2, ATTR_COUNT, CONF_DAYS_OLD)

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'bdx_pmv'
SCAN_INTERVAL = timedelta(seconds=30*60)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_KEY): cv.string,
    vol.Required(CONF_GID, default='5742'): cv.string,
    # vol.Required(CONF_SCAN_INTERVAL, default=3600): cv.positive_int,
    vol.Required(CONF_DAYS_OLD, default='30'): cv.positive_int,
})



def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the PMV platform."""
    add_entities([PMVEntity(config)], True)


class PMVEntity(Entity):
    """PMV Entity."""

    def __init__(self, config):
        """Init the PMV Entity."""
        self._attr = {
            ATTR_PAGE1: {},
            ATTR_PAGE2: {},
	        ATTR_COUNT: 0
        }

        self.bdx_key = config[CONF_KEY]
        self.gid = config[CONF_GID]

    def update(self):
        """Update data."""
        self._attr = {
            ATTR_PAGE1: {},
            ATTR_PAGE2: {},
	        ATTR_COUNT: 0
        }

        # update to current day
        # self.flag = [u'SINCE', date.today() - timedelta(days=self.days_old)]
        # _LOGGER.debug(f'flag: {self.flag}')

        message1 = ""
        message2 = ""
        url = "https://data.bordeaux-metropole.fr/geojson?key={}&typename=pc_pmv_p".format(self.bdx_key)
        response = requests.get(url)
        data = response.json()
        _LOGGER.debug(f'json data: {data}')
        for feature in data['features']:
            if feature['properties']['gid'] == int(self.gid):
                message1 = feature['properties']['page1']
                message2 = feature['properties']['page2']
                break

        self._attr[ATTR_PAGE1] = message1
        self._attr[ATTR_PAGE2] = message2
        _LOGGER.debug(f'ATTR_PAGE1: {self._attr[ATTR_PAGE1]}')
        _LOGGER.debug(f'ATTR_PAGE2: {self._attr[ATTR_PAGE2]}')

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'pmv_{}'.format(self.gid)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._attr[ATTR_PAGE1]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attr

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return 'mdi:email'
