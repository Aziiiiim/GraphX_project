import { fetchJson } from "./api.js";

let liveInterval = null;
let lastTimestamp = null;

export function initIncidents() {
  const modeSelect = document.getElementById("incidents-mode");
  const historyFields = document.getElementById("incidents-history-fields");
  const lookbackSelect = document.getElementById("incidents-lookback");
  const actionButton = document.getElementById("incidents-action-button");
  const result = document.getElementById("incidents-result");

  function setResult(content, isError = false) {
    result.textContent = content;
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

  function updateForm() {
    const mode = modeSelect.value;

    const showHistory =
        mode === "dataframe" || mode === "rdd";

    if (showHistory) {
        historyFields.classList.remove("hidden");
    } else {
        historyFields.classList.add("hidden");
    }
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
    const lookback = lookbackSelect.value;

    actionButton.disabled = true;
    setResult("Chargement...");

    try {
      const data = await fetchJson("/api/incidents/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          type: mode,
          lookback
        })
      });

      setResult(JSON.stringify(data, null, 2));
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