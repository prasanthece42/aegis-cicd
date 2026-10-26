"use strict";

const element = (id) => document.getElementById(id);
const button = element("refresh");
element("origin").textContent = window.location.host;

async function readEndpoint(path, validate) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  const start = performance.now();
  let status = null;
  let body = null;
  try {
    const response = await fetch(path, { cache: "no-store", signal: controller.signal });
    status = response.status;
    body = await response.json();
    if (!response.ok) throw new Error(`HTTP ${status}`);
    if (!validate(body)) throw new Error("Unexpected API response");
    return { ok: true, status, body, duration: Math.round(performance.now() - start) };
  } catch (error) {
    const message = error.name === "AbortError" ? "Request timed out" : error.message;
    return { ok: false, status, body, error: message };
  } finally {
    clearTimeout(timeout);
  }
}

function showResponse(name, result) {
  element(`${name}-http`).textContent = result.status === null
    ? "No response"
    : `HTTP ${result.status}${result.ok ? ` · ${result.duration} ms` : ""}`;
  element(`${name}-response`).textContent = result.body === null
    ? result.error
    : JSON.stringify(result.body, null, 2);
}

async function runChecks() {
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  element("overall").textContent = "Checking";
  element("overall").dataset.tone = "pending";
  element("health-card").dataset.tone = "pending";
  element("health-value").textContent = "Checking…";
  element("health-detail").textContent = "Contacting the running application.";
  element("version-value").textContent = "—";
  element("version-detail").textContent = "Reading the version from the API.";
  element("check-message").textContent = "Checking the API…";
  for (const name of ["health", "version"]) {
    element(`${name}-http`).textContent = "Checking…";
    element(`${name}-response`).textContent = "Waiting for a response…";
  }
  const [health, version] = await Promise.all([
    readEndpoint("/health", (body) => body?.status === "ok"),
    readEndpoint("/version", (body) => typeof body?.version === "string" && body.version.length > 0),
  ]);

  showResponse("health", health);
  showResponse("version", version);
  element("health-card").dataset.tone = health.ok ? "success" : "error";
  element("health-value").textContent = health.ok ? "Healthy" : "Check failed";
  element("health-detail").textContent = health.ok
    ? "The application is responding successfully."
    : `Could not confirm application health. ${health.error}.`;
  element("version-value").textContent = version.ok ? version.body.version : "Unavailable";
  element("version-detail").textContent = version.ok
    ? "Read directly from this application's /version endpoint."
    : `Could not read the application version. ${version.error}.`;
  const allPassed = health.ok && version.ok;
  element("overall").textContent = allPassed ? "All checks passed" : "Needs attention";
  element("overall").dataset.tone = allPassed ? "success" : "error";
  element("check-message").textContent = allPassed
    ? "Both endpoints responded successfully. Your application is reachable."
    : "One or more checks failed. Review the responses above, then try again.";
  element("last-checked").textContent = `Last checked at ${new Date().toLocaleTimeString()}`;
  button.disabled = false;
  button.removeAttribute("aria-busy");
}

button.addEventListener("click", runChecks);
runChecks();
