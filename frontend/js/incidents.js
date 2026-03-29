import { fetchJson } from "./api.js";

let liveInterval = null;

export function initIncidents() {
  const modeSelect = document.getElementById("incidents-mode");
  const actionButton = document.getElementById("incidents-action-button");
  const result = document.getElementById("incidents-result");

  function setResult(content, isError = false) {
    result.textContent = content;
    result.classList.remove("result-html");
    result.classList.add("result-text");
    result.classList.toggle("error", isError);
  }

  function setHtmlResult(html, isError = false) {
    result.innerHTML = html;
    result.classList.remove("result-text");
    result.classList.add("result-html");
    result.classList.toggle("error", isError);
  }

  function clearResult() {
    result.innerHTML = "";
    result.classList.remove("error");
    result.classList.remove("result-text");
    result.classList.remove("result-html");
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatDateTime(value) {
    if (!value) return "—";

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return escapeHtml(value);
    }

    return date.toLocaleString("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      day: "2-digit",
      month: "2-digit"
    });
  }

  function formatTime(value) {
    if (!value) return "—";

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return escapeHtml(value);
    }

    return date.toLocaleTimeString("fr-FR", {
      hour: "2-digit",
      minute: "2-digit"
    });
  }

  function normalizeSeverityLabel(value) {
    const raw = String(value ?? "").trim();
    if (!raw) return "Inconnue";

    return raw.charAt(0).toUpperCase() + raw.slice(1);
  }

  function getSeverityClass(value) {
    const normalized = String(value ?? "").trim().toLowerCase();

    if (normalized.includes("bloquante")) return "severity--critical";
    if (normalized.includes("perturb")) return "severity--warning";
    if (normalized.includes("information")) return "severity--info";
    return "severity--default";
  }

  function renderDataframeResult(data) {
    if (!Array.isArray(data) || data.length === 0) {
      setHtmlResult(`
        <div class="df-result">
          <h4 class="df-result__title">Stations les plus impactées</h4>
          <p class="df-result__subtitle">
            Aucune donnée disponible pour le moment.
          </p>
        </div>
      `);
      return;
    }

    const rows = data
      .map((item, index) => {
        const stopName = item.stop_name ?? "Station inconnue";
        const incidents = item.stop_incidents ?? 0;

        return `
          <tr>
            <td class="df-rank">#${index + 1}</td>
            <td>${escapeHtml(stopName)}</td>
            <td>
              <span class="incident-badge">${escapeHtml(incidents)}</span>
            </td>
          </tr>
        `;
      })
      .join("");

    setHtmlResult(`
      <div class="df-result">
        <h4 class="df-result__title">Stations les plus impactées</h4>
        <p class="df-result__subtitle">
          Classement des stations selon le nombre total de perturbations détectées.
        </p>

        <div class="df-table-wrapper">
          <table class="df-table">
            <thead>
              <tr>
                <th>Rang</th>
                <th>Station</th>
                <th>Incidents</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        </div>
      </div>
    `);
  }

  function renderRddResult(data) {
    if (data?.error) {
      setHtmlResult(`
        <div class="rdd-result">
          <h4 class="rdd-result__title">Perturbations par ligne</h4>
          <p>${escapeHtml(data.error)}</p>
        </div>
      `, true);
      return;
    }

    if (!Array.isArray(data) || data.length === 0) {
      setHtmlResult(`
        <div class="rdd-result">
          <h4 class="rdd-result__title">Perturbations par ligne</h4>
          <p>Aucune donnée disponible pour le moment.</p>
        </div>
      `);
      return;
    }

    const cards = data
      .map((item) => {
        const lineId = item.line_id ?? "Ligne inconnue";
        const messages = Array.isArray(item.messages) ? item.messages : [];

        const messagesHtml = messages.length
          ? messages
              .map((msg) => `<li class="rdd-message">${escapeHtml(msg)}</li>`)
              .join("")
          : `<li class="rdd-message">Aucun message</li>`;

        return `
          <div class="rdd-card">
            <h5 class="rdd-line">${escapeHtml(lineId)}</h5>
            <ul class="rdd-messages">
              ${messagesHtml}
            </ul>
          </div>
        `;
      })
      .join("");

    setHtmlResult(`
      <div class="rdd-result">
        <h4 class="rdd-result__title">Perturbations par ligne</h4>
        <p class="rdd-result__subtitle">
          Liste des messages de perturbation regroupés par ligne.
        </p>
        <div class="rdd-list">
          ${cards}
        </div>
      </div>
    `);
  }

  function renderLiveResult(data) {
      
    const incidents = Array.isArray(data?.severity) ? data.severity : [];
    const status = data?.status ?? "unknown";
    const lastTimestamp = data?.last_timestamp ?? null;

    if (status === "starting") {
      setHtmlResult(`
        <div class="live-result">
          <h4 class="live-result__title">Suivi live par sévérité</h4>
          <p class="live-result__subtitle">Initialisation du streaming...</p>
        </div>
      `);
      return;
    }

    if (status === "stopped") {
      setHtmlResult(`
        <div class="live-result">
          <h4 class="live-result__title">Suivi live par sévérité</h4>
          <p class="live-result__subtitle">Streaming arrêté.</p>
        </div>
      `);
      return;
    }

    if (!incidents.length) {
      setHtmlResult(`
        <div class="live-result">
          <div class="live-result__header">
            <div>
              <h4 class="live-result__title">Suivi live par sévérité</h4>
              <p class="live-result__subtitle">
                Dernière mise à jour : ${escapeHtml(formatDateTime(lastTimestamp))}
              </p>
            </div>
            <span class="live-pill">En direct</span>
          </div>
          <p class="live-empty">Aucune donnée live disponible pour le moment.</p>
        </div>
      `);
      return;
    }

    const groupedByWindow = new Map();

    incidents.forEach((incident) => {
      const windowStart = incident.window_start ?? "";
      const windowEnd = incident.window_end ?? "";
      const key = `${windowStart}__${windowEnd}`;

      if (!groupedByWindow.has(key)) {
        groupedByWindow.set(key, {
          window_start: windowStart,
          window_end: windowEnd,
          items: []
        });
      }

      groupedByWindow.get(key).items.push(incident);
    });

    const windows = Array.from(groupedByWindow.values())
      .sort((a, b) => new Date(b.window_end) - new Date(a.window_end))
      .slice(0, 4);

    const sectionsHtml = windows
      .map((group) => {
        const rowsHtml = group.items
          .sort((a, b) => (b.nb_events ?? 0) - (a.nb_events ?? 0))
          .map((item) => {
            const severityLabel = normalizeSeverityLabel(item.severity_name);
            const nbEvents = item.nb_events ?? 0;
            const severityClass = getSeverityClass(item.severity_name);

            return `
              <tr>
                <td>
                  <span class="live-badge ${severityClass}">
                    ${escapeHtml(severityLabel)}
                  </span>
                </td>
                <td class="live-table__count">${escapeHtml(nbEvents)}</td>
              </tr>
            `;
          })
          .join("");

        return `
          <div class="live-section">
            <div class="live-section__title">
              Fenêtre ${escapeHtml(formatTime(group.window_start))} → ${escapeHtml(formatTime(group.window_end))}
            </div>
            <div class="live-table-wrapper">
              <table class="live-table">
                <thead>
                  <tr>
                    <th>Sévérité</th>
                    <th>Événements</th>
                  </tr>
                </thead>
                <tbody>
                  ${rowsHtml}
                </tbody>
              </table>
            </div>
          </div>
        `;
      })
      .join("");

    setHtmlResult(`
      <div class="live-result">
        <div class="live-result__header">
          <div>
            <h4 class="live-result__title">Suivi live par sévérité</h4>
            <p class="live-result__subtitle">
              Dernière mise à jour : ${escapeHtml(formatDateTime(lastTimestamp))}
            </p>
          </div>
          <span class="live-pill">En direct</span>
        </div>

        ${sectionsHtml}
      </div>
    `);
  }

  function updateForm() {
    const mode = modeSelect.value;

    if (mode !== "live") {
      stopLivePolling();
    }
  }

  async function fetchLiveIncidents() {
    try {
      const data = await fetchJson("/api/incidents/live");
      renderLiveResult(data);
    } catch (error) {
      console.error("Erreur live incidents :", error);
      setResult(`Erreur : ${error.message}`, true);
      stopLivePolling();
    }
  }

  function startLivePolling() {
    stopLivePolling();
    clearResult();

    fetchLiveIncidents();
    liveInterval = setInterval(fetchLiveIncidents, 3000);
  }

  function stopLivePolling() {
    if (liveInterval) {
      clearInterval(liveInterval);
      liveInterval = null;
    }
  }

  async function runHistoryQuery() {
    const mode = modeSelect.value;

    actionButton.disabled = true;
    setResult("Chargement...");

    try {
      const data = await fetchJson("/api/incidents/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          type: mode
        })
      });

      if (mode === "dataframe") {
        renderDataframeResult(data);
      } else if (mode === "rdd") {
        renderRddResult(data);
      } else {
        setResult(JSON.stringify(data, null, 2));
      }
    } catch (error) {
      console.error("Erreur requête incidents :", error);
      setResult(`Erreur : ${error.message}`, true);
    } finally {
      actionButton.disabled = false;
    }
  }

  function handleAction() {
    const mode = modeSelect.value;

    if (mode === "live") {
      startLivePolling();
      return;
    }

    runHistoryQuery();
  }

  modeSelect.addEventListener("change", updateForm);
  actionButton.addEventListener("click", handleAction);

  updateForm();
}