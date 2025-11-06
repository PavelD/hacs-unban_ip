import yaml
import pytest
from homeassistant.core import HomeAssistant

from custom_components.unban_ip.services import (
    async_setup_services,
    async_unload_services,
)
from custom_components.unban_ip.const import DOMAIN, IP_BANS_FILE


@pytest.mark.asyncio
async def test_service_registration(hass: HomeAssistant):
    """Test that the unban_ip service registers correctly."""
    await async_setup_services(hass)
    assert hass.services.has_service(DOMAIN, "unban_ip")

    await async_unload_services(hass)
    assert not hass.services.has_service(DOMAIN, "unban_ip")


@pytest.mark.asyncio
async def test_unban_ip_removes_from_file_and_memory(hass: HomeAssistant, tmp_path, monkeypatch, ban_file):
    """Test that unban_ip removes the IP from the file and memory."""

    # Mock hass.config.path to return the temp file path
    monkeypatch.setattr(hass.config, "path", lambda x: str(ban_file))

    # Create dummy in-memory ban list
    class DummyBan:
        def __init__(self):
            self.banned = {"192.168.1.25": "banned"}

    hass.data["http"] = type("dummy_http", (), {"_ban": DummyBan()})()

    # Register service
    await async_setup_services(hass)

    # Call service
    await hass.services.async_call(
        DOMAIN,
        "unban_ip",
        {"ip_address": "192.168.1.25"},
        blocking=True,
    )

    # Check file
    with open(ban_file, "r") as f:
        data = yaml.safe_load(f)
    ips = [b["ip_address"] for b in data]
    assert "192.168.1.25" not in ips

    # Check in-memory ban list
    assert "192.168.1.25" not in hass.data["http"]._ban.banned


@pytest.mark.asyncio
async def test_reload_services(hass: HomeAssistant):
    """Test that reload correctly unloads and reloads services."""
    from custom_components.unban_ip import async_reload_entry

    await async_setup_services(hass)
    assert hass.services.has_service(DOMAIN, "unban_ip")

    await async_reload_entry(hass, None)
    assert hass.services.has_service(DOMAIN, "unban_ip")
