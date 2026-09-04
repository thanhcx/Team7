"""Minimal orchestrator skeleton for I/O operations analysis."""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from tools._common import parse_timestamp
from tools.system_inventory import get_system_inventory
from tools.application_metrics import get_application_metrics
from tools.server_metrics import get_server_metrics
from tools.vmware_metrics import get_vmware_metrics
from tools.storage_metrics import get_storage_metrics
from tools.network_metrics import get_network_metrics
from tools.monitoring_alerts import get_monitoring_alerts
from tools.application_logs import search_application_logs
from tools.knowledge_retrieval import search_knowledge_documents, list_knowledge_documents
from agent.config import load_config
from agent.greennode_client import GreenNodeClient, SYSTEM_PROMPT


class IOOperationsOrchestrator:
    """Orchestrator for resolving I/O operations questions."""

    _STOP_WORDS: frozenset[str] = frozenset({
        "the", "a", "an", "and", "or", "but", "nor",
        "in", "on", "at", "to", "for", "of", "with", "by", "from",
        "about", "after", "before", "between", "into", "through",
        "during", "above", "below", "up", "down", "out", "off",
        "over", "under", "again", "further", "within", "without",
        "this", "that", "these", "those", "it", "its",
        "is", "was", "are", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "must", "can",
        "as", "if", "then", "else", "when", "where", "why", "how",
        "all", "both", "each", "few", "more", "most", "other",
        "some", "such", "no", "not", "only", "own", "same", "so",
        "than", "too", "very", "just", "also", "here", "there", "now",
        "unable", "failed", "failure", "error", "warning", "critical",
        "high", "low", "medium", "ok", "normal", "info", "debug",
        "status", "level", "message", "time", "date", "timestamp",
        "id", "name", "type", "value", "count", "total",
        "avg", "average", "min", "max", "sum", "unit",
    })

    _TEXT_FIELDS: frozenset[str] = frozenset({
        "description", "message", "domain", "alert_code", "severity",
        "status", "component", "reason", "detail", "details",
        "operation", "event", "category", "subcategory", "action",
        "application",
    })

    _MAX_KEYWORDS: int = 30

    #: Default window (minutes) applied when only a start time is resolved
    #: (open-ended start, no explicit end).  Prevents unlimited future data
    #: from entering the evidence context.
    DEFAULT_OPEN_ENDED_WINDOW_MINUTES: int = 30

    def resolve_request(self, user_question: str):
        """Resolve the user's request into a structured intent."""
        pass

    def resolve_system(self, user_question: str):
        """Resolve the target system from the user's question.

        Uses the System Inventory tool as the authoritative source of known
        systems/services and matches the user's natural-language question
        against available inventory entries (case-insensitive).

        Returns:
            dict: One of:
                - {"status": "resolved", "system_name": str}
                - {"status": "ambiguous", "candidates": list[str]}
                - {"status": "unresolved", "message": str}
        """
        all_inventory = get_system_inventory("")

        known_systems: list[str] = []
        seen: set[str] = set()
        for item in all_inventory:
            name = item.get("system_name", "")
            if name and name.lower() not in seen:
                seen.add(name.lower())
                known_systems.append(name)

        question_lower = user_question.lower()
        matches = [name for name in known_systems if name.lower() in question_lower]

        if len(matches) == 1:
            return {"status": "resolved", "system_name": matches[0]}
        elif len(matches) > 1:
            return {"status": "ambiguous", "candidates": matches}
        else:
            return {
                "status": "unresolved",
                "message": "No system could be resolved from the question.",
            }

    def resolve_time_window(self, user_question: str):
        """Resolve the relevant time window from the user's question.

        Extracts an explicit analysis time window from natural-language text.
        Supports exact times, time ranges, "from X", "between X and Y",
        date+time combinations, and deterministic relative wording ("now", "today").

        Returns:
            dict: One of:
                - {"status": "resolved", "start": str, "end": str}
                - {"status": "resolved", "start": str}
                - {"status": "resolved", "point": str}
                - {"status": "unresolved", "message": str}
        """
        question = user_question.strip()

        time_pat = r"\d{1,2}:\d{2}(?::\d{2})?\s*(?:[AaPp][Mm])?"
        date_pat = r"\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        token_pat = rf"(?:{date_pat})\s+(?:{time_pat})|(?:{date_pat})|(?:{time_pat})"

        # "between X and Y"
        m = re.search(
            rf"between\s+({token_pat})\s+and\s+({token_pat})", question, re.IGNORECASE
        )
        if m:
            return {
                "status": "resolved",
                "start": m.group(1).strip(),
                "end": m.group(2).strip(),
            }

        # "from TIME to TIME on DATE" (time range with trailing date)
        m = re.search(
            rf"from\s+({time_pat})\s+(?:to|until|–|-)\s+({time_pat})\s+(?:on|at)\s+({date_pat})",
            question,
            re.IGNORECASE,
        )
        if m:
            date = m.group(3).strip()
            return {
                "status": "resolved",
                "start": f"{date} {m.group(1).strip()}",
                "end": f"{date} {m.group(2).strip()}",
            }

        # "from X to/until/–/- Y"
        m = re.search(
            rf"from\s+({token_pat})\s+(?:to|until|–|-)\s+({token_pat})",
            question,
            re.IGNORECASE,
        )
        if m:
            return {
                "status": "resolved",
                "start": m.group(1).strip(),
                "end": m.group(2).strip(),
            }

        # "from/từ [around/approximately/khoảng] TIME on/ngày DATE"
        # (open-ended start with separated date and time)
        m = re.search(
            rf"(?:from|từ)\s+(?:around\s+|approximately\s+|khoảng\s+)?"
            rf"({time_pat})\s+(?:on|ngày)\s+({date_pat})",
            question,
            re.IGNORECASE,
        )
        if m:
            date = m.group(2).strip()
            time_val = m.group(1).strip()
            return {"status": "resolved", "start": f"{date} {time_val}"}

        # "from X" / "từ X" (open-ended start)
        m = re.search(rf"(?:from|từ)\s+({token_pat})", question, re.IGNORECASE)
        if m:
            return {"status": "resolved", "start": m.group(1).strip()}

        # "on DATE at TIME" (date and time separated by "at")
        m = re.search(
            rf"on\s+({date_pat})\s+at\s+({time_pat})", question, re.IGNORECASE
        )
        if m:
            return {
                "status": "resolved",
                "point": f"{m.group(1).strip()} {m.group(2).strip()}",
            }

        # "at X" / "on X"
        m = re.search(rf"(?:at|on)\s+({token_pat})", question, re.IGNORECASE)
        if m:
            return {"status": "resolved", "point": m.group(1).strip()}

        # Bare date/time tokens
        dates = re.findall(date_pat, question)
        times = re.findall(time_pat, question)
        if dates and times:
            return {"status": "resolved", "point": f"{dates[0]} {times[0]}".strip()}
        if dates:
            return {"status": "resolved", "point": dates[0]}
        if times:
            return {"status": "resolved", "point": times[0]}

        # Deterministic relative wording
        if re.search(r"\bnow\b", question, re.IGNORECASE):
            return {"status": "resolved", "point": datetime.now().isoformat()}
        if re.search(r"\btoday\b", question, re.IGNORECASE):
            return {
                "status": "resolved",
                "point": datetime.now().date().isoformat(),
            }

        return {
            "status": "unresolved",
            "message": "No time window could be resolved from the question.",
        }

    def collect_inventory(self, system_name: str):
        """Collect system inventory information for the given system."""
        return get_system_inventory(system_name)

    def collect_operational_evidence(self, inventory, time_window):
        """Collect operational evidence for the inventory within the time window.

        Uses inventory and time_window information to call the deterministic
        Application Metrics, Server Metrics, VMware Metrics, Storage Metrics,
        Network Metrics, Monitoring Alerts, and Application Logs tools.
        Returns a structured dictionary with ``application``, ``server``,
        ``vmware``, ``storage``, ``network``, ``alerts``, and ``logs`` keys.
        If data cannot be retrieved, an unavailable result is returned rather
        than inventing data.

        Returns:
            dict: ``{"application": ..., "server": ..., "vmware": ..., "storage": ..., "network": ..., "alerts": ..., "logs": ...}``
        """
        system_ids: list[str] = []
        applications: list[str] = []
        hostnames: list[str] = []
        vm_names: list[str] = []
        esxi_hosts: list[str] = []
        clusters: list[str] = []
        storage_pools: list[str] = []
        datastores: list[str] = []
        network_zones: list[str] = []
        network_devices: list[str] = []
        endpoints: list[str] = []
        alert_components: list[str] = []
        if inventory:
            for item in inventory:
                if isinstance(item, dict):
                    sid = item.get("system_id")
                    if sid and sid not in system_ids:
                        system_ids.append(sid)
                    app = item.get("application")
                    if app and app not in applications:
                        applications.append(app)
                    host = item.get("hostname") or item.get("server_name")
                    if host and host not in hostnames:
                        hostnames.append(host)
                    vm = item.get("vm_name")
                    if vm and vm not in vm_names:
                        vm_names.append(vm)
                    esxi = item.get("esxi_host")
                    if esxi and esxi not in esxi_hosts:
                        esxi_hosts.append(esxi)
                    clu = item.get("cluster")
                    if clu and clu not in clusters:
                        clusters.append(clu)
                    sp = item.get("storage_pool")
                    if sp and sp not in storage_pools:
                        storage_pools.append(sp)
                    ds = item.get("datastore")
                    if ds and ds not in datastores:
                        datastores.append(ds)
                    nz = item.get("network_zone")
                    if nz and nz not in network_zones:
                        network_zones.append(nz)
                    nd = item.get("device") or item.get("network_device")
                    if nd and nd not in network_devices:
                        network_devices.append(nd)
                    ep = item.get("endpoint")
                    if ep and ep not in endpoints:
                        endpoints.append(ep)
                    comp = item.get("component")
                    if comp and comp not in alert_components:
                        alert_components.append(comp)

        start_time: str | None = None
        end_time: str | None = None
        if isinstance(time_window, dict) and time_window.get("status") == "resolved":
            start_time = time_window.get("start")
            end_time = time_window.get("end")
            if not start_time and not end_time:
                point = time_window.get("point")
                if point:
                    start_time = point
                    end_time = point

        # Apply a bounded default window for open-ended start (start set,
        # end not set).  This prevents unrelated future incidents from
        # entering the grounded context while preserving the user's
        # original semantic intent (end=None means "no explicit end").
        if start_time and not end_time:
            try:
                start_dt = parse_timestamp(start_time)
                effective_end_dt = start_dt + timedelta(
                    minutes=self.DEFAULT_OPEN_ENDED_WINDOW_MINUTES
                )
                end_time = effective_end_dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                pass  # keep end_time as None if start_time is unparseable

        try:
            app_results: list[dict] = []
            if system_ids or applications:
                for sid in system_ids:
                    app_results.extend(
                        get_application_metrics(
                            system_id=sid,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
                for app in applications:
                    app_results.extend(
                        get_application_metrics(
                            application=app,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
            else:
                app_results = get_application_metrics(
                    start_time=start_time,
                    end_time=end_time,
                )
        except Exception:
            app_results = []

        try:
            server_results: list[dict] = []
            if hostnames:
                for host in hostnames:
                    server_results.extend(
                        get_server_metrics(
                            hostname=host,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
            else:
                server_results = get_server_metrics(
                    start_time=start_time,
                    end_time=end_time,
                )
        except Exception:
            server_results = []

        try:
            vmware_results: list[dict] = []
            if vm_names or esxi_hosts or clusters:
                for vm in vm_names:
                    vmware_results.extend(
                        get_vmware_metrics(
                            vm_name=vm,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
                for esxi in esxi_hosts:
                    vmware_results.extend(
                        get_vmware_metrics(
                            esxi_host=esxi,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
                for clu in clusters:
                    vmware_results.extend(
                        get_vmware_metrics(
                            cluster=clu,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
            else:
                vmware_results = get_vmware_metrics(
                    start_time=start_time,
                    end_time=end_time,
                )
        except Exception:
            vmware_results = []

        try:
            storage_results: list[dict] = []
            if storage_pools or datastores:
                for sp in storage_pools:
                    storage_results.extend(
                        get_storage_metrics(
                            storage_pool=sp,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
                for ds in datastores:
                    storage_results.extend(
                        get_storage_metrics(
                            datastore=ds,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
            else:
                storage_results = get_storage_metrics(
                    start_time=start_time,
                    end_time=end_time,
                )
        except Exception:
            storage_results = []

        try:
            network_results: list[dict] = []
            if network_zones or network_devices or endpoints:
                for nz in network_zones:
                    network_results.extend(
                        get_network_metrics(
                            network_zone=nz,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
                for nd in network_devices:
                    network_results.extend(
                        get_network_metrics(
                            device=nd,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
                for ep in endpoints:
                    network_results.extend(
                        get_network_metrics(
                            endpoint=ep,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
            else:
                network_results = get_network_metrics(
                    start_time=start_time,
                    end_time=end_time,
                )
        except Exception:
            network_results = []

        try:
            alert_results: list[dict] = []
            if system_ids or alert_components:
                for sid in system_ids:
                    alert_results.extend(
                        get_monitoring_alerts(
                            system_id=sid,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
                for comp in alert_components:
                    alert_results.extend(
                        get_monitoring_alerts(
                            component=comp,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
            else:
                alert_results = get_monitoring_alerts(
                    start_time=start_time,
                    end_time=end_time,
                )
        except Exception:
            alert_results = []

        try:
            log_results: list[dict] = []
            if applications:
                for app in applications:
                    log_results.extend(
                        search_application_logs(
                            application=app,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
            else:
                log_results = search_application_logs(
                    start_time=start_time,
                    end_time=end_time,
                )
        except Exception:
            log_results = []

        return {
            "application": app_results,
            "server": server_results,
            "vmware": vmware_results,
            "storage": storage_results,
            "network": network_results,
            "alerts": alert_results,
            "logs": log_results,
        }

    def _extract_keywords_from_text(self, text: str) -> set[str]:
        """Extract deterministic keywords from a text string.

        Normalizes text by lowercasing, removing punctuation and
        numeric-only tokens, filtering stop words and very short tokens,
        and generating both single tokens and concise bigram phrases.

        Returns:
            set[str]: Extracted keywords.
        """
        if not text or not isinstance(text, str):
            return set()

        cleaned = re.sub(r"[^a-z0-9\s]", " ", text.lower())
        tokens = cleaned.split()

        meaningful: list[str] = []
        for token in tokens:
            if token.isdigit():
                continue
            if len(token) < 3:
                continue
            if token in self._STOP_WORDS:
                continue
            meaningful.append(token)

        keywords: set[str] = set(meaningful)

        for i in range(len(meaningful) - 1):
            bigram = f"{meaningful[i]} {meaningful[i + 1]}"
            keywords.add(bigram)

        return keywords

    def retrieve_knowledge(self, evidence):
        """Retrieve relevant knowledge based on the collected evidence.

        Uses the collected operational evidence to drive retrieval of approved
        knowledge documents (Standards and Runbooks) through the deterministic
        Knowledge Retrieval tool.  Keywords are extracted dynamically from
        all operational evidence domains using deterministic text
        normalization (lowercasing, punctuation removal, stop-word filtering,
        bigram generation).

        Returns:
            dict: ``{"standards": [...], "runbooks": [...]}`` where each
            entry preserves source metadata (file_name, file_path, title,
            status, version, doc_type, content) returned by the tool.
            If no applicable knowledge is found, empty lists are returned.
        """
        # Preserve keyword discovery/insertion order without alphabetical
        # sorting.  This keeps earlier-discovered (typically higher-level
        # domain) keywords and drops later ones only when the limit is
        # exceeded, rather than discarding terms that simply sort later
        # alphabetically.
        ordered_keywords: list[str] = []
        seen_keywords: set[str] = set()

        def _add_keyword(kw: str) -> None:
            if kw and kw not in seen_keywords:
                seen_keywords.add(kw)
                ordered_keywords.append(kw)

        if isinstance(evidence, dict):
            for domain_key in (
                "application",
                "server",
                "vmware",
                "storage",
                "network",
                "alerts",
                "logs",
            ):
                domain_data = evidence.get(domain_key, [])
                if domain_data:
                    _add_keyword(domain_key)
                    for record in domain_data:
                        if isinstance(record, dict):
                            for field in self._TEXT_FIELDS:
                                text = record.get(field)
                                if text:
                                    for kw in self._extract_keywords_from_text(
                                        str(text)
                                    ):
                                        _add_keyword(kw)

        keywords: list[str] = ordered_keywords[: self._MAX_KEYWORDS]

        try:
            standards: list[dict] = []
            runbooks: list[dict] = []

            if keywords:
                for kw in keywords:
                    standards.extend(
                        search_knowledge_documents(keyword=kw, doc_type="standard")
                    )
                    runbooks.extend(
                        search_knowledge_documents(keyword=kw, doc_type="runbook")
                    )
            else:
                # No keywords extracted — return all available knowledge.
                all_docs = list_knowledge_documents()
                for doc in all_docs:
                    doc_type = doc.get("doc_type", "")
                    if doc_type == "standard":
                        standards.append(doc)
                    elif doc_type == "runbook":
                        runbooks.append(doc)

            # De-duplicate by file_name while preserving order.
            seen_files: set[str] = set()
            unique_standards: list[dict] = []
            for doc in standards:
                fname = doc.get("file_name", "")
                if fname and fname not in seen_files:
                    seen_files.add(fname)
                    unique_standards.append(doc)

            seen_files2: set[str] = set()
            unique_runbooks: list[dict] = []
            for doc in runbooks:
                fname = doc.get("file_name", "")
                if fname and fname not in seen_files2:
                    seen_files2.add(fname)
                    unique_runbooks.append(doc)

        except Exception:
            unique_standards = []
            unique_runbooks = []

        return {
            "standards": unique_standards,
            "runbooks": unique_runbooks,
        }

    def build_grounded_context(
        self,
        user_question,
        inventory,
        evidence,
        knowledge,
        time_window,
    ):
        """Build a grounded context from the question, inventory, evidence, and knowledge.

        Assembles a structured, deterministic, serializable dictionary that
        clearly separates user request, system scope, time window, inventory,
        operational evidence, retrieved knowledge, and evidence gaps.

        No additional data is retrieved; no tools are called; no LLM is used.
        Missing or unavailable domains are explicitly represented.

        Returns:
            dict: Structured grounded context with keys ``user_request``,
            ``system_service_scope``, ``analysis_time_window``,
            ``system_inventory_topology``, ``operational_evidence``,
            ``retrieved_knowledge``, and ``evidence_gaps``.
        """
        # --- A. User Request ---
        user_request = user_question

        # --- B. System / Service Scope ---
        system_names: list[str] = []
        if inventory:
            for item in inventory:
                if isinstance(item, dict):
                    name = item.get("system_name")
                    if name and name not in system_names:
                        system_names.append(name)

        system_service_scope: dict[str, Any] = {
            "system_names": system_names,
            "inventory_count": len(inventory) if inventory else 0,
        }

        # --- C. Analysis Time Window ---
        # Preserve the resolved time window exactly as produced by
        # resolve_time_window().  Do not reinterpret, normalize or invent
        # dates/times here.
        if isinstance(time_window, dict):
            analysis_time_window: dict[str, Any] = time_window
        else:
            analysis_time_window = {"status": "not_provided"}

        # --- D. System Inventory / Topology ---
        system_inventory_topology = inventory if inventory is not None else []

        # --- E. Operational Evidence ---
        evidence_domains = [
            "application",
            "server",
            "vmware",
            "storage",
            "network",
            "alerts",
            "logs",
        ]
        operational_evidence: dict[str, Any] = {}
        if isinstance(evidence, dict):
            for domain in evidence_domains:
                operational_evidence[domain] = evidence.get(domain, [])
        else:
            for domain in evidence_domains:
                operational_evidence[domain] = []

        # --- F. Retrieved Knowledge ---
        knowledge_categories = ["standards", "runbooks"]
        retrieved_knowledge: dict[str, Any] = {}
        if isinstance(knowledge, dict):
            for cat in knowledge_categories:
                retrieved_knowledge[cat] = knowledge.get(cat, [])
        else:
            for cat in knowledge_categories:
                retrieved_knowledge[cat] = []
        # Known Errors category is not supported by the existing tool.
        retrieved_knowledge["known_errors"] = []

        # --- G. Evidence Gaps / Missing Information ---
        evidence_gaps: list[str] = []
        for domain in evidence_domains:
            data = operational_evidence.get(domain)
            if data is None or (isinstance(data, list) and len(data) == 0):
                evidence_gaps.append(
                    f"operational_evidence.{domain}: no data available"
                )

        for cat in knowledge_categories:
            data = retrieved_knowledge.get(cat)
            if data is None or (isinstance(data, list) and len(data) == 0):
                evidence_gaps.append(
                    f"retrieved_knowledge.{cat}: no knowledge available"
                )

        if not system_names:
            evidence_gaps.append("system_service_scope: no system names resolved")

        return {
            "user_request": user_request,
            "system_service_scope": system_service_scope,
            "analysis_time_window": analysis_time_window,
            "system_inventory_topology": system_inventory_topology,
            "operational_evidence": operational_evidence,
            "retrieved_knowledge": retrieved_knowledge,
            "evidence_gaps": evidence_gaps,
        }

    def generate_response(self, grounded_context):
        """Generate a response from the grounded context.

        Sends the Agent Instruction (system prompt) and the serialized grounded
        context to the GreenNode MaaS client.  The model reasons only from the
        grounded evidence and retrieved knowledge provided in the context.

        No additional operational data or knowledge is retrieved from this
        method.  No files are read directly.  No operational tools are called.

        The model is instructed to produce a structured response following the
        11-section output format (Overall Health, Scope, Affected Components,
        Findings, Evidence, RCA Hypothesis, Standard/Baseline Assessment,
        Recommendation/Next Actions, Knowledge References, Confidence,
        Insufficient Evidence).

        If the LLM call fails, a structured error is returned rather than
        inventing an operational response.

        Returns:
            dict: ``{"status": "ok", "response": str}`` on success, or
            ``{"status": "error", "message": str, "response": None}`` on
            failure.
        """
        try:
            config = load_config()
            client = GreenNodeClient(config)

            context_str = json.dumps(
                grounded_context, indent=2, default=str, ensure_ascii=False
            )

            response_text = client.chat(
                user_message=context_str,
                system_prompt=SYSTEM_PROMPT,
            )

            return {
                "status": "ok",
                "response": response_text,
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": f"GreenNode client error: {exc}",
                "response": None,
            }

    def run(self, user_question: str):
        """Run the full orchestration pipeline for the user's question.

        Orchestrates the existing methods in order:
        resolve_system → resolve_time_window → collect_inventory →
        collect_operational_evidence → retrieve_knowledge →
        build_grounded_context → generate_response.

        This method only coordinates; no business logic, RCA, threshold
        evaluation, or recommendation generation is performed here.

        Returns:
            dict: Structured agent response, or a structured
            Insufficient Evidence / unresolved response when the system or
            time window cannot be resolved.
        """
        # 1. Resolve system / service
        try:
            system_result = self.resolve_system(user_question)
        except Exception as exc:
            return {
                "status": "error",
                "message": f"resolve_system failed: {exc}",
                "response": None,
            }

        if not isinstance(system_result, dict):
            return {
                "status": "error",
                "message": "resolve_system returned an unexpected result.",
                "response": None,
            }

        if system_result.get("status") != "resolved":
            return {
                "status": "insufficient_evidence",
                "message": (
                    "System/service could not be resolved or is ambiguous."
                ),
                "system_resolution": system_result,
                "response": None,
            }

        system_name = system_result.get("system_name", "")

        # 2. Resolve time window
        try:
            time_window = self.resolve_time_window(user_question)
        except Exception as exc:
            return {
                "status": "error",
                "message": f"resolve_time_window failed: {exc}",
                "response": None,
            }

        if not isinstance(time_window, dict):
            return {
                "status": "error",
                "message": "resolve_time_window returned an unexpected result.",
                "response": None,
            }

        if time_window.get("status") != "resolved":
            return {
                "status": "insufficient_evidence",
                "message": (
                    "Analysis time window could not be resolved from the request."
                ),
                "system_resolution": system_result,
                "time_window_resolution": time_window,
                "response": None,
            }

        # 3. Collect inventory
        try:
            inventory = self.collect_inventory(system_name)
        except Exception as exc:
            return {
                "status": "insufficient_evidence",
                "message": f"collect_inventory failed: {exc}",
                "system_resolution": system_result,
                "time_window_resolution": time_window,
                "response": None,
            }

        if not inventory:
            return {
                "status": "insufficient_evidence",
                "message": (
                    "No inventory could be retrieved for the resolved system."
                ),
                "system_resolution": system_result,
                "time_window_resolution": time_window,
                "response": None,
            }

        # 4. Collect operational evidence
        try:
            evidence = self.collect_operational_evidence(inventory, time_window)
        except Exception as exc:
            return {
                "status": "error",
                "message": f"collect_operational_evidence failed: {exc}",
                "system_resolution": system_result,
                "time_window_resolution": time_window,
                "response": None,
            }

        # 5. Retrieve knowledge
        try:
            knowledge = self.retrieve_knowledge(evidence)
        except Exception as exc:
            return {
                "status": "error",
                "message": f"retrieve_knowledge failed: {exc}",
                "system_resolution": system_result,
                "time_window_resolution": time_window,
                "response": None,
            }

        # 6. Build grounded context
        try:
            grounded_context = self.build_grounded_context(
                user_question, inventory, evidence, knowledge, time_window
            )
        except Exception as exc:
            return {
                "status": "error",
                "message": f"build_grounded_context failed: {exc}",
                "system_resolution": system_result,
                "time_window_resolution": time_window,
                "response": None,
            }

        # 7. Generate response
        try:
            return self.generate_response(grounded_context)
        except Exception as exc:
            return {
                "status": "error",
                "message": f"generate_response failed: {exc}",
                "response": None,
            }
