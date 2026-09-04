from agent.orchestrator import IOOperationsOrchestrator


def test_orchestrator_class_can_be_imported():
    assert IOOperationsOrchestrator is not None


def test_orchestrator_can_be_instantiated():
    orchestrator = IOOperationsOrchestrator()
    assert orchestrator is not None


def test_resolve_system_resolves_mocked_system(monkeypatch):
    fake_inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service",
            "application": "test-payment-service",
        }
    ]
    monkeypatch.setattr(
        "agent.orchestrator.get_system_inventory",
        lambda query="": fake_inventory,
    )

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.resolve_system("What is wrong with Test Payment Service?")

    assert result["status"] == "resolved"
    assert result["system_name"] == "Test Payment Service"


def test_resolve_system_unknown_system_returns_unresolved(monkeypatch):
    fake_inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service",
            "application": "test-payment-service",
        }
    ]
    monkeypatch.setattr(
        "agent.orchestrator.get_system_inventory",
        lambda query="": fake_inventory,
    )

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.resolve_system("What is wrong with Test Refund Service?")

    assert result["status"] == "unresolved"
    assert "system_name" not in result


def test_resolve_system_ambiguous_matches_returns_ambiguous(monkeypatch):
    fake_inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service A",
            "application": "test-payment-service-a",
        },
        {
            "system_id": "SYS-TEST-002",
            "system_name": "Test Payment Service B",
            "application": "test-payment-service-b",
        },
    ]
    monkeypatch.setattr(
        "agent.orchestrator.get_system_inventory",
        lambda query="": fake_inventory,
    )

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.resolve_system(
        "Compare Test Payment Service A and Test Payment Service B"
    )

    assert result["status"] == "ambiguous"
    candidates = result["candidates"]
    assert "Test Payment Service A" in candidates
    assert "Test Payment Service B" in candidates
    assert "system_name" not in result


def test_resolve_time_window_explicit_date_and_time():
    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.resolve_time_window(
        "Check Test Service on 2026-09-10 14:30."
    )

    assert result["status"] == "resolved"
    point = result["point"]
    assert "2026-09-10" in point
    assert "14:30" in point


def test_resolve_time_window_explicit_time_range():
    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.resolve_time_window(
        "Analyze Test Service from 2026-09-10 10:00 to 2026-09-10 10:30."
    )

    assert result["status"] == "resolved"
    assert "2026-09-10" in result["start"]
    assert "10:00" in result["start"]
    assert "2026-09-10" in result["end"]
    assert "10:30" in result["end"]


def test_resolve_time_window_from_time_on_date_preserves_both():
    """'from 14:00 on 2026-08-25' must resolve to start with both date and time."""
    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.resolve_time_window(
        "Internet Banking is slow from 14:00 on 2026-08-25. What is the cause?"
    )

    assert result["status"] == "resolved"
    assert "start" in result
    assert "end" not in result
    assert "2026-08-25" in result["start"]
    assert "14:00" in result["start"]


def test_resolve_time_window_from_around_time_on_date_preserves_both():
    """'from around 14:00 on 2026-08-25' must resolve to start with both date and time."""
    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.resolve_time_window(
        "Internet Banking is slow from around 14:00 on 2026-08-25. What is the cause?"
    )

    assert result["status"] == "resolved"
    assert "start" in result
    assert "end" not in result
    assert "2026-08-25" in result["start"]
    assert "14:00" in result["start"]


def test_resolve_time_window_vietnamese_tu_time_ngay_date_preserves_both():
    """'từ 14:00 ngày 2026-08-25' must resolve to start with both date and time."""
    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.resolve_time_window(
        "Internet Banking đang chậm từ 14:00 ngày 2026-08-25. Kiểm tra nguyên nhân?"
    )

    assert result["status"] == "resolved"
    assert "start" in result
    assert "end" not in result
    assert "2026-08-25" in result["start"]
    assert "14:00" in result["start"]


def test_resolve_time_window_vietnamese_tu_khoang_time_ngay_date_preserves_both():
    """'từ khoảng 14:00 ngày 2026-08-25' must resolve to start with both date and time."""
    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.resolve_time_window(
        "Internet Banking đang chậm từ khoảng 14:00 ngày 2026-08-25. "
        "Kiểm tra giúp tôi nguyên nhân có thể nằm ở đâu?"
    )

    assert result["status"] == "resolved"
    assert "start" in result
    assert "end" not in result
    assert "2026-08-25" in result["start"]
    assert "14:00" in result["start"]


def test_resolve_time_window_insufficient_info_returns_unresolved():
    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.resolve_time_window("Check Test Service performance.")

    assert result["status"] == "unresolved"
    assert "start" not in result
    assert "end" not in result
    assert "point" not in result


