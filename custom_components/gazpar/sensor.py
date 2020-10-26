from datetime import timedelta, datetime
import json
import logging
import traceback

import custom_components.gazpar.gazpar as gazpar
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION, CONF_PASSWORD, CONF_USERNAME,
    ENERGY_KILO_WATT_HOUR, CURRENCY_EURO)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import track_time_interval, call_later

_LOGGER = logging.getLogger(__name__)

# CONST
DEFAULT_SCAN_INTERVAL = timedelta(hours=4)
CONF_COST = 'cost'

HA_ATTRIBUTION = 'Data provided by GrDF'
HA_TIME = 'time'
HA_TIMESTAMP = 'timestamp'
HA_TYPE = 'type'

ICON_GAS = 'mdi:fire'
ICON_PRICE = 'mdi:currency-eur'

HA_LAST_ENERGY_KWH = 'Gazpar energy'
HA_LAST_ENERGY_PRICE = 'Gazpar energy price'
HA_MONTH_ENERGY_KWH = 'Gazpar energy month'
HA_MONTH_ENERGY_PRICE = 'Gazpar energy month price'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_COST): cv.small_float,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Configure the platform and add the Gazpar sensor."""

    _LOGGER.debug('Initializing Gazpar platform...')

    try:
        username = config[CONF_USERNAME]
        password = config[CONF_PASSWORD]
        cost = config[CONF_COST]

        account = GazparAccount(hass, username, password, cost)
        add_entities(account.sensors, True)

        _LOGGER.debug('Gazpar platform initialization has completed successfully')
    except BaseException:
        _LOGGER.error('Gazpar platform initialization has failed with exception : {0}'.format(traceback.format_exc()))


class GazparAccount:
    """Representation of a Gazpar account."""

    def __init__(self, hass, username, password, cost):
        """Initialise the Gazpar account."""
        self._username = username
        self._password = password
        self._cost = cost
        self.sensors = []

        call_later(hass, 5, self.update_gazpar_data)

        # Add sensors
        self.sensors.append(GazparSensor(HA_LAST_ENERGY_KWH, ENERGY_KILO_WATT_HOUR))
        self.sensors.append(GazparSensor(HA_LAST_ENERGY_PRICE, CURRENCY_EURO))
        self.sensors.append(GazparSensor(HA_MONTH_ENERGY_KWH, ENERGY_KILO_WATT_HOUR))
        self.sensors.append(GazparSensor(HA_MONTH_ENERGY_PRICE, CURRENCY_EURO))

        track_time_interval(hass, self.update_gazpar_data, DEFAULT_SCAN_INTERVAL)

    def update_gazpar_data(self, event_time):
        """Fetch new state data for the sensor."""

        _LOGGER.debug('Querying Gazpar library for new data...')

        try:
            # Get full month data
            session = gazpar.login(self._username, self._password)
            data = gazpar.get_data_per_day(session,
                                           datetime.now().replace(day=1).strftime('%d/%m/%Y'),
                                           datetime.now().replace(day=31).strftime('%d/%m/%Y'))
            _LOGGER.debug('data={0}'.format(json.dumps(data, indent=2)))

            last_kwh = int(data[-1]['conso'])
            month_kwh = sum([int(d['conso']) for d in data])
            timestamp = datetime.strptime(data[-1]['time'], '%d/%m/%Y')

            # Update sensors
            for sensor in self.sensors:
                if sensor.name == HA_LAST_ENERGY_KWH:
                    sensor.set_data(timestamp, last_kwh)
                if sensor.name == HA_MONTH_ENERGY_KWH:
                    sensor.set_data(timestamp, month_kwh)
                if sensor.name == HA_LAST_ENERGY_PRICE:
                    sensor.set_data(timestamp, round(last_kwh * self._cost, 4))
                if sensor.name == HA_MONTH_ENERGY_PRICE:
                    sensor.set_data(timestamp, round(month_kwh * self._cost, 4))

                sensor.async_schedule_update_ha_state(True)
                _LOGGER.debug('HA notified that new data is available')
        except BaseException:
            _LOGGER.error('Failed to query Gazpar library with exception : {0}'.format(traceback.format_exc()))

    @property
    def username(self):
        """Return the username."""
        return self._username


class GazparSensor(Entity):
    """Representation of a sensor entity for Gazpar."""

    def __init__(self, name, unit):
        """Initialize the sensor."""
        self._name = name
        self._unit = unit
        self._timestamp = None
        self._measure = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._measure

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def icon(self):
        """Return the icon of the sensor."""
        if self._name in [HA_MONTH_ENERGY_KWH, HA_LAST_ENERGY_KWH]:
            return ICON_GAS
        else:
            return ICON_PRICE

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_ATTRIBUTION: HA_ATTRIBUTION,
            HA_TIMESTAMP: self._timestamp,
        }

    def set_data(self, timestamp, measure):
        """Update sensor data"""
        self._measure = measure
        self._timestamp = timestamp
