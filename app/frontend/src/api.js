const jsonHeaders = { "Content-Type": "application/json" };

export async function fetchJson(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

export function getStatus() {
  return fetchJson("/api/status");
}

export function getDashboardData() {
  return fetchJson("/api/dashboard-data");
}

export function getPortfolio() {
  return fetchJson("/api/portfolio");
}

export function getSignals() {
  return fetchJson("/api/signals");
}

export function getDataHealth() {
  return fetchJson("/api/data-health");
}

export function getResearch() {
  return fetchJson("/api/research");
}

export function getTaskStatus() {
  return fetchJson("/api/tasks/status");
}

export function getTasks() {
  return fetchJson("/api/tasks");
}

export function getAppEnv() {
  return fetchJson("/api/app-env");
}

export function getSafety() {
  return fetchJson("/api/safety");
}

export function runTask(taskName) {
  return fetchJson("/api/tasks/run", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ task_name: taskName })
  });
}

export function getLog(name) {
  return fetchJson(`/api/logs?name=${encodeURIComponent(name)}`);
}
