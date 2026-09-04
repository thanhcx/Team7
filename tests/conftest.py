"""Shared pytest fixtures for the I&O Operations Support Agent tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the project root is on sys.path so ``tools`` is importable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Reusable constants derived from the actual data files
# ---------------------------------------------------------------------------

#: The single system_id present in every operational data file.
SYSTEM_ID = "SYS-IB-001"

#: The application name used across application metrics, logs and alerts.
APPLICATION = "internet-banking"

#: The two application server hostnames.
HOST_APP01 = "APP01"
HOST_APP02 = "APP02"

#: VMware cluster / VM / ESXi host identifiers.
CLUSTER_DIGITAL = "CLUSTER-DIGITAL"
VM_APP01 = "vm-app01"
VM_APP02 = "vm-app02"
ESXI_05 = "esxi-05"
ESXI_06 = "esxi-06"

#: Storage identifiers.
STORAGE_POOL = "POOL-FLASH-01"
DATASTORE = "DS-IB-01"

#: Network identifiers.
NETWORK_ZONE = "APP-ZONE"
DEVICE_LEAF101 = "leaf-101"
DEVICE_LEAF102 = "leaf-102"


# ---------------------------------------------------------------------------
# Time windows used across tests
# ---------------------------------------------------------------------------

#: Scenario 1 time window — application slow response on 2026-08-25.
SCENARIO1_START = "2026-08-25 14:00"
SCENARIO1_END = "2026-08-25 14:20"

#: Scenario 2 time window — storage high latency on 2026-08-26.
SCENARIO2_START = "2026-08-26 10:00"
SCENARIO2_END = "2026-08-26 10:20"


@pytest.fixture
def system_id() -> str:
    """Return the canonical system_id used in the data files."""
    return SYSTEM_ID


@pytest.fixture
def application() -> str:
    """Return the canonical application name."""
    return APPLICATION