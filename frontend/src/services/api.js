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

export async function runRosewoodPipelineBatch(payload) {
  const response = await fetch(`${API_BASE_URL}/pipeline/run-batch`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Pipeline batch request failed with ${response.status}`);
  }

  return response.json();
}

export async function startRosewoodPipelineJobs(payload) {
  const response = await fetch(`${API_BASE_URL}/pipeline/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Pipeline job request failed with ${response.status}`);
  }

  return response.json();
}

export async function listRosewoodPipelineJobs() {
  const response = await fetch(`${API_BASE_URL}/pipeline/jobs`);

  if (!response.ok) {
    throw new Error(`Pipeline job list failed with ${response.status}`);
  }

  return response.json();
}

export async function getRosewoodPipelineJobs(batchId) {
  const response = await fetch(`${API_BASE_URL}/pipeline/jobs/${batchId}`);

  if (!response.ok) {
    throw new Error(`Pipeline job status failed with ${response.status}`);
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