def test_collect_inventory_found_returns_mocked_inventory(monkeypatch):
    fake_inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service",
            "application": "test-app-01",
            "vm": "test-vm-01",
            "host": "test-host-01",
            "cluster": "test-cluster-01",
            "datastore": "test-datastore-01",
            "storage_pool": "test-storage-pool-01",
            "network_zone": "test-zone-01",
        }
    ]
    call_args = []

    def fake_get_system_inventory(query=""):
        call_args.append(query)
        return fake_inventory

    monkeypatch.setattr(
        "agent.orchestrator.get_system_inventory", fake_get_system_inventory
    )

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.collect_inventory("Test Payment Service")

    assert call_args == ["Test Payment Service"]
    assert result == fake_inventory
    assert result[0]["system_id"] == "SYS-TEST-001"
    assert result[0]["system_name"] == "Test Payment Service"
    assert result[0]["application"] == "test-app-01"
    assert result[0]["vm"] == "test-vm-01"
    assert result[0]["host"] == "test-host-01"
    assert result[0]["cluster"] == "test-cluster-01"
    assert result[0]["datastore"] == "test-datastore-01"
    assert result[0]["storage_pool"] == "test-storage-pool-01"
    assert result[0]["network_zone"] == "test-zone-01"
    assert len(result) == 1


def test_collect_inventory_not_found_returns_empty(monkeypatch):
    monkeypatch.setattr(
        "agent.orchestrator.get_system_inventory", lambda query="": []
    )

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.collect_inventory("Test Payment Service")

    assert result == []
    assert len(result) == 0


