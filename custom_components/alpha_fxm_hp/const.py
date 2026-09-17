"""Constants for the Alpha FXM HP UPS integration."""
from __future__ import annotations

DOMAIN = "alpha_fxm_hp"

DEFAULT_PORT = 161
DEFAULT_NAME = "Alpha FXM HP"
DEFAULT_SCAN_INTERVAL = 60  # seconds
MIN_SCAN_INTERVAL = 15

# --- Config entry / options keys -------------------------------------------------
CONF_SNMP_VERSION = "snmp_version"
CONF_COMMUNITY = "community"
CONF_USERNAME = "username"
CONF_AUTH_PROTOCOL = "auth_protocol"
CONF_AUTH_KEY = "auth_key"
CONF_PRIV_PROTOCOL = "priv_protocol"
CONF_PRIV_KEY = "priv_key"
CONF_SCAN_INTERVAL = "scan_interval"

SNMP_V1 = "v1"
SNMP_V2C = "v2c"
SNMP_V3 = "v3"
SNMP_VERSIONS = [SNMP_V1, SNMP_V2C, SNMP_V3]

# Display-name -> pysnmp object lookup keys. The actual pysnmp protocol
# objects are resolved lazily in snmp_client.py so this module has no
# hard dependency on pysnmp being importable at HA startup.
AUTH_PROTOCOL_NONE = "none"
AUTH_PROTOCOL_MD5 = "md5"
AUTH_PROTOCOL_SHA = "sha"
AUTH_PROTOCOL_SHA224 = "sha224"
AUTH_PROTOCOL_SHA256 = "sha256"
AUTH_PROTOCOL_SHA384 = "sha384"
AUTH_PROTOCOL_SHA512 = "sha512"

AUTH_PROTOCOLS = [
    AUTH_PROTOCOL_NONE,
    AUTH_PROTOCOL_MD5,
    AUTH_PROTOCOL_SHA,
    AUTH_PROTOCOL_SHA224,
    AUTH_PROTOCOL_SHA256,
    AUTH_PROTOCOL_SHA384,
    AUTH_PROTOCOL_SHA512,
]

PRIV_PROTOCOL_NONE = "none"
PRIV_PROTOCOL_DES = "des"
PRIV_PROTOCOL_3DES = "3des"
PRIV_PROTOCOL_AES128 = "aes128"
PRIV_PROTOCOL_AES192 = "aes192"
PRIV_PROTOCOL_AES256 = "aes256"

PRIV_PROTOCOLS = [
    PRIV_PROTOCOL_NONE,
    PRIV_PROTOCOL_DES,
    PRIV_PROTOCOL_3DES,
    PRIV_PROTOCOL_AES128,
    PRIV_PROTOCOL_AES192,
    PRIV_PROTOCOL_AES256,
]

PLATFORMS = ["sensor", "binary_sensor", "button"]

# Base OID for a full diagnostic walk (upsObjects, RFC 1628).
OID_UPS_MIB_BASE = "1.3.6.1.2.1.33"

# --- Standard UPS-MIB (RFC 1628) OIDs ---------------------------------------------
# Base: 1.3.6.1.2.1.33
OID_IDENT_MANUFACTURER = "1.3.6.1.2.1.33.1.1.1.0"
OID_IDENT_MODEL = "1.3.6.1.2.1.33.1.1.2.0"
OID_IDENT_UPS_SOFTWARE_VERSION = "1.3.6.1.2.1.33.1.1.3.0"
OID_IDENT_AGENT_SOFTWARE_VERSION = "1.3.6.1.2.1.33.1.1.4.0"
OID_IDENT_NAME = "1.3.6.1.2.1.33.1.1.5.0"

OID_BATTERY_STATUS = "1.3.6.1.2.1.33.1.2.1.0"
OID_SECONDS_ON_BATTERY = "1.3.6.1.2.1.33.1.2.2.0"
OID_ESTIMATED_MINUTES_REMAINING = "1.3.6.1.2.1.33.1.2.3.0"
OID_ESTIMATED_CHARGE_REMAINING = "1.3.6.1.2.1.33.1.2.4.0"
OID_BATTERY_VOLTAGE = "1.3.6.1.2.1.33.1.2.5.0"  # 0.1 Volt DC
OID_BATTERY_CURRENT = "1.3.6.1.2.1.33.1.2.6.0"  # 0.1 Amp DC
OID_BATTERY_TEMPERATURE = "1.3.6.1.2.1.33.1.2.7.0"  # degrees C

OID_INPUT_LINE_BADS = "1.3.6.1.2.1.33.1.3.1.0"
OID_INPUT_NUM_LINES = "1.3.6.1.2.1.33.1.3.2.0"
# Input table entries are indexed by line number, starting at 1.
OID_INPUT_FREQUENCY = "1.3.6.1.2.1.33.1.3.3.1.2.1"  # 0.1 Hertz
OID_INPUT_VOLTAGE = "1.3.6.1.2.1.33.1.3.3.1.3.1"  # RMS Volts
OID_INPUT_CURRENT = "1.3.6.1.2.1.33.1.3.3.1.4.1"  # 0.1 RMS Amp
OID_INPUT_TRUE_POWER = "1.3.6.1.2.1.33.1.3.3.1.5.1"  # Watts

OID_OUTPUT_SOURCE = "1.3.6.1.2.1.33.1.4.1.0"
OID_OUTPUT_FREQUENCY = "1.3.6.1.2.1.33.1.4.2.0"  # 0.1 Hertz
OID_OUTPUT_NUM_LINES = "1.3.6.1.2.1.33.1.4.3.0"
OID_OUTPUT_VOLTAGE = "1.3.6.1.2.1.33.1.4.4.1.2.1"  # RMS Volts
OID_OUTPUT_CURRENT = "1.3.6.1.2.1.33.1.4.4.1.3.1"  # 0.1 RMS Amp
OID_OUTPUT_POWER = "1.3.6.1.2.1.33.1.4.4.1.4.1"  # Watts
OID_OUTPUT_PERCENT_LOAD = "1.3.6.1.2.1.33.1.4.4.1.5.1"  # percent

OID_BYPASS_FREQUENCY = "1.3.6.1.2.1.33.1.5.1.0"  # 0.1 Hertz
OID_BYPASS_NUM_LINES = "1.3.6.1.2.1.33.1.5.2.0"
OID_BYPASS_VOLTAGE = "1.3.6.1.2.1.33.1.5.3.1.2.1"  # RMS Volts

OID_ALARMS_PRESENT = "1.3.6.1.2.1.33.1.6.1.0"

# Enum lookups
BATTERY_STATUS_MAP = {
    1: "unknown",
    2: "normal",
    3: "low",
    4: "depleted",
}

OUTPUT_SOURCE_MAP = {
    1: "other",
    2: "none",
    3: "normal",
    4: "bypass",
    5: "battery",
    6: "booster",
    7: "reducer",
}
