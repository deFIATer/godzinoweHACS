"""Constants for TGE ENEA integration."""

DOMAIN = "tge_enea"
DEFAULT_NAME = "TGE ENEA"

# API Configuration
API_BASE_URL = "https://godzinowe.pl/api"
DEFAULT_API_URL = API_BASE_URL

# Update intervals (seconds)
UPDATE_INTERVAL_CURRENT = 300  # 5 minutes
UPDATE_INTERVAL_DAILY = 3600   # 1 hour

# Price Classifications
CLASSIFICATION_TANIUTKO = "TANIUTKO"
CLASSIFICATION_NISKA = "NISKA"
CLASSIFICATION_SREDNIA = "ŚREDNIA"
CLASSIFICATION_WYSOKA = "WYSOKA"

PRICE_CLASSIFICATIONS = [
    CLASSIFICATION_TANIUTKO,
    CLASSIFICATION_NISKA,
    CLASSIFICATION_SREDNIA,
    CLASSIFICATION_WYSOKA,
]

# Services
SERVICE_UPDATE_PRICES = "update_prices"
SERVICE_GET_CHEAP_HOURS = "get_cheap_hours"

# Configuration
CONF_API_URL = "api_url"

# Sensor types
SENSOR_TYPES = {
    "current_price": {
        "name": "Aktualna Cena ENEA",
        "unit": "zł/kWh",
        "icon": "mdi:flash",
        "device_class": "monetary",
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
        "device_class": "monetary",
        "state_class": "measurement",
    },
    "cheap_hours_count": {
        "name": "Liczba Tanich Godzin",
        "unit": "godzin",
        "icon": "mdi:clock-outline",
    },
    "expensive_hours_count": {
        "name": "Liczba Drogich Godzin", 
        "unit": "godzin",
        "icon": "mdi:clock-alert-outline",
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
ATTR_CLASSIFICATION_TGE = "classification_tge"
ATTR_CLASSIFICATION_ENEA = "classification_enea"
ATTR_VOLUME = "volume"
ATTR_CHEAP_HOURS = "cheap_hours"
ATTR_EXPENSIVE_HOURS = "expensive_hours"
ATTR_THRESHOLDS = "thresholds"
ATTR_STATISTICS = "statistics"