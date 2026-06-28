export default function ContentHistoryPanel({
  contentHistory,
  setGeneratedContent,
  setQuizData,
  handleDeleteContent,
}) {
  if (!contentHistory.length) return null;

  return (
    <section className="card">
      <h4>Content History</h4>

      <ul>
        {contentHistory.map((item) => (
          <li key={item.id}>
            <strong>{item.title}</strong> ({item.content_type})

            <button
  onClick={() => {
    try {
      if (item.content_type === "quiz") {
        const cleaned = item.content
         .replace(/```json/g, "")
         .replace(/```/g, "")
         .trim();
        const parsedQuiz = JSON.parse(cleaned);
        setQuizData(parsedQuiz);
        setGeneratedContent("");
      } else {
        setGeneratedContent(item.content);
      }
    } catch (error) {
      console.error(error);
    }
  }}
>
  View
</button>

            <button onClick={() => handleDeleteContent(item.id)}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}