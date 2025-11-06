import pytest
import yaml
from homeassistant.core import HomeAssistant

from custom_components.unban_ip.const import DOMAIN, IP_BANS_FILE

@pytest.fixture
def hass(loop, hass):
    """Fixture for Home Assistant instance."""
    return hass

@pytest.fixture
def ban_file(tmp_path):
    """Create a temporary ip_bans.yaml file."""
    file_path = tmp_path / "ip_bans.yaml"
    data = [
        {"ip_address": "192.168.1.25", "banned_at": "2025-11-06T21:42:12"},
        {"ip_address": "192.168.2.26", "banned_at": "2025-11-06T21:43:00"},
    ]
    with open(file_path, "w") as f:
        yaml.safe_dump(data, f)
    return file_path

@pytest.mark.asyncio
async def test_unban_ip_service(hass: HomeAssistant, tmp_path, monkeypatch, ban_file):
    """Test that unban_ip service removes the IP from file and in-memory bans."""

    # Mock hass.config.path to return our tmp_path file
    monkeypatch.setattr(hass.config, "path", lambda x: str(ban_file))

    # Create dummy in-memory _ban object
    class DummyBan:
        banned = {"192.168.1.25": "ban"}

    hass.data["http"] = type("dummy_http", (), {"_ban": DummyBan()})()

    # Setup service
    assert setup(hass, {}) is True

    # Call service
    await hass.services.async_call(
        DOMAIN,
        "unban_ip",
        {"ip_address": "192.168.1.25"},
        blocking=True
    )

    # Check file
    with open(ban_file, "r") as f:
        data = yaml.safe_load(f)
    assert all(b["ip_address"] != "192.168.1.25" for b in data)

    # Check in-memory
    assert "192.168.1.25" not in hass.data["http"]._ban.banned
