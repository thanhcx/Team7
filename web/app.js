/* ==========================================================================
   MSB I&O Operations Support Agent — Frontend Logic
   Vanilla JavaScript | No external dependencies
   ========================================================================== */

(function () {
    "use strict";

    /* --- DOM References --- */
    var chatInput = document.getElementById("chatInput");
    var sendBtn = document.getElementById("chatSendBtn");
    var responseArea = document.getElementById("responseArea");
    var suggestionCards = document.querySelectorAll(".suggestion-card");

    /* --- Constants --- */
    var API_ENDPOINT = "/api/v1/chat";

    /* --- Initialization --- */
    function init() {
        // Suggested scenario cards: copy question into textarea, no auto-submit
        suggestionCards.forEach(function (card) {
            card.addEventListener("click", function () {
                var question = card.getAttribute("data-question") || "";
                chatInput.value = question;
                chatInput.focus();
                // Move cursor to end
                var len = chatInput.value.length;
                chatInput.setSelectionRange(len, len);
            });
        });

        // Send button click
        sendBtn.addEventListener("click", handleSubmit);

        // Ctrl+Enter to submit
        chatInput.addEventListener("keydown", function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                e.preventDefault();
                handleSubmit();
            }
        });

        // Auto-resize textarea
        chatInput.addEventListener("input", autoResizeTextarea);
    }

    /* --- Auto-resize textarea --- */
    function autoResizeTextarea() {
        chatInput.style.height = "auto";
        chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + "px";
    }

    /* --- Submit Handler --- */
    function handleSubmit() {
        var message = chatInput.value.trim();

        // Ignore empty messages
        if (!message) {
            return;
        }

        // Display user message
        appendUserMessage(message);

        // Disable Send button and show loading
        setSendButtonLoading(true);
        var loadingEl = showLoadingIndicator();

        // Call API
        callChatApi(message)
            .then(function (result) {
                removeLoadingIndicator(loadingEl);
                handleApiResponse(result);
            })
            .catch(function (err) {
                removeLoadingIndicator(loadingEl);
                handleApiError(err);
            })
            .finally(function () {
                setSendButtonLoading(false);
                clearTextarea();
                scrollToLatest();
            });
    }

    /* --- API Call --- */
    function callChatApi(message) {
        return fetch(API_ENDPOINT, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ message: message }),
        }).then(function (response) {
            if (!response.ok) {
                throw new Error(
                    "HTTP " + response.status + ": " + response.statusText
                );
            }
            return response.json();
        });
    }

    /* --- API Response Handler --- */
    function handleApiResponse(result) {
        if (!result || typeof result !== "object") {
            appendAgentMessage(
                "Unexpected response format from the server.",
                "error"
            );
            return;
        }

        var status = result.status;

        if (status === "ok") {
            var responseText = result.response || "";
            appendAgentMessage(responseText, "ok");
        } else if (status === "insufficient_evidence") {
            var msg =
                result.message ||
                "Insufficient evidence to provide an analysis.";
            appendAgentMessage(msg, "insufficient_evidence");
        } else if (status === "error") {
            var errMsg =
                result.message || "An error occurred during analysis.";
            appendAgentMessage(errMsg, "error");
        } else {
            // Unknown status
            var unknownMsg =
                result.message ||
                "Received an unexpected response status: " + status;
            appendAgentMessage(unknownMsg, "error");
        }
    }

    /* --- API Error Handler --- */
    function handleApiError(err) {
        var errorMsg = "Network or server error occurred.";
        if (err && err.message) {
            errorMsg = err.message;
        }
        appendAgentMessage(errorMsg, "error");
    }

    /* --- DOM: Append User Message --- */
    function appendUserMessage(text) {
        var wrapper = document.createElement("div");
        wrapper.className = "message user-message";

        var content = document.createElement("div");
        content.className = "message-content";

        var body = document.createElement("div");
        body.className = "message-body";

        var p = document.createElement("p");
        p.textContent = text;
        body.appendChild(p);

        content.appendChild(body);
        wrapper.appendChild(content);
        responseArea.appendChild(wrapper);
    }

    /* --- Markdown Strip Helper --- */
    function stripMarkdown(text) {
        if (!text) {
            return "";
        }
        var s = text;
        // Remove bold/italic markers
        s = s.replace(/\*\*\*/g, "");
        s = s.replace(/\*\*/g, "");
        s = s.replace(/__/g, "");
        s = s.replace(/\*/g, "");
        s = s.replace(/_/g, "");
        // Remove heading markers
        s = s.replace(/^#+\s*/g, "");
        // Remove list markers
        s = s.replace(/^[-*+]\s+/g, "");
        // Remove inline code backticks
        s = s.replace(/`/g, "");
        // Collapse whitespace
        s = s.replace(/\s+/g, " ").trim();
        return s;
    }

    /* --- Find section content by heading pattern --- */
    function findSection(lines, headingPattern) {
        var startIndex = -1;
        var endIndex = lines.length;

        // Find the heading line
        for (var i = 0; i < lines.length; i++) {
            if (headingPattern.test(lines[i].trim())) {
                startIndex = i + 1;
                break;
            }
        }

        if (startIndex === -1) {
            return [];
        }

        // Find the next ## heading to determine section end
        for (var j = startIndex; j < lines.length; j++) {
            if (/^##\s/.test(lines[j].trim())) {
                endIndex = j;
                break;
            }
        }

        return lines.slice(startIndex, endIndex);
    }

    /* --- Extract first meaningful line from section lines --- */
    function firstMeaningfulLine(sectionLines) {
        for (var i = 0; i < sectionLines.length; i++) {
            var line = stripMarkdown(sectionLines[i].trim());
            if (line && line.length > 0) {
                return line;
            }
        }
        return null;
    }

    /* --- Extract health status word from text --- */
    function extractHealthStatus(text) {
        if (!text) {
            return null;
        }
        var stripped = stripMarkdown(text);
        var match = stripped.match(
            /\b(critical|warning|healthy|normal|degraded|error|ok)\b/i
        );
        if (match) {
            return (
                match[1].charAt(0).toUpperCase() +
                match[1].slice(1).toLowerCase()
            );
        }
        return stripped || null;
    }

    /* --- Extract field value from "Field: value" pattern within lines --- */
    function extractFieldValue(sectionLines, fieldPattern) {
        for (var i = 0; i < sectionLines.length; i++) {
            var raw = sectionLines[i].trim();
            var match = raw.match(fieldPattern);
            if (match) {
                return stripMarkdown(match[1]);
            }
        }
        return null;
    }

    /* --- Summary Extraction --- */
    function extractSummary(text) {
        var summary = {
            overallHealth: null,
            systemService: null,
            timeWindow: null,
            rcaHypothesis: null,
            confidence: null,
        };

        var lines = text.split("\n");

        // --- Overall Health: section "## 1. Overall Health" ---
        var healthSection = findSection(
            lines,
            /^##\s*1\.\s*overall\s*health/i
        );
        var healthLine = firstMeaningfulLine(healthSection);
        if (healthLine) {
            summary.overallHealth = extractHealthStatus(healthLine);
        }

        // --- Scope section: "## 2. Scope" ---
        var scopeSection = findSection(lines, /^##\s*2\.\s*scope/i);

        // System / Service — support "System / Service:" and "System/Service:"
        summary.systemService = extractFieldValue(
            scopeSection,
            /(?:system\s*\/\s*service|system\/service)\s*:\s*(.+)/i
        );

        // Analysis Time Window
        summary.timeWindow = extractFieldValue(
            scopeSection,
            /analysis\s*time\s*window\s*:\s*(.+)/i
        );

        // --- RCA Hypothesis: section "## 6. RCA Hypothesis" ---
        var rcaSection = findSection(
            lines,
            /^##\s*6\.\s*rca\s*hypothesis/i
        );
        var rcaLine = firstMeaningfulLine(rcaSection);
        if (rcaLine) {
            summary.rcaHypothesis = rcaLine;
        }

        // --- Confidence: section "## 10. Confidence" ---
        var confSection = findSection(
            lines,
            /^##\s*10\.\s*confidence/i
        );
        var confLine = firstMeaningfulLine(confSection);
        if (confLine) {
            summary.confidence = confLine;
        }

        return summary;
    }

    /* --- Health Badge Class --- */
    function getHealthBadgeClass(healthValue) {
        if (!healthValue) {
            return "badge-info";
        }
        var v = healthValue.toLowerCase();
        if (v.indexOf("critical") >= 0 || v.indexOf("error") >= 0) {
            return "badge-critical";
        }
        if (v.indexOf("warning") >= 0 || v.indexOf("degrad") >= 0) {
            return "badge-warning";
        }
        if (
            v.indexOf("healthy") >= 0 ||
            v.indexOf("normal") >= 0 ||
            v.indexOf("ok") >= 0
        ) {
            return "badge-healthy";
        }
        return "badge-info";
    }

    /* --- Summary Row Helper --- */
    function createSummaryRow(label, value, badgeClass) {
        var row = document.createElement("div");
        row.className = "summary-row";

        var labelEl = document.createElement("span");
        labelEl.className = "summary-label";
        labelEl.textContent = label + ":";
        row.appendChild(labelEl);

        var valueEl = document.createElement("span");
        valueEl.className = "summary-value";

        if (!value) {
            valueEl.textContent = "Not available";
            valueEl.classList.add("summary-not-available");
        } else if (badgeClass) {
            var badge = document.createElement("span");
            badge.className = "summary-badge " + badgeClass;
            badge.textContent = value;
            valueEl.appendChild(badge);
        } else {
            valueEl.textContent = value;
        }

        row.appendChild(valueEl);
        return row;
    }

    /* --- Summary Card Renderer --- */
    function renderSummaryCard(summary) {
        var card = document.createElement("div");
        card.className = "analysis-section summary-card";

        var title = document.createElement("div");
        title.className = "analysis-title";
        title.textContent = "Overall Summary";
        card.appendChild(title);

        // Health status row (prominent badge)
        var healthRow = createSummaryRow(
            "Overall Health",
            summary.overallHealth,
            getHealthBadgeClass(summary.overallHealth)
        );
        card.appendChild(healthRow);

        // System / Service row
        var sysRow = createSummaryRow(
            "System / Service",
            summary.systemService,
            null
        );
        card.appendChild(sysRow);

        // Time Window row
        var timeRow = createSummaryRow(
            "Analysis Time Window",
            summary.timeWindow,
            null
        );
        card.appendChild(timeRow);

        // RCA Hypothesis row
        var rcaRow = createSummaryRow(
            "Primary RCA Hypothesis",
            summary.rcaHypothesis,
            null
        );
        card.appendChild(rcaRow);

        // Confidence row
        var confRow = createSummaryRow(
            "Confidence",
            summary.confidence,
            null
        );
        card.appendChild(confRow);

        return card;
    }

    /* --- Status Badge Renderer --- */
    function renderStatusBadge(value) {
        if (!value) {
            return null;
        }
        var stripped = stripMarkdown(value).trim();
        var lower = stripped.toLowerCase();

        var statusMap = {
            critical: "status-critical",
            warning: "status-warning",
            healthy: "status-healthy",
            normal: "status-normal",
            degraded: "status-degraded",
            error: "status-error",
            open: "status-open",
            closed: "status-closed",
        };

        var match = lower.match(
            /^(critical|warning|healthy|normal|degraded|error|open|closed)$/
        );
        if (match && statusMap[match[1]]) {
            var badge = document.createElement("span");
            badge.className = "status-badge " + statusMap[match[1]];
            badge.textContent = stripped;
            return badge;
        }

        return null;
    }

    /* --- Section Class Resolver --- */
    function getSectionClass(headingText) {
        var stripped = stripMarkdown(headingText).toLowerCase();

        if (stripped.indexOf("overall health") >= 0) {
            return "analysis-section overall-health-section";
        }
        if (stripped.indexOf("scope") >= 0) {
            return "analysis-section scope-section";
        }
        if (stripped.indexOf("affected components") >= 0) {
            return "analysis-section affected-components-section";
        }
        if (stripped.indexOf("findings") >= 0) {
            return "analysis-section findings-section";
        }
        if (
            stripped.indexOf("evidence") >= 0 &&
            stripped.indexOf("insufficient") < 0
        ) {
            return "analysis-section evidence-section";
        }
        if (
            stripped.indexOf("rca") >= 0 ||
            stripped.indexOf("hypothesis") >= 0
        ) {
            return "analysis-section rca-section rca-panel";
        }
        if (
            stripped.indexOf("standard") >= 0 ||
            stripped.indexOf("baseline") >= 0
        ) {
            return "analysis-section standard-section";
        }
        if (
            stripped.indexOf("recommendation") >= 0 ||
            stripped.indexOf("next action") >= 0
        ) {
            return "analysis-section recommendation-section recommendation-panel";
        }
        if (
            stripped.indexOf("knowledge") >= 0 &&
            stripped.indexOf("reference") >= 0
        ) {
            return "analysis-section knowledge-section";
        }
        if (stripped.indexOf("confidence") >= 0) {
            return "analysis-section confidence-section";
        }
        if (
            stripped.indexOf("insufficient") >= 0 &&
            stripped.indexOf("evidence") >= 0
        ) {
            return "analysis-section insufficient-evidence-section insufficient-evidence-panel";
        }

        return "analysis-section";
    }

    /* --- Inline Content Renderer (bold + code, no innerHTML) --- */
    function renderInlineContent(text, container) {
        if (!text) {
            return;
        }

        var pattern = /(\*\*[^*]+\*\*|`[^`]+`)/g;
        var lastIndex = 0;
        var match;

        while ((match = pattern.exec(text)) !== null) {
            if (match.index > lastIndex) {
                var plainText = text.substring(lastIndex, match.index);
                container.appendChild(document.createTextNode(plainText));
            }

            var token = match[0];

            if (token.startsWith("**") && token.endsWith("**")) {
                var boldEl = document.createElement("strong");
                boldEl.textContent = token.substring(2, token.length - 2);
                container.appendChild(boldEl);
            } else if (token.startsWith("`") && token.endsWith("`")) {
                var codeEl = document.createElement("code");
                codeEl.textContent = token.substring(1, token.length - 1);
                container.appendChild(codeEl);
            }

            lastIndex = pattern.lastIndex;
        }

        if (lastIndex < text.length) {
            var remaining = text.substring(lastIndex);
            container.appendChild(document.createTextNode(remaining));
        }
    }

    /* --- Markdown Table Renderer --- */
    function renderTable(lines, startIndex) {
        var container = document.createElement("div");
        container.className = "table-container";

        var table = document.createElement("table");
        var thead = document.createElement("thead");
        var tbody = document.createElement("tbody");

        var headerParsed = false;
        var i = startIndex;

        while (i < lines.length) {
            var line = lines[i].trim();

            if (!line.startsWith("|") || !line.endsWith("|")) {
                break;
            }

            if (/^\|[\s-:]+\|/.test(line) && line.indexOf("---") >= 0) {
                i++;
                continue;
            }

            var cells = line.substring(1, line.length - 1).split("|");
            var tr = document.createElement("tr");

            if (!headerParsed) {
                for (var c = 0; c < cells.length; c++) {
                    var th = document.createElement("th");
                    renderInlineContent(cells[c].trim(), th);
                    tr.appendChild(th);
                }
                thead.appendChild(tr);
                headerParsed = true;
            } else {
                for (var c = 0; c < cells.length; c++) {
                    var td = document.createElement("td");
                    var cellValue = cells[c].trim();

                    var badge = renderStatusBadge(cellValue);
                    if (badge) {
                        td.appendChild(badge);
                    } else {
                        renderInlineContent(cellValue, td);
                    }
                    tr.appendChild(td);
                }
                tbody.appendChild(tr);
            }

            i++;
        }

        table.appendChild(thead);
        table.appendChild(tbody);
        container.appendChild(table);

        return { element: container, nextIndex: i };
    }

    /* --- Agent Response Renderer (lightweight Markdown) --- */
    function renderAgentResponse(text) {
        var container = document.createElement("div");
        container.className = "agent-response-rendered";

        if (!text) {
            return container;
        }

        var lines = text.split("\n");
        var i = 0;

        while (i < lines.length) {
            var line = lines[i];
            var trimmed = line.trim();

            if (!trimmed) {
                i++;
                continue;
            }

            // Horizontal rule
            if (/^---+$/.test(trimmed) || /^\*\*\*+$/.test(trimmed)) {
                var hr = document.createElement("hr");
                container.appendChild(hr);
                i++;
                continue;
            }

            // Headings
            var headingMatch = trimmed.match(/^(#{1,4})\s+(.+)/);
            if (headingMatch) {
                var level = headingMatch[1].length;
                var headingText = headingMatch[2];
                var headingEl;

                if (level === 1) {
                    headingEl = document.createElement("h2");
                } else if (level === 2) {
                    headingEl = document.createElement("h3");
                } else {
                    headingEl = document.createElement("h4");
                }

                headingEl.className = getSectionClass(headingText);
                renderInlineContent(headingText, headingEl);
                container.appendChild(headingEl);
                i++;
                continue;
            }

            // Table
            if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
                var tableResult = renderTable(lines, i);
                container.appendChild(tableResult.element);
                i = tableResult.nextIndex;
                continue;
            }

            // Blockquote
            if (trimmed.startsWith(">")) {
                var quoteEl = document.createElement("blockquote");
                var quoteText = trimmed.substring(1).trim();
                renderInlineContent(quoteText, quoteEl);
                container.appendChild(quoteEl);
                i++;
                continue;
            }

            // Bullet list
            if (/^[-*+]\s+/.test(trimmed)) {
                var ul = document.createElement("ul");
                while (i < lines.length) {
                    var bulletLine = lines[i].trim();
                    if (!/^[-*+]\s+/.test(bulletLine)) {
                        break;
                    }
                    var li = document.createElement("li");
                    var bulletText = bulletLine.replace(/^[-*+]\s+/, "");
                    renderInlineContent(bulletText, li);
                    ul.appendChild(li);
                    i++;
                }
                container.appendChild(ul);
                continue;
            }

            // Numbered list (consecutive items share one <ol>; nested
            // unordered bullets stay inside the current <li> without
            // closing the parent <ol>, so numbering continues 1, 2, 3...)
            if (/^\d+\.\s+/.test(trimmed)) {
                var ol = document.createElement("ol");
                var currentOlLi = null;
                var nestedUl = null;
                while (i < lines.length) {
                    var numLine = lines[i].trim();

                    // Blank line: keep the ordered list open so that
                    // numbered items separated by blank lines still group.
                    if (!numLine) {
                        i++;
                        continue;
                    }

                    // Next numbered item: new <li> in the same <ol>.
                    if (/^\d+\.\s+/.test(numLine)) {
                        currentOlLi = document.createElement("li");
                        var numText = numLine.replace(/^\d+\.\s+/, "");
                        renderInlineContent(numText, currentOlLi);
                        ol.appendChild(currentOlLi);
                        nestedUl = null;
                        i++;
                        continue;
                    }

                    // Nested unordered bullet inside the current ordered
                    // item: attach to a <ul> on the current <li> without
                    // closing the parent <ol>.
                    if (/^[-*+]\s+/.test(numLine) && currentOlLi) {
                        if (!nestedUl) {
                            nestedUl = document.createElement("ul");
                            currentOlLi.appendChild(nestedUl);
                        }
                        var nestedLi = document.createElement("li");
                        var nestedBulletText = numLine.replace(/^[-*+]\s+/, "");
                        renderInlineContent(nestedBulletText, nestedLi);
                        nestedUl.appendChild(nestedLi);
                        i++;
                        continue;
                    }

                    // Any other content ends the ordered list.
                    break;
                }
                container.appendChild(ol);
                continue;
            }

            // Normal paragraph
            var para = document.createElement("p");

            var badge = renderStatusBadge(trimmed);
            if (badge) {
                para.appendChild(badge);
            } else {
                renderInlineContent(trimmed, para);
            }
            container.appendChild(para);
            i++;
        }

        return container;
    }

    /* --- DOM: Append Agent Message --- */
    function appendAgentMessage(text, type) {
        var wrapper = document.createElement("div");
        wrapper.className = "message agent-message";

        var avatar = document.createElement("div");
        avatar.className = "message-avatar message-avatar-agent";
        var avatarIcon = document.createElement("span");
        avatarIcon.className = "avatar-icon";
        avatarIcon.textContent = "AI";
        avatar.appendChild(avatarIcon);

        var content = document.createElement("div");
        content.className = "message-content";

        var sender = document.createElement("div");
        sender.className = "message-sender";
        sender.textContent = "I&O Operations Support Agent";
        content.appendChild(sender);

        var body = document.createElement("div");
        body.className = "message-body";

        if (type === "insufficient_evidence") {
            var alertDiv = document.createElement("div");
            alertDiv.className = "insufficient-evidence";
            alertDiv.textContent = text;
            body.appendChild(alertDiv);
        } else if (type === "error") {
            var errorDiv = document.createElement("div");
            errorDiv.className = "analysis-section";
            var errorTitle = document.createElement("div");
            errorTitle.className = "analysis-title";
            errorTitle.textContent = "Error";
            errorDiv.appendChild(errorTitle);
            var errorBody = document.createElement("p");
            errorBody.textContent = text;
            errorDiv.appendChild(errorBody);
            body.appendChild(errorDiv);
        } else {
            // Normal response — render summary card + full response

            // Extract and render summary card
            var summary = extractSummary(text);
            var summaryCard = renderSummaryCard(summary);
            body.appendChild(summaryCard);

            // Divider
            var divider = document.createElement("hr");
            divider.className = "summary-divider";
            body.appendChild(divider);

            // Full response — structured Markdown renderer
            var rendered = renderAgentResponse(text);
            body.appendChild(rendered);
        }

        content.appendChild(body);
        wrapper.appendChild(avatar);
        wrapper.appendChild(content);
        responseArea.appendChild(wrapper);
    }

    /* --- DOM: Loading Indicator --- */
    function showLoadingIndicator() {
        var wrapper = document.createElement("div");
        wrapper.className = "message agent-message";

        var avatar = document.createElement("div");
        avatar.className = "message-avatar message-avatar-agent";
        var avatarIcon = document.createElement("span");
        avatarIcon.className = "avatar-icon";
        avatarIcon.textContent = "AI";
        avatar.appendChild(avatarIcon);

        var content = document.createElement("div");
        content.className = "message-content";

        var loadingDiv = document.createElement("div");
        loadingDiv.className = "loading";
        loadingDiv.textContent = "Analyzing";

        var dot1 = document.createElement("span");
        dot1.className = "loading-dot";
        var dot2 = document.createElement("span");
        dot2.className = "loading-dot";
        var dot3 = document.createElement("span");
        dot3.className = "loading-dot";

        loadingDiv.appendChild(dot1);
        loadingDiv.appendChild(dot2);
        loadingDiv.appendChild(dot3);

        content.appendChild(loadingDiv);
        wrapper.appendChild(avatar);
        wrapper.appendChild(content);
        responseArea.appendChild(wrapper);

        return wrapper;
    }

    function removeLoadingIndicator(el) {
        if (el && el.parentNode) {
            el.parentNode.removeChild(el);
        }
    }

    /* --- UI State: Send Button --- */
    function setSendButtonLoading(isLoading) {
        if (isLoading) {
            sendBtn.disabled = true;
            sendBtn.classList.add("is-loading");
        } else {
            sendBtn.disabled = false;
            sendBtn.classList.remove("is-loading");
        }
    }

    /* --- UI: Clear Textarea --- */
    function clearTextarea() {
        chatInput.value = "";
        chatInput.style.height = "auto";
    }

    /* --- UI: Scroll to Latest --- */
    function scrollToLatest() {
        if (responseArea.lastChild) {
            responseArea.lastChild.scrollIntoView({
                behavior: "smooth",
                block: "end",
            });
        }
    }

    /* --- Boot --- */
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();