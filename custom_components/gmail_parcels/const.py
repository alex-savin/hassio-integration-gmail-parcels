DOMAIN = "gmail_parcels"
DEFAULT_HOST = "http://addon:8080"
WS_ENDPOINT = "/ws"
SENSOR_TYPE = "sensor"
CONF_LOG_LEVEL = "log_level"
DEFAULT_LOG_LEVEL = "info"
LOG_LEVEL_CHOICES = ["debug", "info", "warning", "error", "critical"]

# Buckets surfaced as count sensors. "upcoming" = everything not delivered;
# "today" is a subset of upcoming (out-for-delivery / ETA today).
BUCKETS = ["upcoming", "today", "delivered"]

# Carriers we model. A fixed list keeps the entity set stable across restarts
# (sensors stay put even at count 0) rather than appearing/disappearing as mail
# arrives. Keys are the canonical carrier names emitted by the addon; the value
# is the entity-id slug. Anything else falls into the "other" bucket sensors.
CARRIERS = {
    "UPS": "ups",
    "FedEx": "fedex",
    "USPS": "usps",
    "DHL": "dhl",
}
OTHER_CARRIER_SLUG = "other"
