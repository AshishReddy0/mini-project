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
        let cleaned = item.content.replace(/```json/gi, "").replace(/```/g, "").trim();
        let parsedQuiz;
        try {
          parsedQuiz = JSON.parse(cleaned);
        } catch (_) {
          let repaired = cleaned;
          const quoteMatches = repaired.match(/(?<!\\)"/g) || [];
          if (quoteMatches.length % 2 !== 0) repaired += '"';

          const openBraces = (repaired.match(/\{/g) || []).length;
          const closeBraces = (repaired.match(/\}/g) || []).length;
          const openBrackets = (repaired.match(/\[/g) || []).length;
          const closeBrackets = (repaired.match(/\]/g) || []).length;

          for (let i = 0; i < openBrackets - closeBrackets; i++) repaired += "]";
          for (let i = 0; i < openBraces - closeBraces; i++) repaired += "}";

          parsedQuiz = JSON.parse(repaired);
        }
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