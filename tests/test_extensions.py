from app.extensions.manager import ExtensionManager


def test_extension_registry_and_persistence():
    manager = ExtensionManager(":memory:")
    ids = [item["id"] for item in manager.list_extensions()]
    assert ids == ["gmail", "drive", "calendar", "github", "notion"]
    assert all(item["connected"] is False for item in manager.list_extensions())
    manager._save_token("github", {"access_token": "x"})
    assert manager.list_extensions()[3]["connected"] is True
    manager.disconnect("github")
    assert manager.list_extensions()[3]["connected"] is False
