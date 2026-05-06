"""Constants for godzinowe.pl Home Assistant integration."""

DOMAIN = "godzinowe_pl"
DEFAULT_NAME = "godzinowe.pl"

# API Configuration
API_BASE_URL = "https://godzinowe.pl/api.php"
DEFAULT_API_URL = API_BASE_URL

# Update intervals (seconds)
UPDATE_INTERVAL_CURRENT = 300  # 5 minutes
UPDATE_INTERVAL_DAILY = 3600   # 1 hour

# Price Classifications
CLASSIFICATION_UJEMNA = "UJEMNA"
CLASSIFICATION_ZERO = "ZERO"
CLASSIFICATION_BARDZO_NISKA = "BARDZO NISKA"
CLASSIFICATION_NISKA = "NISKA"
CLASSIFICATION_SREDNIA = "ŚREDNIA"
CLASSIFICATION_WYSOKA = "WYSOKA"
CLASSIFICATION_BARDZO_WYSOKA = "BARDZO WYSOKA"
CLASSIFICATION_EKSTREMALNA = "EKSTREMALNA"

PRICE_CLASSIFICATIONS = [
    CLASSIFICATION_UJEMNA,
    CLASSIFICATION_ZERO,
    CLASSIFICATION_BARDZO_NISKA,
    CLASSIFICATION_NISKA,
    CLASSIFICATION_SREDNIA,
    CLASSIFICATION_WYSOKA,
    CLASSIFICATION_BARDZO_WYSOKA,
    CLASSIFICATION_EKSTREMALNA,
]

# Services
SERVICE_UPDATE_PRICES = "update_prices"
SERVICE_GET_CHEAP_HOURS = "get_cheap_hours"

# Configuration
CONF_API_URL = "api_url"
CONF_TARIFF_TYPE = "tariff_type"
CONF_MARKET_VAT_MULTIPLIER = "market_vat_multiplier"
CONF_FIXED_RATE = "fixed_rate"
CONF_G11_RATE = "g11_distribution_rate"
CONF_G12_DAY_RATE = "g12_day_distribution_rate"
CONF_G12_NIGHT_RATE = "g12_night_distribution_rate"
CONF_G12_DAY_START = "g12_day_start"
CONF_G12_DAY_END = "g12_day_end"
CONF_G12_NIGHT_START = "g12_night_start"
CONF_G12_NIGHT_END = "g12_night_end"
CONF_G13_MORNING_RATE = "g13_morning_peak_distribution_rate"
CONF_G13_AFTERNOON_RATE = "g13_afternoon_peak_distribution_rate"
CONF_G13_OFFPEAK_RATE = "g13_offpeak_distribution_rate"

TARIFF_G11 = "g11"
TARIFF_G12 = "g12"
TARIFF_G12W = "g12w"
TARIFF_G13 = "g13"
TARIFF_TYPES = [TARIFF_G11, TARIFF_G12, TARIFF_G12W, TARIFF_G13]

DEFAULT_TARIFF_OPTIONS = {
    CONF_TARIFF_TYPE: TARIFF_G11,
    CONF_MARKET_VAT_MULTIPLIER: 1.23,
    CONF_FIXED_RATE: 0.0,
    CONF_G11_RATE: 0.0,
    CONF_G12_DAY_RATE: 0.0,
    CONF_G12_NIGHT_RATE: 0.0,
    CONF_G12_DAY_START: 6,
    CONF_G12_DAY_END: 22,
    CONF_G12_NIGHT_START: 22,
    CONF_G12_NIGHT_END: 6,
    CONF_G13_MORNING_RATE: 0.0,
    CONF_G13_AFTERNOON_RATE: 0.0,
    CONF_G13_OFFPEAK_RATE: 0.0,
}

# Sensor types
SENSOR_TYPES = {
    "current_price": {
        "name": "Aktualna cena rynkowa",
        "unit": "zł/kWh",
        "icon": "mdi:flash",
        "state_class": "measurement",
    },
    "current_total_price": {
        "name": "Aktualna cena z taryfą",
        "unit": "zł/kWh",
        "icon": "mdi:cash-plus",
        "state_class": "measurement",
    },
    "current_classification": {
        "name": "Klasyfikacja Ceny",
        "icon": "mdi:tag-outline",
    },
    "tge_price": {
        "name": "Cena TGE",
        "unit": "zł/kWh",
        "icon": "mdi:transmission-tower",
        "state_class": "measurement",
    },
    "cheap_hours_count": {
        "name": "Liczba tanich godzin dziś",
        "unit": "godzin",
        "icon": "mdi:clock-outline",
    },
    "expensive_hours_count": {
        "name": "Liczba drogich godzin dziś",
        "unit": "godzin",
        "icon": "mdi:clock-alert-outline",
    },
    "tomorrow_cheap_hours_count": {
        "name": "Liczba tanich godzin jutro",
        "unit": "godzin",
        "icon": "mdi:clock-check-outline",
    },
    "tomorrow_expensive_hours_count": {
        "name": "Liczba drogich godzin jutro",
        "unit": "godzin",
        "icon": "mdi:clock-alert",
    },
    "today_schedule": {
        "name": "Plan cen dziś",
        "icon": "mdi:calendar-today",
    },
    "tomorrow_schedule": {
        "name": "Plan cen jutro",
        "icon": "mdi:calendar-arrow-right",
    },
}

# Binary sensor types
BINARY_SENSOR_TYPES = {
    "is_cheap": {
        "name": "Energia Tania",
        "icon": "mdi:currency-usd-off",
        "device_class": "power",
    },
    "is_expensive": {
        "name": "Energia Droga",
        "icon": "mdi:alert",
        "device_class": "problem",
    },
}

# Attributes
ATTR_CURRENT_HOUR_RANGE = "current_hour_range"
ATTR_DATE = "date"
ATTR_CLASSIFICATION = "classification"
ATTR_VOLUME = "volume"
ATTR_CHEAP_HOURS = "cheap_hours"
ATTR_EXPENSIVE_HOURS = "expensive_hours"
ATTR_THRESHOLDS = "thresholds"
ATTR_STATISTICS = "statistics"
ATTR_RECORDS = "records"
ATTR_AVAILABLE = "available"
ATTR_MESSAGE = "message"
ATTR_COMPLETENESS = "completeness"
ATTR_TOTAL_PRICE = "total_price"
ATTR_TARIFF_RATE = "tariff_rate"
ATTR_MARKET_PRICE_GROSS = "market_price_gross"
ATTR_CHEAPEST_HOURS = "cheapest_hours"
ATTR_MOST_EXPENSIVE_HOURS = "most_expensive_hours"
ATTR_TARIFF_OPTIONS = "tariff_options"
