import { fetchJson } from "./api.js";

let liveInterval = null;
let lastTimestamp = null;

export function initIncidents() {
  const modeSelect = document.getElementById("incidents-mode");
  const actionButton = document.getElementById("incidents-action-button");
  const result = document.getElementById("incidents-result");

  function setResult(content, isError = false) {
    result.textContent = content;
    result.classList.toggle("error", isError);
  }

  function setHtmlResult(html, isError = false) {
    result.innerHTML = html;
    result.classList.toggle("error", isError);
  }

  function clearResult() {
    result.innerHTML = "chat";
    result.classList.remove("error");
  }

  function appendIncident(incident) {
    if (result.textContent === "chat") {
      result.innerHTML = "";
    }

    const item = document.createElement("div");
    item.className = "result-item";
    item.textContent = JSON.stringify(incident);

    result.prepend(item);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
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
              .map(
                (msg) => `<li class="rdd-message">${escapeHtml(msg)}</li>`
              )
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

  function updateForm() {
    const mode = modeSelect.value;

    if (mode !== "live") {
      stopLivePolling();
    }
  }

  async function fetchLiveIncidents() {
    try {
      const url = lastTimestamp
        ? `/api/incidents/live?since=${encodeURIComponent(lastTimestamp)}`
        : `/api/incidents/live`;

      const data = await fetchJson(url);
      const incidents = data.incidents || [];

      incidents.forEach((incident) => {
        appendIncident(incident);
      });

      if (data.last_timestamp) {
        lastTimestamp = data.last_timestamp;
      }
    } catch (error) {
      console.error("Erreur live incidents :", error);
      setResult(`Erreur : ${error.message}`, true);
      stopLivePolling();
    }
  }

  function startLivePolling() {
    stopLivePolling();
    clearResult();
    lastTimestamp = null;

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