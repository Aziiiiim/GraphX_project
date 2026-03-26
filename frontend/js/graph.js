export function initGraph() {
  let graphMap = null;
  let graphLayerGroup = null;

  function initGraphMap() {
    graphMap = L.map("graph-map").setView([48.8566, 2.3522], 13);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(graphMap);

    graphLayerGroup = L.layerGroup().addTo(graphMap);
  }

  function renderGraph(data) {
    if (!graphMap || !graphLayerGroup) return;

    graphLayerGroup.clearLayers();

    const stations = data.stations || [];
    const edges = data.edges || [];

    const stationById = new Map();
    const bounds = [];

    stations.forEach((station) => {
      stationById.set(station.id, station);

      const marker = L.circleMarker([station.lat, station.lon], {
        radius: 6,
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      });

      marker.bindPopup(`
        <strong>${station.name || "Station " + station.id}</strong><br />
        id: ${station.id}<br />
        lat: ${station.lat}<br />
        lon: ${station.lon}
      `);

      marker.addTo(graphLayerGroup);
      bounds.push([station.lat, station.lon]);
    });

    edges.forEach((edge) => {
      const src = stationById.get(edge.src);
      const dst = stationById.get(edge.dst);

      if (!src || !dst) return;

      L.polyline(
        [
          [src.lat, src.lon],
          [dst.lat, dst.lon]
        ],
        {
          weight: 3,
          opacity: 0.7
        }
      ).addTo(graphLayerGroup);
    });

    if (bounds.length > 0) {
      graphMap.fitBounds(bounds, { padding: [30, 30] });
    }
  }

  async function loadGraph() {
    try {
      const response = await fetch("/api/graph");

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      renderGraph(data);
    } catch (error) {
      console.error("Erreur chargement graphe :", error);

      const fallbackData = {
        stations: [
          { id: 1, name: "Châtelet", lat: 48.8586, lon: 2.3470 },
          { id: 2, name: "Hôtel de Ville", lat: 48.8577, lon: 2.3514 },
          { id: 3, name: "République", lat: 48.8674, lon: 2.3630 },
          { id: 4, name: "Bastille", lat: 48.8532, lon: 2.3692 },
          { id: 5, name: "Gare de Lyon", lat: 48.8443, lon: 2.3730 }
        ],
        edges: [
          { src: 1, dst: 2 },
          { src: 2, dst: 3 },
          { src: 2, dst: 4 },
          { src: 4, dst: 5 }
        ]
      };

      renderGraph(fallbackData);
    }
  }

  const graphQueryType = document.getElementById("graph-query-type");
  const routeParams = document.getElementById("route-params");
  const routeSource = document.getElementById("route-source");
  const routeTarget = document.getElementById("route-target");
  const graphQueryButton = document.getElementById("graph-query-button");
  const graphResult = document.getElementById("graph-result");

  function updateGraphQueryForm() {
    const queryType = graphQueryType.value;
    const isRoute = queryType === "route";

    routeParams.classList.toggle("hidden", !isRoute);
    routeSource.required = isRoute;
    routeTarget.required = isRoute;

    if (!isRoute) {
      routeSource.value = "";
      routeTarget.value = "";
    }
  }

  function setGraphResult(content, isError = false) {
    graphResult.textContent = content;
    graphResult.classList.toggle("error", isError);
  }

  function buildGraphQueryPayload() {
    const queryType = graphQueryType.value;

    if (queryType === "pagerank") {
      return { type: "pagerank" };
    }

    if (queryType === "degree") {
      return { type: "degree" };
    }

    if (queryType === "route") {
      const source = routeSource.value.trim();
      const target = routeTarget.value.trim();

      if (!source || !target) {
        throw new Error("Les stations de départ et d'arrivée sont obligatoires.");
      }

      return {
        type: "route",
        source: Number(source),
        target: Number(target)
      };
    }

    throw new Error("Type de requête inconnu.");
  }

  async function sendGraphQuery() {
    graphQueryButton.disabled = true;
    setGraphResult("Chargement...");

    try {
      const payload = buildGraphQueryPayload();

      const response = await fetch("/api/graph/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setGraphResult(JSON.stringify(data, null, 2));
    } catch (error) {
      console.error("Erreur requête graphe :", error);
      setGraphResult(`Erreur : ${error.message}`, true);
    } finally {
      graphQueryButton.disabled = false;
    }
  }

  graphQueryType.addEventListener("change", updateGraphQueryForm);
  graphQueryButton.addEventListener("click", sendGraphQuery);

  initGraphMap();
  updateGraphQueryForm();
  loadGraph();
}