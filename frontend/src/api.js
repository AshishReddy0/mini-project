// API helper functions for calling the FastAPI backend

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function getToken() {
  return localStorage.getItem("token");
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("token", token);
  } else {
    localStorage.removeItem("token");
  }
}

async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  // Let the browser set multipart boundaries for file uploads
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    let errorMessage = `Request failed (${response.status})`;
    if (data?.detail) {
      if (Array.isArray(data.detail)) {
        errorMessage = data.detail.map(err => `${err.loc[err.loc.length - 1]}: ${err.msg}`).join(", ");
      } else {
        errorMessage = data.detail;
      }
    }
    throw new Error(errorMessage);
  }

  return data;
}

export const api = {
  // Auth
  register: (body) =>
    apiFetch("/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body) =>
    apiFetch("/auth/login", { method: "POST", body: JSON.stringify(body) }),
  me: () => apiFetch("/auth/me"),

  // Workspaces
  listWorkspaces: () => apiFetch("/workspaces"),
  createWorkspace: (body) =>
    apiFetch("/workspaces", { method: "POST", body: JSON.stringify(body) }),
  deleteWorkspace: (workspaceId) =>
    apiFetch(`/workspaces/${workspaceId}`, { method: "DELETE" }),


  // Documents
  listDocuments: (workspaceId) =>
    apiFetch(`/workspaces/${workspaceId}/documents`),
  uploadDocument: (workspaceId, file) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiFetch(`/workspaces/${workspaceId}/documents`, {
      method: "POST",
      body: formData,
    });
  },
  deleteDocument: (workspaceId, documentId) =>
    apiFetch(`/workspaces/${workspaceId}/documents/${documentId}`, {
      method: "DELETE",
    }),
  getDocumentText: (workspaceId, documentId) =>
    apiFetch(`/workspaces/${workspaceId}/documents/${documentId}/text`),

  // Chat
  sendChatMessage: (workspaceId, body) =>
    apiFetch(`/workspaces/${workspaceId}/chat`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getChatHistory: (workspaceId) =>
    apiFetch(`/workspaces/${workspaceId}/chat`),

  // Concept Graph (Roadmap)
  generateGraph: (workspaceId, body = {}) =>
    apiFetch(`/workspaces/${workspaceId}/graph/generate`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getGraph: (workspaceId) =>
    apiFetch(`/workspaces/${workspaceId}/graph`),
  clearGraph: (workspaceId) =>
    apiFetch(`/workspaces/${workspaceId}/graph`, {
      method: "DELETE",
    }),
  downloadSyllabusPDF: async (workspaceId, filename = "Concept_Syllabus.pdf") => {
    const token = getToken();
    const headers = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    const response = await fetch(`${API_URL}/workspaces/${workspaceId}/graph/export-pdf`, { headers });
    if (!response.ok) throw new Error("Failed to download PDF report");
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  // Node actions
  getNodeAnswer: (workspaceId, nodeId) =>
    apiFetch(`/workspaces/${workspaceId}/node/${nodeId}/answer`),
  markNodeMastered: (workspaceId, nodeId) =>
    apiFetch(`/workspaces/${workspaceId}/node/${nodeId}/master`, {
      method: "POST",
    }),
  attemptNode: (workspaceId, nodeId, body) =>
    apiFetch(`/workspaces/${workspaceId}/node/${nodeId}/attempt`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
