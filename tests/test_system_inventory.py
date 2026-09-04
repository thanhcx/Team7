"""Tests for ``tools/system_inventory.py``."""

from __future__ import annotations

from tools.system_inventory import get_system_inventory


class TestGetSystemInventory:
    def test_finds_internet_banking(self):
        results = get_system_inventory("Internet Banking")
        assert len(results) == 2
        assert all(r["system_id"] == "SYS-IB-001" for r in results)

    def test_case_insensitive(self):
        results = get_system_inventory("internet banking")
        assert len(results) == 2

    def test_partial_match(self):
        results = get_system_inventory("Banking")
        assert len(results) == 2

    def test_no_match_returns_empty(self):
        results = get_system_inventory("Nonexistent System")
        assert results == []

    def test_returns_dicts_with_expected_keys(self):
        results = get_system_inventory("Internet Banking")
        expected_keys = {
            "system_id", "system_name", "service_name", "application",
            "environment", "app_server", "vm_name", "esxi_host",
            "vmware_cluster", "datastore", "storage_pool",
            "network_zone", "owner_domain",
        }
        for row in results:
            assert set(row.keys()) == expected_keys

    def test_two_app_servers(self):
        results = get_system_inventory("Internet Banking")
        app_servers = {r["app_server"] for r in results}
        assert app_servers == {"APP01", "APP02"}

    def test_two_vms(self):
        results = get_system_inventory("Internet Banking")
        vm_names = {r["vm_name"] for r in results}
        assert vm_names == {"vm-app01", "vm-app02"}

    def test_relationships_intact(self):
        """Each row should link app_server → vm_name → esxi_host consistently."""
        results = get_system_inventory("Internet Banking")
        for row in results:
            if row["app_server"] == "APP01":
                assert row["vm_name"] == "vm-app01"
                assert row["esxi_host"] == "esxi-05"
            elif row["app_server"] == "APP02":
                assert row["vm_name"] == "vm-app02"
                assert row["esxi_host"] == "esxi-06"