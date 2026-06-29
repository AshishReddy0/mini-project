// API helper functions for calling the FastAPI backend

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Read the saved JWT token from browser storage.
 */
export function getToken() {
  return localStorage.getItem("token");
}

/**
 * Save or remove the JWT after login/logout.
 */
export function setToken(token) {
  if (token) {
    localStorage.setItem("token", token);
  } else {
    localStorage.removeItem("token");
  }
}

/**
 * Generic fetch wrapper that attaches the auth header when a token exists.
 */
async function apiFetch(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  // Let the browser set multipart boundaries for file uploads
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    throw new Error(data?.detail || `Request failed (${response.status})`);
  }

  return data;
}

export const api = {
  health: () => apiFetch("/health"),
  healthDb: () => apiFetch("/health/db"),

  register: (body) =>
    apiFetch("/auth/register", { method: "POST", body: JSON.stringify(body) }),

  login: (body) =>
    apiFetch("/auth/login", { method: "POST", body: JSON.stringify(body) }),

  me: () => apiFetch("/auth/me"),

  listWorkspaces: () => apiFetch("/workspaces"),
  listContent: (workspaceId) =>
  apiFetch(`/workspaces/${workspaceId}/content`),

  createWorkspace: (body) =>
    apiFetch("/workspaces", { method: "POST", body: JSON.stringify(body) }),

  uploadDocument: (workspaceId, file) => {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch(`/workspaces/${workspaceId}/documents`, {
    method: "POST",
    body: formData,
  });
},

generateRevision: (workspaceId, body) =>
  apiFetch(`/workspaces/${workspaceId}/content/revision`, {
    method: "POST",
    body: JSON.stringify(body),
  }),

generateExam: (workspaceId, body) =>
  apiFetch(`/workspaces/${workspaceId}/content/exam`, {
    method: "POST",
    body: JSON.stringify(body),
  }),

generateQuiz: (workspaceId, body) =>
  apiFetch(`/workspaces/${workspaceId}/content/quiz`, {
    method: "POST",
    body: JSON.stringify(body),
  }),

deleteContent: (workspaceId, contentId) =>
  apiFetch(`/workspaces/${workspaceId}/content/${contentId}`, {
    method: "DELETE",
  }),

sendChatMessage: (workspaceId, body) =>
  apiFetch(`/workspaces/${workspaceId}/chat`, {
    method: "POST",
    body: JSON.stringify(body),
  }),

getChatHistory: (workspaceId) =>
  apiFetch(`/workspaces/${workspaceId}/chat`),

listDocuments: (workspaceId) =>
  apiFetch(`/workspaces/${workspaceId}/documents`),

deleteDocument: (workspaceId, documentId) =>
  apiFetch(`/workspaces/${workspaceId}/documents/${documentId}`, {
    method: "DELETE",
  }),

listContent: (workspaceId) =>
  apiFetch(`/workspaces/${workspaceId}/content`),
};
