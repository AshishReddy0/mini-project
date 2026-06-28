export default function QuizPanel({
  quizData,
  currentQuestionIndex,
  setCurrentQuestionIndex,
  userAnswers,
  setUserAnswers,
  handleSubmitQuiz,
  quizScore,
  showReview
}) {
  if (!quizData.length) return null;

  const currentQuestion = quizData[currentQuestionIndex];

  function handleAnswer(option) {
    setUserAnswers((prev) => ({
      ...prev,
      [currentQuestionIndex]: option,
    }));
  }

  return (
    <section className="card">
      <h4>
        Question {currentQuestionIndex + 1} of {quizData.length}
      </h4>

      <p>{currentQuestion.question}</p>

      <div className="quiz-options">
        {Object.entries(currentQuestion.options).map(([key, value]) => (
          <label key={key}>
            <input
              type="radio"
              name={`question-${currentQuestionIndex}`}
              checked={userAnswers[currentQuestionIndex] === key}
              onChange={() => handleAnswer(key)}
            />
            {key}. {value}
          </label>
        ))}
      </div>

      <div className="quiz-navigation">
        {currentQuestionIndex > 0 && (
          <button
            onClick={() =>
              setCurrentQuestionIndex(currentQuestionIndex - 1)
            }
          >
            Previous
          </button>
        )}

        {currentQuestionIndex < quizData.length - 1 && (
          <button
            onClick={() =>
              setCurrentQuestionIndex(currentQuestionIndex + 1)
            }
          >
            Next
          </button>
        )}

        {currentQuestionIndex === quizData.length - 1 && (
          <button onClick={handleSubmitQuiz}>
            Submit Quiz
          </button>
        )}
      </div>

      {quizScore && (
        <div className="quiz-score">
          <h4>
            Score: {quizScore.score}/{quizScore.total}
          </h4>
        </div>
      )}
      {showReview && (
        <div className="quiz-review">
          <h4>Quiz Review</h4>

          {quizData.map((question, index) => (
                 <div key={index}>
                     <p>{question.question}</p>
 
                     <p>
                         Your Answer: {userAnswers[index] || "Not Answered"}
                     </p>

                     <p>
                         Correct Answer: {question.answer}
                     </p>

                     <p>
                         {userAnswers[index] === question.answer ? "✅ Correct" : "❌ Wrong"}
                    </p>

                    <hr />
                </div>
            ))}
       </div>
    )}
    </section>
  );
}