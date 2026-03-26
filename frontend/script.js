async function callApi() {
  try {
    const response = await fetch("/api/");
    const text = await response.text();

    document.getElementById("result").innerHTML = text;
  } catch (err) {
    document.getElementById("result").textContent =
      "Erreur: " + err;
  }
}