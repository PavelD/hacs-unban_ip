import logging
import os
import yaml
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN, IP_BANS_FILE

_LOGGER = logging.getLogger(__name__)


def setup(hass: HomeAssistant, config: ConfigType):
    """Set up the Unban IP service."""

    def handle_unban_ip(call):
        ip_to_unban = call.data.get("ip_address")
        _LOGGER.info(f"Attempting to unban IP: {ip_to_unban}")

        # ath to ip_bans.yaml
        config_dir = hass.config.path(IP_BANS_FILE)
        if not os.path.exists(config_dir):
            _LOGGER.warning(f"{IP_BANS_FILE} not found, nothing to unban.")
            return

        # load existing bans
        with open(config_dir, "r") as f:
            try:
                bans = yaml.safe_load(f) or []
            except Exception as e:
                _LOGGER.error(f"Error reading {IP_BANS_FILE}: {e}")
                return

        # remove IP from list
        new_bans = [b for b in bans if b.get("ip_address") != ip_to_unban]

        if len(new_bans) == len(bans):
            _LOGGER.info(f"IP {ip_to_unban} not found in ban list.")
        else:
            _LOGGER.info(f"IP {ip_to_unban} removed from ban list.")
            with open(config_dir, "w") as f:
                yaml.safe_dump(new_bans, f)

        # in-memory unblock: remove IP from internal http.ban objet
        try:
            http_component = hass.data.get("http")
            if http_component and hasattr(http_component, "_ban"):
                ban_obj = http_component._ban
                if ip_to_unban in ban_obj.banned:
                    del ban_obj.banned[ip_to_unban]
                    _LOGGER.info(f"IP {ip_to_unban} removed from in-memory ban list.")
        except Exception as e:
            _LOGGER.warning(f"Could not remove IP from in-memory bans: {e}")

    hass.services.register(DOMAIN, "unban_ip", handle_unban_ip)
    _LOGGER.info("Unban IP service loaded.")
    return True
