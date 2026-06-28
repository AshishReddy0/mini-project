export default function ContentPanel({
  topic,
  setTopic,
  handleGenerateRevision,
  handleGenerateExam,
  handleGenerateQuiz,
  generatedContent,
  documents,
  selectedDocumentId,
  setSelectedDocumentId,
  questionCount,
  setQuestionCount
}) {
  return (
    <>
      <section className="card">
        <h4>Generate Study Content</h4>

        <input 
          type="text"
          placeholder="Enter topic (optional)"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        />

        <div className="document-selector">
          <label>Select Source:</label>

          <select
            value={selectedDocumentId}
            onChange={(e) => setSelectedDocumentId(e.target.value)}
          >
            <option value="">All Documents</option>

            {documents.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.filename}
              </option>
            ))}
          </select>
        </div>
        <div className="question-selector">
  <label>Number of Questions:</label>

  <select
    value={questionCount}
    onChange={(e) => setQuestionCount(Number(e.target.value))}
  >
    <option value={5}>5</option>
    <option value={10}>10</option>
    <option value={15}>15</option>
    <option value={20}>20</option>
  </select>
</div>

        <div className="content-buttons">
          <button type="button" onClick={handleGenerateRevision}>
            Revision
          </button>

         <button type="button" onClick={handleGenerateExam}>
           Exam Prep
         </button>

         <button type="button" onClick={handleGenerateQuiz}>
           Quiz
         </button>
        </div>

        {generatedContent && (
          <section className="card">
          <h4>Generated Content</h4>
          <p>{generatedContent}</p>
        </section>
       )}
     </section>
    </>
  );
}