def test_collect_operational_evidence_application_only(monkeypatch):
    fake_app_metrics = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "response_time_ms": 220,
            "error_rate_pct": 0.5,
            "db_connection_pool_pct": 45,
            "thread_pool_pct": 40,
        },
        {
            "timestamp": "2026-09-10T10:05:00",
            "response_time_ms": 260,
            "error_rate_pct": 0.7,
            "db_connection_pool_pct": 48,
            "thread_pool_pct": 43,
        },
    ]
    app_calls = []

    def fake_get_application_metrics(
        system_id=None, application=None, start_time=None, end_time=None
    ):
        app_calls.append(
            {
                "system_id": system_id,
                "application": application,
                "start_time": start_time,
                "end_time": end_time,
            }
        )
        return fake_app_metrics

    monkeypatch.setattr(
        "agent.orchestrator.get_application_metrics", fake_get_application_metrics
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_server_metrics",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_vmware_metrics",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_storage_metrics",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_network_metrics",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_monitoring_alerts",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        "agent.orchestrator.search_application_logs",
        lambda **kwargs: [],
    )

    inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service",
            "application": "test-app-01",
        }
    ]
    time_window = {
        "status": "resolved",
        "start": "2026-09-10 10:00",
        "end": "2026-09-10 10:05",
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.collect_operational_evidence(inventory, time_window)

    assert len(app_calls) >= 1
    assert all(item in result["application"] for item in fake_app_metrics)
    assert len(result["application"]) == len(app_calls) * len(fake_app_metrics)
    assert result["server"] == []
    assert result["vmware"] == []
    assert result["storage"] == []
    assert result["network"] == []
    assert result["alerts"] == []
    assert result["logs"] == []


def test_collect_operational_evidence_server_and_vmware_only(monkeypatch):
    fake_server_metrics = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "cpu_pct": 35,
            "memory_pct": 48,
            "disk_usage_pct": 52,
        },
        {
            "timestamp": "2026-09-10T10:05:00",
            "cpu_pct": 38,
            "memory_pct": 50,
            "disk_usage_pct": 53,
        },
    ]
    fake_vmware_metrics = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "cpu_ready_pct": 1.2,
            "memory_balloon_mb": 0,
            "memory_swap_mb": 0,
        },
        {
            "timestamp": "2026-09-10T10:05:00",
            "cpu_ready_pct": 1.4,
            "memory_balloon_mb": 0,
            "memory_swap_mb": 0,
        },
    ]
    server_calls = []
    vmware_calls = []

    def fake_get_server_metrics(
        hostname=None, start_time=None, end_time=None
    ):
        server_calls.append(
            {"hostname": hostname, "start_time": start_time, "end_time": end_time}
        )
        return fake_server_metrics

    def fake_get_vmware_metrics(
        vm_name=None, esxi_host=None, cluster=None,
        start_time=None, end_time=None,
    ):
        vmware_calls.append(
            {
                "vm_name": vm_name,
                "esxi_host": esxi_host,
                "cluster": cluster,
                "start_time": start_time,
                "end_time": end_time,
            }
        )
        return fake_vmware_metrics

    monkeypatch.setattr(
        "agent.orchestrator.get_application_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_server_metrics", fake_get_server_metrics
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_vmware_metrics", fake_get_vmware_metrics
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_storage_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_network_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_monitoring_alerts", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.search_application_logs", lambda **kwargs: []
    )

    inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service",
            "hostname": "test-host-01",
            "vm_name": "test-vm-01",
        }
    ]
    time_window = {
        "status": "resolved",
        "start": "2026-09-10 10:00",
        "end": "2026-09-10 10:05",
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.collect_operational_evidence(inventory, time_window)

    assert len(server_calls) >= 1
    assert len(vmware_calls) >= 1
    assert all(item in result["server"] for item in fake_server_metrics)
    assert len(result["server"]) == len(server_calls) * len(fake_server_metrics)
    assert all(item in result["vmware"] for item in fake_vmware_metrics)
    assert len(result["vmware"]) == len(vmware_calls) * len(fake_vmware_metrics)
    assert result["application"] == []
    assert result["storage"] == []
    assert result["network"] == []
    assert result["alerts"] == []
    assert result["logs"] == []


def test_collect_operational_evidence_storage_and_network_only(monkeypatch):
    fake_storage_metrics = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "latency_ms": 2.5,
            "iops": 4200,
            "throughput_mbps": 180,
            "capacity_used_pct": 62,
        },
        {
            "timestamp": "2026-09-10T10:05:00",
            "latency_ms": 3.0,
            "iops": 4500,
            "throughput_mbps": 195,
            "capacity_used_pct": 62,
        },
    ]
    fake_network_metrics = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "latency_ms": 4,
            "packet_loss_pct": 0.0,
            "interface_utilization_pct": 28,
        },
        {
            "timestamp": "2026-09-10T10:05:00",
            "latency_ms": 5,
            "packet_loss_pct": 0.1,
            "interface_utilization_pct": 31,
        },
    ]
    storage_calls = []
    network_calls = []

    def fake_get_storage_metrics(
        storage_pool=None, datastore=None, start_time=None, end_time=None
    ):
        storage_calls.append(
            {
                "storage_pool": storage_pool,
                "datastore": datastore,
                "start_time": start_time,
                "end_time": end_time,
            }
        )
        return fake_storage_metrics

    def fake_get_network_metrics(
        network_zone=None, device=None, endpoint=None,
        start_time=None, end_time=None,
    ):
        network_calls.append(
            {
                "network_zone": network_zone,
                "device": device,
                "endpoint": endpoint,
                "start_time": start_time,
                "end_time": end_time,
            }
        )
        return fake_network_metrics

    monkeypatch.setattr(
        "agent.orchestrator.get_application_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_server_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_vmware_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_storage_metrics", fake_get_storage_metrics
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_network_metrics", fake_get_network_metrics
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_monitoring_alerts", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.search_application_logs", lambda **kwargs: []
    )

    inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service",
            "storage_pool": "test-storage-pool-01",
            "network_zone": "test-zone-01",
        }
    ]
    time_window = {
        "status": "resolved",
        "start": "2026-09-10 10:00",
        "end": "2026-09-10 10:05",
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.collect_operational_evidence(inventory, time_window)

    assert len(storage_calls) >= 1
    assert len(network_calls) >= 1
    assert all(item in result["storage"] for item in fake_storage_metrics)
    assert len(result["storage"]) == len(storage_calls) * len(fake_storage_metrics)
    assert all(item in result["network"] for item in fake_network_metrics)
    assert len(result["network"]) == len(network_calls) * len(fake_network_metrics)
    assert result["application"] == []
    assert result["server"] == []
    assert result["vmware"] == []
    assert result["alerts"] == []
    assert result["logs"] == []


def test_collect_operational_evidence_alerts_and_logs_only(monkeypatch):
    fake_alerts = [
        {
            "timestamp": "2026-09-10T10:02:00",
            "severity": "warning",
            "source": "test-monitor",
            "component": "test-app-01",
            "alert_name": "High Response Time",
            "message": "Response time exceeded expected operating range",
        },
        {
            "timestamp": "2026-09-10T10:04:00",
            "severity": "critical",
            "source": "test-monitor",
            "component": "test-app-01",
            "alert_name": "Application Error Rate",
            "message": "Application error rate increased",
        },
    ]
    fake_logs = [
        {
            "timestamp": "2026-09-10T10:03:00",
            "level": "WARN",
            "component": "test-app-01",
            "message": "Request processing time increased",
        },
        {
            "timestamp": "2026-09-10T10:04:30",
            "level": "ERROR",
            "component": "test-app-01",
            "message": "Request processing failed",
        },
    ]
    alert_calls = []
    log_calls = []

    def fake_get_monitoring_alerts(
        system_id=None, start_time=None, end_time=None
    ):
        alert_calls.append(
            {
                "system_id": system_id,
                "start_time": start_time,
                "end_time": end_time,
            }
        )
        return fake_alerts

    def fake_search_application_logs(
        application=None, start_time=None, end_time=None
    ):
        log_calls.append(
            {
                "application": application,
                "start_time": start_time,
                "end_time": end_time,
            }
        )
        return fake_logs

    monkeypatch.setattr(
        "agent.orchestrator.get_application_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_server_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_vmware_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_storage_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_network_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_monitoring_alerts", fake_get_monitoring_alerts
    )
    monkeypatch.setattr(
        "agent.orchestrator.search_application_logs", fake_search_application_logs
    )

    inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service",
            "application": "test-app-01",
        }
    ]
    time_window = {
        "status": "resolved",
        "start": "2026-09-10 10:00",
        "end": "2026-09-10 10:05",
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.collect_operational_evidence(inventory, time_window)

    assert len(alert_calls) >= 1
    assert len(log_calls) >= 1
    assert all(item in result["alerts"] for item in fake_alerts)
    assert len(result["alerts"]) == len(alert_calls) * len(fake_alerts)
    assert all(item in result["logs"] for item in fake_logs)
    assert len(result["logs"]) == len(log_calls) * len(fake_logs)
    assert result["application"] == []
    assert result["server"] == []
    assert result["vmware"] == []
    assert result["storage"] == []
    assert result["network"] == []


def test_collect_operational_evidence_aggregate_all_domains(monkeypatch):
    fake_app = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "response_time_ms": 200,
            "error_rate_pct": 0.3,
        }
    ]
    fake_server = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "cpu_pct": 30,
            "memory_pct": 45,
        }
    ]
    fake_vmware = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "cpu_ready_pct": 1.0,
            "memory_balloon_mb": 0,
        }
    ]
    fake_storage = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "latency_ms": 2.0,
            "iops": 4000,
        }
    ]
    fake_network = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "latency_ms": 3,
            "packet_loss_pct": 0.0,
        }
    ]
    fake_alerts = [
        {
            "timestamp": "2026-09-10T10:01:00",
            "severity": "warning",
            "alert_name": "High Response Time",
            "message": "Response time elevated",
        }
    ]
    fake_logs = [
        {
            "timestamp": "2026-09-10T10:01:30",
            "level": "WARN",
            "message": "Request processing slow",
        }
    ]
    app_calls = []
    server_calls = []
    vmware_calls = []
    storage_calls = []
    network_calls = []
    alert_calls = []
    log_calls = []

    monkeypatch.setattr(
        "agent.orchestrator.get_application_metrics",
        lambda **kwargs: (app_calls.append(kwargs) or fake_app),
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_server_metrics",
        lambda **kwargs: (server_calls.append(kwargs) or fake_server),
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_vmware_metrics",
        lambda **kwargs: (vmware_calls.append(kwargs) or fake_vmware),
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_storage_metrics",
        lambda **kwargs: (storage_calls.append(kwargs) or fake_storage),
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_network_metrics",
        lambda **kwargs: (network_calls.append(kwargs) or fake_network),
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_monitoring_alerts",
        lambda **kwargs: (alert_calls.append(kwargs) or fake_alerts),
    )
    monkeypatch.setattr(
        "agent.orchestrator.search_application_logs",
        lambda **kwargs: (log_calls.append(kwargs) or fake_logs),
    )

    inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service",
            "application": "test-app-01",
            "hostname": "test-host-01",
            "vm_name": "test-vm-01",
            "storage_pool": "test-storage-pool-01",
            "network_zone": "test-zone-01",
        }
    ]
    time_window = {
        "status": "resolved",
        "start": "2026-09-10 10:00",
        "end": "2026-09-10 10:05",
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.collect_operational_evidence(inventory, time_window)

    assert len(app_calls) >= 1
    assert len(server_calls) >= 1
    assert len(vmware_calls) >= 1
    assert len(storage_calls) >= 1
    assert len(network_calls) >= 1
    assert len(alert_calls) >= 1
    assert len(log_calls) >= 1

    expected_domains = {
        "application": fake_app,
        "server": fake_server,
        "vmware": fake_vmware,
        "storage": fake_storage,
        "network": fake_network,
        "alerts": fake_alerts,
        "logs": fake_logs,
    }
    for domain, fake_data in expected_domains.items():
        assert all(item in result[domain] for item in fake_data)

    assert all(item in result["application"] for item in fake_app)
    assert all(item in result["server"] for item in fake_server)
    assert all(item in result["vmware"] for item in fake_vmware)
    assert all(item in result["storage"] for item in fake_storage)
    assert all(item in result["network"] for item in fake_network)
    assert all(item in result["alerts"] for item in fake_alerts)
    assert all(item in result["logs"] for item in fake_logs)


def test_collect_operational_evidence_missing_domains_safe(monkeypatch):
    fake_app = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "response_time_ms": 200,
            "error_rate_pct": 0.3,
        }
    ]
    fake_server = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "cpu_pct": 30,
            "memory_pct": 45,
        }
    ]
    fake_network = [
        {
            "timestamp": "2026-09-10T10:00:00",
            "latency_ms": 3,
            "packet_loss_pct": 0.0,
        }
    ]

    monkeypatch.setattr(
        "agent.orchestrator.get_application_metrics", lambda **kwargs: fake_app
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_server_metrics", lambda **kwargs: fake_server
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_vmware_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_storage_metrics", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_network_metrics", lambda **kwargs: fake_network
    )
    monkeypatch.setattr(
        "agent.orchestrator.get_monitoring_alerts", lambda **kwargs: []
    )
    monkeypatch.setattr(
        "agent.orchestrator.search_application_logs", lambda **kwargs: []
    )

    inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service",
            "application": "test-app-01",
            "hostname": "test-host-01",
            "vm_name": "test-vm-01",
            "storage_pool": "test-storage-pool-01",
            "network_zone": "test-zone-01",
        }
    ]
    time_window = {
        "status": "resolved",
        "start": "2026-09-10 10:00",
        "end": "2026-09-10 10:05",
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.collect_operational_evidence(inventory, time_window)

    assert all(item in result["application"] for item in fake_app)
    assert all(item in result["server"] for item in fake_server)
    assert all(item in result["network"] for item in fake_network)

    assert result["vmware"] == []
    assert result["storage"] == []
    assert result["alerts"] == []
    assert result["logs"] == []

    assert "rca" not in result
    assert "root_cause" not in result
    assert "health" not in result
    assert "threshold" not in result


def test_collect_operational_evidence_open_ended_start_gets_30min_window(monkeypatch):
    """A. Open-ended start (start set, end=None) produces a 30-minute effective window."""
    captured_calls = []

    def fake_get_application_metrics(
        system_id=None, application=None, start_time=None, end_time=None
    ):
        captured_calls.append({"start_time": start_time, "end_time": end_time})
        return []

    monkeypatch.setattr(
        "agent.orchestrator.get_application_metrics", fake_get_application_metrics
    )
    monkeypatch.setattr("agent.orchestrator.get_server_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_vmware_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_storage_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_network_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_monitoring_alerts", lambda **kwargs: [])
    monkeypatch.setattr(
        "agent.orchestrator.search_application_logs", lambda **kwargs: []
    )

    inventory = [{"system_id": "SYS-TEST-001", "application": "test-app"}]
    time_window = {"status": "resolved", "start": "2026-08-25 14:00"}

    orchestrator = IOOperationsOrchestrator()
    orchestrator.collect_operational_evidence(inventory, time_window)

    assert len(captured_calls) >= 1
    assert captured_calls[0]["start_time"] == "2026-08-25 14:00"
    assert captured_calls[0]["end_time"] == "2026-08-25 14:30"


def test_collect_operational_evidence_explicit_range_preserved(monkeypatch):
    """B. Explicit start+end range is preserved exactly (no default window applied)."""
    captured_calls = []

    def fake_get_application_metrics(
        system_id=None, application=None, start_time=None, end_time=None
    ):
        captured_calls.append({"start_time": start_time, "end_time": end_time})
        return []

    monkeypatch.setattr(
        "agent.orchestrator.get_application_metrics", fake_get_application_metrics
    )
    monkeypatch.setattr("agent.orchestrator.get_server_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_vmware_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_storage_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_network_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_monitoring_alerts", lambda **kwargs: [])
    monkeypatch.setattr(
        "agent.orchestrator.search_application_logs", lambda **kwargs: []
    )

    inventory = [{"system_id": "SYS-TEST-001", "application": "test-app"}]
    time_window = {
        "status": "resolved",
        "start": "2026-08-25 14:00",
        "end": "2026-08-25 15:00",
    }

    orchestrator = IOOperationsOrchestrator()
    orchestrator.collect_operational_evidence(inventory, time_window)

    assert len(captured_calls) >= 1
    assert captured_calls[0]["start_time"] == "2026-08-25 14:00"
    assert captured_calls[0]["end_time"] == "2026-08-25 15:00"


def test_collect_operational_evidence_after_effective_end_excluded(monkeypatch):
    """C. Evidence after effective_end (start + 30min) is excluded."""
    from tools._common import parse_timestamp

    all_records = [
        {"timestamp": "2026-08-25 14:00:00", "response_time_ms": 420},
        {"timestamp": "2026-08-25 14:10:00", "response_time_ms": 1200},
        {"timestamp": "2026-08-25 14:25:00", "response_time_ms": 520},
        {"timestamp": "2026-08-25 14:30:00", "response_time_ms": 300},
        {"timestamp": "2026-08-25 14:35:00", "response_time_ms": 280},
        {"timestamp": "2026-08-26 10:00:00", "response_time_ms": 550},
    ]

    def fake_get_application_metrics(
        system_id=None, application=None, start_time=None, end_time=None
    ):
        start_dt = parse_timestamp(start_time) if start_time else None
        end_dt = parse_timestamp(end_time) if end_time else None
        result = []
        for rec in all_records:
            ts = parse_timestamp(rec["timestamp"])
            if start_dt and ts < start_dt:
                continue
            if end_dt and ts > end_dt:
                continue
            result.append(rec)
        return result

    monkeypatch.setattr(
        "agent.orchestrator.get_application_metrics", fake_get_application_metrics
    )
    monkeypatch.setattr("agent.orchestrator.get_server_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_vmware_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_storage_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_network_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_monitoring_alerts", lambda **kwargs: [])
    monkeypatch.setattr(
        "agent.orchestrator.search_application_logs", lambda **kwargs: []
    )

    inventory = [{"system_id": "SYS-TEST-001", "application": "test-app"}]
    time_window = {"status": "resolved", "start": "2026-08-25 14:00"}

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.collect_operational_evidence(inventory, time_window)

    timestamps = [r["timestamp"] for r in result["application"]]
    assert "2026-08-25 14:00:00" in timestamps
    assert "2026-08-25 14:10:00" in timestamps
    assert "2026-08-25 14:25:00" in timestamps
    assert "2026-08-25 14:30:00" in timestamps
    assert "2026-08-25 14:35:00" not in timestamps
    assert "2026-08-26 10:00:00" not in timestamps


def test_collect_operational_evidence_point_in_time_unchanged(monkeypatch):
    """D. Point-in-time behavior (start=end=point) is unchanged."""
    captured_calls = []

    def fake_get_application_metrics(
        system_id=None, application=None, start_time=None, end_time=None
    ):
        captured_calls.append({"start_time": start_time, "end_time": end_time})
        return []

    monkeypatch.setattr(
        "agent.orchestrator.get_application_metrics", fake_get_application_metrics
    )
    monkeypatch.setattr("agent.orchestrator.get_server_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_vmware_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_storage_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_network_metrics", lambda **kwargs: [])
    monkeypatch.setattr("agent.orchestrator.get_monitoring_alerts", lambda **kwargs: [])
    monkeypatch.setattr(
        "agent.orchestrator.search_application_logs", lambda **kwargs: []
    )

    inventory = [{"system_id": "SYS-TEST-001", "application": "test-app"}]
    time_window = {"status": "resolved", "point": "2026-08-25 14:00"}

    orchestrator = IOOperationsOrchestrator()
    orchestrator.collect_operational_evidence(inventory, time_window)

    assert len(captured_calls) >= 1
    assert captured_calls[0]["start_time"] == "2026-08-25 14:00"
    assert captured_calls[0]["end_time"] == "2026-08-25 14:00"


def test_retrieve_knowledge_through_mocked_dependency(monkeypatch):
    fake_standard = {
        "type": "standard",
        "title": "Test Application Performance Standard",
        "source": "TEST-STD-001",
        "content": "Generic application performance operating guidance.",
        "file_name": "test_std_001.md",
    }
    fake_runbook = {
        "type": "runbook",
        "title": "Test Application Troubleshooting Runbook",
        "source": "TEST-RUN-001",
        "content": "Generic troubleshooting procedure.",
        "file_name": "test_run_001.md",
    }
    search_calls = []

    def fake_search_knowledge_documents(keyword=None, doc_type=None):
        search_calls.append({"keyword": keyword, "doc_type": doc_type})
        if doc_type == "standard":
            return [fake_standard]
        elif doc_type == "runbook":
            return [fake_runbook]
        return []

    monkeypatch.setattr(
        "agent.orchestrator.search_knowledge_documents",
        fake_search_knowledge_documents,
    )
    monkeypatch.setattr(
        "agent.orchestrator.list_knowledge_documents", lambda: []
    )

    evidence = {
        "application": [
            {
                "timestamp": "2026-09-10T10:00:00",
                "response_time_ms": 200,
                "message": "Response latency increased for test payment service",
            }
        ],
        "server": [],
        "vmware": [],
        "storage": [],
        "network": [],
        "alerts": [],
        "logs": [],
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.retrieve_knowledge(evidence)

    assert len(search_calls) >= 1
    assert "standards" in result
    assert "runbooks" in result
    assert len(result["standards"]) >= 1
    assert len(result["runbooks"]) >= 1
    std = result["standards"][0]
    assert std["title"] == "Test Application Performance Standard"
    assert std["source"] == "TEST-STD-001"
    assert std["content"] == "Generic application performance operating guidance."
    run = result["runbooks"][0]
    assert run["title"] == "Test Application Troubleshooting Runbook"
    assert run["source"] == "TEST-RUN-001"
    assert run["content"] == "Generic troubleshooting procedure."


def test_retrieve_knowledge_empty_result_safe(monkeypatch):
    monkeypatch.setattr(
        "agent.orchestrator.search_knowledge_documents",
        lambda keyword=None, doc_type=None: [],
    )
    monkeypatch.setattr(
        "agent.orchestrator.list_knowledge_documents", lambda: []
    )

    evidence = {
        "application": [
            {
                "timestamp": "2026-09-10T10:00:00",
                "response_time_ms": 200,
                "message": "Response latency increased for test payment service",
            }
        ],
        "server": [],
        "vmware": [],
        "storage": [],
        "network": [],
        "alerts": [],
        "logs": [],
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.retrieve_knowledge(evidence)

    assert "standards" in result
    assert "runbooks" in result
    assert result["standards"] == []
    assert result["runbooks"] == []
    assert "rca" not in result
    assert "root_cause" not in result
    assert "health" not in result
    assert "threshold" not in result


def test_retrieve_knowledge_deterministic_keyword_order(monkeypatch):
    search_calls = []

    def fake_search_knowledge_documents(keyword=None, doc_type=None):
        search_calls.append({"keyword": keyword, "doc_type": doc_type})
        return []

    monkeypatch.setattr(
        "agent.orchestrator.search_knowledge_documents",
        fake_search_knowledge_documents,
    )
    monkeypatch.setattr(
        "agent.orchestrator.list_knowledge_documents", lambda: []
    )

    evidence = {
        "application": [
            {"message": "payment transaction timeout"}
        ],
        "server": [
            {"message": "database pool utilization"}
        ],
        "vmware": [],
        "storage": [],
        "network": [],
        "alerts": [
            {"message": "disk latency elevated"}
        ],
        "logs": [
            {"message": "request processing failed"}
        ],
    }

    orchestrator = IOOperationsOrchestrator()
    orchestrator.retrieve_knowledge(evidence)

    keywords_sent = [
        call["keyword"] for call in search_calls if call["doc_type"] == "standard"
    ]

    assert len(keywords_sent) >= 1
    assert len(keywords_sent) <= 30
    assert len(keywords_sent) == len(set(keywords_sent))

    assert "application" in keywords_sent
    assert "server" in keywords_sent
    assert "alerts" in keywords_sent
    assert "logs" in keywords_sent

    assert keywords_sent.index("application") < keywords_sent.index("server")
    assert keywords_sent.index("server") < keywords_sent.index("alerts")
    assert keywords_sent.index("alerts") < keywords_sent.index("logs")

    sorted_keywords = sorted(keywords_sent)
    assert keywords_sent != sorted_keywords


def test_build_grounded_context_complete(monkeypatch):
    user_question = "What is causing slow response in Test Payment Service?"
    inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service",
            "application": "test-app-01",
            "hostname": "test-host-01",
        }
    ]
    evidence = {
        "application": [
            {
                "timestamp": "2026-09-10T10:00:00",
                "response_time_ms": 250,
                "message": "Response time elevated",
            }
        ],
        "server": [
            {
                "timestamp": "2026-09-10T10:00:00",
                "cpu_pct": 35,
                "memory_pct": 48,
            }
        ],
        "vmware": [],
        "storage": [
            {
                "timestamp": "2026-09-10T10:00:00",
                "latency_ms": 3.0,
                "iops": 4500,
            }
        ],
        "network": [],
        "alerts": [
            {
                "timestamp": "2026-09-10T10:01:00",
                "severity": "warning",
                "alert_name": "High Response Time",
                "message": "Response time exceeded expected range",
            }
        ],
        "logs": [
            {
                "timestamp": "2026-09-10T10:01:30",
                "level": "WARN",
                "message": "Request processing slow",
            }
        ],
    }
    knowledge = {
        "standards": [
            {
                "file_name": "test_std_001.md",
                "title": "Test Application Performance Standard",
                "content": "Generic application performance operating guidance.",
            }
        ],
        "runbooks": [
            {
                "file_name": "test_run_001.md",
                "title": "Test Troubleshooting Runbook",
                "content": "Generic troubleshooting procedure.",
            }
        ],
    }
    time_window = {
        "status": "resolved",
        "start": "2026-09-10 10:00",
        "end": "2026-09-10 10:05",
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.build_grounded_context(
        user_question, inventory, evidence, knowledge, time_window
    )

    assert result["user_request"] == user_question
    assert "Test Payment Service" in result["system_service_scope"]["system_names"]
    assert result["system_service_scope"]["inventory_count"] == 1
    assert result["analysis_time_window"] == time_window
    assert result["system_inventory_topology"] == inventory
    assert result["operational_evidence"]["application"] == evidence["application"]
    assert result["operational_evidence"]["server"] == evidence["server"]
    assert result["operational_evidence"]["storage"] == evidence["storage"]
    assert result["operational_evidence"]["alerts"] == evidence["alerts"]
    assert result["operational_evidence"]["logs"] == evidence["logs"]
    assert result["retrieved_knowledge"]["standards"] == knowledge["standards"]
    assert result["retrieved_knowledge"]["runbooks"] == knowledge["runbooks"]
    assert result["retrieved_knowledge"]["standards"][0]["title"] == "Test Application Performance Standard"
    assert result["retrieved_knowledge"]["runbooks"][0]["title"] == "Test Troubleshooting Runbook"


def test_build_grounded_context_missing_evidence_and_knowledge(monkeypatch):
    user_question = "What is causing slow response in Test Payment Service?"
    inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service",
            "application": "test-app-01",
        }
    ]
    evidence = {
        "application": [
            {
                "timestamp": "2026-09-10T10:00:00",
                "response_time_ms": 250,
            }
        ],
        "server": [],
        "vmware": [],
        "storage": [],
        "network": [],
        "alerts": [],
        "logs": [],
    }
    knowledge = {"standards": [], "runbooks": []}
    time_window = {
        "status": "resolved",
        "start": "2026-09-10 10:00",
        "end": "2026-09-10 10:05",
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.build_grounded_context(
        user_question, inventory, evidence, knowledge, time_window
    )

    assert result["operational_evidence"]["application"] == evidence["application"]
    assert result["operational_evidence"]["server"] == []
    assert result["operational_evidence"]["vmware"] == []
    assert result["operational_evidence"]["storage"] == []
    assert result["operational_evidence"]["network"] == []
    assert result["operational_evidence"]["alerts"] == []
    assert result["operational_evidence"]["logs"] == []
    assert result["retrieved_knowledge"]["standards"] == []
    assert result["retrieved_knowledge"]["runbooks"] == []
    assert isinstance(result["evidence_gaps"], list)
    assert any("server" in gap for gap in result["evidence_gaps"])
    assert any("vmware" in gap for gap in result["evidence_gaps"])
    assert any("storage" in gap for gap in result["evidence_gaps"])
    assert any("alerts" in gap for gap in result["evidence_gaps"])
    assert any("logs" in gap for gap in result["evidence_gaps"])


def test_build_grounded_context_contains_no_reasoning_output(monkeypatch):
    user_question = "What is causing slow response in Test Payment Service?"
    inventory = [
        {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Payment Service",
            "application": "test-app-01",
        }
    ]
    evidence = {
        "application": [
            {
                "timestamp": "2026-09-10T10:00:00",
                "response_time_ms": 500,
                "message": "Response time elevated",
            }
        ],
        "server": [],
        "vmware": [],
        "storage": [
            {
                "timestamp": "2026-09-10T10:00:00",
                "latency_ms": 15.0,
                "message": "Storage latency increased",
            }
        ],
        "network": [],
        "alerts": [],
        "logs": [
            {
                "timestamp": "2026-09-10T10:01:00",
                "level": "ERROR",
                "message": "Request processing failed",
            }
        ],
    }
    knowledge = {"standards": [], "runbooks": []}
    time_window = {
        "status": "resolved",
        "start": "2026-09-10 10:00",
        "end": "2026-09-10 10:05",
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.build_grounded_context(
        user_question, inventory, evidence, knowledge, time_window
    )

    reasoning_keys = [
        "root_cause",
        "rca",
        "rca_hypothesis",
        "recommendation",
        "confidence",
        "overall_health",
        "findings",
        "affected_components",
        "threshold",
        "assessment",
    ]
    for key in reasoning_keys:
        assert key not in result, f"Unexpected reasoning key '{key}' in grounded context"

    assert set(result.keys()) == {
        "user_request",
        "system_service_scope",
        "analysis_time_window",
        "system_inventory_topology",
        "operational_evidence",
        "retrieved_knowledge",
        "evidence_gaps",
    }

    assert result["operational_evidence"]["application"] == evidence["application"]
    assert result["operational_evidence"]["storage"] == evidence["storage"]
    assert result["operational_evidence"]["logs"] == evidence["logs"]



def test_generate_response(monkeypatch):
    import agent.orchestrator as orchestrator_module

    chat_calls = []

    class MockClient:
        def __init__(self, config):
            self.config = config

        def chat(self, user_message=None, system_prompt=None):
            chat_calls.append({"user_message": user_message, "system_prompt": system_prompt})
            return "Mock grounded analysis response"

    created_clients = []

    def mock_load_config():
        return object()

    def mock_green_node_client(config):
        client = MockClient(config)
        created_clients.append(client)
        return client

    monkeypatch.setattr(orchestrator_module, "load_config", mock_load_config)
    monkeypatch.setattr(orchestrator_module, "GreenNodeClient", mock_green_node_client)

    orchestrator = orchestrator_module.IOOperationsOrchestrator()

    grounded_context = {
        "request": "Analyze Test Service",
        "system": {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Service"
        },
        "time_window": {
            "start": "2026-09-10T10:00:00",
            "end": "2026-09-10T10:15:00"
        },
        "inventory": {
            "application": "test-app-01"
        },
        "operational_evidence": {
            "application": []
        },
        "knowledge": []
    }

    result = orchestrator.generate_response(grounded_context)

    assert len(created_clients) == 1
    assert len(chat_calls) == 1

    user_message = chat_calls[0]["user_message"]
    assert "SYS-TEST-001" in user_message
    assert "Test Service" in user_message
    assert "2026-09-10T10:00:00" in user_message

    assert chat_calls[0]["system_prompt"] == orchestrator_module.SYSTEM_PROMPT

    assert result["status"] == "ok"
    assert result["response"] == "Mock grounded analysis response"



def test_generate_response_error_path(monkeypatch):
    import agent.orchestrator as orchestrator_module

    chat_calls = []

    class MockClient:
        def __init__(self, config):
            self.config = config

        def chat(self, user_message=None, system_prompt=None):
            chat_calls.append({"user_message": user_message, "system_prompt": system_prompt})
            raise RuntimeError("mock GreenNode unavailable")

    created_clients = []

    def mock_load_config():
        return object()

    def mock_green_node_client(config):
        client = MockClient(config)
        created_clients.append(client)
        return client

    monkeypatch.setattr(orchestrator_module, "load_config", mock_load_config)
    monkeypatch.setattr(orchestrator_module, "GreenNodeClient", mock_green_node_client)

    orchestrator = orchestrator_module.IOOperationsOrchestrator()

    grounded_context = {
        "request": "Analyze Test Service",
        "system": {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Service"
        },
        "time_window": {
            "start": "2026-09-10T10:00:00",
            "end": "2026-09-10T10:15:00"
        },
        "inventory": {
            "application": "test-app-01"
        },
        "operational_evidence": {
            "application": []
        },
        "knowledge": []
    }

    result = orchestrator.generate_response(grounded_context)

    assert len(chat_calls) == 1

    assert result["status"] == "error"
    assert result["response"] is None

    message = result["message"]
    assert "GreenNode client error" in message
    assert "mock GreenNode unavailable" in message
