export default function DocumentPanel({
  selectedWorkspace,
  handleUploadDocument,
  setSelectedFile,
  documents,
  handleDeleteDocument,
  handlePreviewDocument,
}) {
  return (
    <section className="card">
      <h3>Selected Workspace: {selectedWorkspace.name}</h3>

      <form onSubmit={handleUploadDocument}>
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={(e) => setSelectedFile(e.target.files[0])}
        />
        <button type="submit">Upload Document</button>
      </form>

      <h4>Uploaded Documents</h4>

      <ul>
        {documents.map((doc) => (
          <li key={doc.id}>
            {doc.filename} ({doc.file_type})

            <button
              type="button"
              className="preview-btn"
              onClick={() => handlePreviewDocument(doc)}
            >
              Preview
            </button>

            <button
              type="button"
              onClick={() => handleDeleteDocument(doc.id)}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}