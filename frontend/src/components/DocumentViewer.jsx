import { useEffect, useState } from "react";
import { api } from "../api";

export default function DocumentViewer({ document, workspaceId, onClose }) {
  const [textContents, setTextContents] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

  useEffect(() => {
    if (!document) return;

    if (document.file_type === "docx") {
      setLoading(true);
      setError("");
      api
        .getDocumentText(workspaceId, document.id)
        .then((res) => {
          setTextContents(res.content);
          setLoading(false);
        })
        .catch((err) => {
          setError("Failed to load document content: " + err.message);
          setLoading(false);
        });
    }
  }, [document, workspaceId]);

  if (!document) return null;

  return (
    <div className="document-viewer-panel">
      <div className="viewer-header">
        <h4>Preview: {document.filename}</h4>
        <button className="close-btn" onClick={onClose}>
          ✕ Close Preview
        </button>
      </div>

      <div className="viewer-body">
        {document.file_type === "pdf" ? (
          <iframe
            src={`${API_URL}/uploads/${document.filename}`}
            title={document.filename}
            width="100%"
            height="100%"
            className="pdf-iframe"
          />
        ) : (
          <div className="text-viewer-content">
            {loading ? (
              <p className="loading">Loading text content...</p>
            ) : error ? (
              <p className="error">{error}</p>
            ) : (
              <pre className="extracted-text-display">
                {textContents || "No text could be extracted from this document."}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
