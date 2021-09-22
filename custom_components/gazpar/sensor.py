from calendar import monthrange
from datetime import timedelta, datetime
import logging
import traceback

from custom_components.gazpar.gazpar import Gazpar
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
HA_LAST_ENERGY_M3 = 'Gazpar energy m³'
HA_LAST_ENERGY_PRICE = 'Gazpar energy price'
HA_MONTH_ENERGY_KWH = 'Gazpar energy month'
HA_MONTH_ENERGY_M3 = 'Gazpar energy month m³'
HA_MONTH_ENERGY_PRICE = 'Gazpar energy month price'
HA_LAST_MONTH_ENERGY_KWH = 'Gazpar energy last month'
HA_LAST_MONTH_ENERGY_M3 = 'Gazpar energy last month m³'
HA_LAST_MONTH_ENERGY_PRICE = 'Gazpar energy last month price'

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
        self.sensors.append(GazparSensor(HA_LAST_MONTH_ENERGY_KWH, ENERGY_KILO_WATT_HOUR))
        self.sensors.append(GazparSensor(HA_LAST_MONTH_ENERGY_PRICE, CURRENCY_EURO))

        track_time_interval(hass, self.update_gazpar_data, DEFAULT_SCAN_INTERVAL)

    def update_gazpar_data(self, event_time):
        """Fetch new state data for the sensor."""

        _LOGGER.debug('Querying Gazpar library for new data...')

        try:
            # Get full month data
            gazpar = Gazpar(self._username, self._password)

            now = datetime.now()
            last_month = now.month - 1 if now.month != 1 else 12
            month_data = gazpar.get_data_per_month(now.replace(month=last_month).strftime('%d/%m/%Y'), now.strftime('%d/%m/%Y'))
            last_day_data = gazpar.get_data_per_day(now.replace(day=now.day - 1).strftime('%d/%m/%Y'), now.strftime('%d/%m/%Y'))
            month_data_m3 = gazpar.get_data_per_month(now.replace(month=last_month).strftime('%d/%m/%Y'), now.strftime('%d/%m/%Y'), True)
            last_day_data_m3 = gazpar.get_data_per_day(now.replace(day=now.day - 1).strftime('%d/%m/%Y'), now.strftime('%d/%m/%Y'), True)

            last_kwh = int(last_day_data[-1]['kwh'])
            month_kwh = int(month_data[-1]['kwh'])
            last_month_kwh = int(month_data[-2]['kwh'])
            last_m3 = int(last_day_data_m3[-1]['kwh'])
            month_m3 = int(month_data_m3[-1]['kwh'])
            last_month_m3 = int(month_data_m3[-2]['kwh'])
            timestamp = datetime.strptime(last_day_data[-1]['time'], '%d/%m/%Y')

            # Update sensors
            for sensor in self.sensors:
                if sensor.name == HA_LAST_ENERGY_KWH:
                    sensor.set_data(timestamp, last_kwh)
                if sensor.name == HA_MONTH_ENERGY_KWH:
                    sensor.set_data(timestamp, month_kwh)
                if sensor.name == HA_LAST_MONTH_ENERGY_KWH:
                    sensor.set_data(timestamp, last_month_kwh)
                if sensor.name == HA_LAST_ENERGY_M3:
                    sensor.set_data(timestamp, last_m3)
                if sensor.name == HA_MONTH_ENERGY_M3:
                    sensor.set_data(timestamp, month_m3)
                if sensor.name == HA_LAST_MONTH_ENERGY_M3:
                    sensor.set_data(timestamp, last_month_m3)
                if sensor.name == HA_LAST_ENERGY_PRICE:
                    sensor.set_data(timestamp, round(last_kwh * self._cost, 4))
                if sensor.name == HA_MONTH_ENERGY_PRICE:
                    sensor.set_data(timestamp, round(month_kwh * self._cost, 4))
                if sensor.name == HA_LAST_MONTH_ENERGY_PRICE:
                    sensor.set_data(timestamp, round(last_month_kwh * self._cost, 4))

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
