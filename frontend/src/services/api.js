const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function runRosewoodPipeline(payload) {
  const response = await fetch(`${API_BASE_URL}/pipeline/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Pipeline request failed with ${response.status}`);
  }

  return response.json();
}

export async function getDemoScenarios() {
  const response = await fetch(`${API_BASE_URL}/scenarios`);

  if (!response.ok) {
    throw new Error(`Scenario request failed with ${response.status}`);
  }

  return response.json();
}
