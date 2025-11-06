import pytest
import yaml
from homeassistant.core import HomeAssistant
from custom_components.unban_ip import async_setup
from custom_components.unban_ip.const import DOMAIN, IP_BANS_FILE


@pytest.fixture
async def setup_integration(hass):
    """Setup the integration and register the service."""
    await async_setup(hass, {})
    await hass.async_block_till_done()
    return hass


@pytest.fixture
def ban_file(tmp_path):
    """Create a temporary ip_bans.yaml file."""
    file_path = tmp_path / IP_BANS_FILE
    data = [
        {"ip_address": "192.168.1.25", "banned_at": "2025-11-06T21:42:12"},
        {"ip_address": "192.168.2.26", "banned_at": "2025-11-06T21:43:00"},
    ]
    with open(file_path, "w") as f:
        yaml.safe_dump(data, f)
    return file_path


async def test_unban_ip_service(
    hass: HomeAssistant, setup_integration, tmp_path, monkeypatch, ban_file
):
    """Test that unban_ip service removes the IP from file and in-memory bans."""

    # Mock hass.config.path to return our tmp_path file
    monkeypatch.setattr(hass.config, "path", lambda x: str(ban_file))

    # Create dummy in-memory _ban object
    class DummyBan:
        banned = {"192.168.1.25": "ban"}

    hass.data["http"] = type("dummy_http", (), {"_ban": DummyBan()})()

    # --- Call the registered service ---
    await hass.services.async_call(
        DOMAIN, "unban_ip", {"ip_address": "192.168.1.25"}, blocking=True
    )

    await hass.async_block_till_done()

    # --- Check file contents ---
    with open(ban_file, "r") as f:
        data = yaml.safe_load(f)
    assert all(b["ip_address"] != "192.168.1.25" for b in data)

    # --- Check in-memory removal ---
    assert "192.168.1.25" not in hass.data["http"]._ban.banned
