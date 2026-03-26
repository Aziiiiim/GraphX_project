import { initTabs } from "./tabs.js";
import { initGraph } from "./graph.js";
import { initIncidents } from "./incidents.js";

window.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initGraph();
  initIncidents();
});