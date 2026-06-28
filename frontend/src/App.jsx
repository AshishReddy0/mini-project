// Minimal connectivity UI for Phase 2 — proves frontend, backend, and DB work together.
// Full screens (revision, exam, quiz, chat) will be built in Phase 4.

import { useEffect, useState } from "react";
import { api, getToken, setToken } from "./api.js";
import AuthForm from "./components/AuthForm";
import WorkspacePanel from "./components/WorkspacePanel";
import DocumentPanel from "./components/DocumentPanel";
import ContentPanel from "./components/ContentPanel";
import ChatPanel from "./components/ChatPanel";
import QuizPanel from "./components/QuizPanel";
import ContentHistoryPanel from "./components/ContentHistoryPanel";

const defaultForm = {
  name: "",
  email: "",
  password: "",
  workspaceName: "",
};

export default function App() {
  const [form, setForm] = useState(defaultForm);
  const [apiStatus, setApiStatus] = useState("checking...");
  const [dbStatus, setDbStatus] = useState("checking...");
  const [user, setUser] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState("login"); // login | register
  const [selectedWorkspace, setSelectedWorkspace] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [generatedContent, setGeneratedContent] = useState("");
  const [quizData, setQuizData] = useState([]);
  const [quizScore, setQuizScore] = useState(null);
  const [showReview, setShowReview] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [topic, setTopic] = useState("");
  const [questionCount, setQuestionCount] = useState(10);
  const [loading, setLoading] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [contentHistory, setContentHistory] = useState([]);
  

  // Check API and database health on page load
  useEffect(() => {
    async function checkHealth() {
      try {
        const health = await api.health();
        setApiStatus(health.status);
      } catch {
        setApiStatus("unreachable");
      }

      try {
        const dbHealth = await api.healthDb();
        setDbStatus(dbHealth.database);
      } catch {
        setDbStatus("unreachable");
      }
    }

    checkHealth();

    // Restore session if a token was saved earlier
    if (getToken()) {
      api
        .me()
        .then(setUser)
        .catch(() => setToken(null));
    }
  }, []);

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleAuth(event) {
    event.preventDefault();
    setMessage("");

    try {
      if (mode === "register") {
        await api.register({
          name: form.name,
          email: form.email,
          password: form.password,
        });
        setMessage("Account created. You can log in now.");
        setMode("login");
        return;
      }

      const result = await api.login({
        email: form.email,
        password: form.password,
      });
      setToken(result.access_token);
      const profile = await api.me();
      setUser(profile);
      await loadWorkspaces();
      setMessage("Logged in successfully.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleCreateWorkspace(event) {
    event.preventDefault();
    setMessage("");

    try {
      await api.createWorkspace({ name: form.workspaceName });
      updateField("workspaceName", "");
      await loadWorkspaces();
      setMessage("Workspace created.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function loadWorkspaces() {
    const data = await api.listWorkspaces();
    setWorkspaces(data);
  }

  async function loadDocuments(workspaceId) {
  try {
     const docs = await api.listDocuments(workspaceId);
     setDocuments(docs);
   } catch (error) {
     setMessage(error.message);
  }
 }

 async function loadChatHistory(workspaceId) {
  try {
    const data = await api.getChatHistory(workspaceId);
    setChatHistory(data);
  } catch (error) {
    setMessage(error.message);
  }
 }

 async function handleSelectWorkspace(workspace) {
  setSelectedWorkspace(workspace);
  await loadDocuments(workspace.id);
  await loadChatHistory(workspace.id);
  await loadContentHistory(workspace.id);
  
 }

 async function loadContentHistory(workspaceId) {
  try {
    const data = await api.listContent(workspaceId);
    setContentHistory(data);
  } catch (error) {
    setMessage(error.message);
  }
 }

 async function handleUploadDocument(event) {
  event.preventDefault();

  if (!selectedWorkspace || !selectedFile) return;

  try {
     await api.uploadDocument(selectedWorkspace.id, selectedFile);
     setMessage("Document uploaded successfully.");
     setSelectedFile(null);
     await loadDocuments(selectedWorkspace.id);
   } catch (error) {
     setMessage(error.message);
   }
 }

 async function handleGenerateRevision() {
  if (!selectedWorkspace) return;

  setLoading(true);
  try {
    const result = await api.generateRevision(selectedWorkspace.id, {
      topic,
      document_id: selectedDocumentId || null,
    });

    setGeneratedContent(result.content);
    setMessage("Revision notes generated.");

    await loadContentHistory(selectedWorkspace.id);

    setLoading(false);
  } catch (error) {
    setMessage(error.message);
    setLoading(false);
  }
}

async function handleGenerateExam() {
  if (!selectedWorkspace) return;

  setLoading(true);
  try {
    const result = await api.generateExam(selectedWorkspace.id, {
      topic,
      document_id: selectedDocumentId || null,
    });

    setGeneratedContent(result.content);
    setMessage("Exam content generated.");

    await loadContentHistory(selectedWorkspace.id);

    setLoading(false);
  } catch (error) {
    setMessage(error.message);
    setLoading(false);
  }
}

async function handleGenerateQuiz() {
  if (!selectedWorkspace) return;

  setLoading(true);
  try {
    const result = await api.generateQuiz(selectedWorkspace.id, {
      topic,
      document_id: selectedDocumentId || null,
      question_count: questionCount,
    });

    const parsedQuiz = JSON.parse(result.content);

    setQuizData(parsedQuiz);
    setCurrentQuestionIndex(0);
    setUserAnswers({});
    setGeneratedContent("");
    
    await loadContentHistory(selectedWorkspace.id);

    setLoading(false);
   } catch (error) {
    setMessage(error.message);
    setLoading(false);
  }
 }

 function handleSubmitQuiz() {
  let score = 0;

  quizData.forEach((question, index) => {
    if (userAnswers[index] === question.answer) {
      score++;
    }
  });

  setQuizScore({
    score,
    total: quizData.length,
  });
  setShowReview(true);
 }

 async function handleSendChat(event) {
  event.preventDefault();

  if (!chatInput || !selectedWorkspace) return;

  setLoading(true);
  try {
    await api.sendChatMessage(selectedWorkspace.id, {
      message: chatInput,
    });

    setChatInput("");
    await loadChatHistory(selectedWorkspace.id);
    setLoading(false);
  } catch (error) {
    setMessage(error.message);
    setLoading(false);
  }
 }

 async function handleDeleteDocument(documentId) {
  if (!selectedWorkspace) return;

  try {
    await api.deleteDocument(selectedWorkspace.id, documentId);
    setMessage("Document deleted successfully.");
    await loadDocuments(selectedWorkspace.id);
  } catch (error) {
    setMessage(error.message);
  }
}

 async function handleDeleteContent(contentId) {
  if (!selectedWorkspace) return;

  try {
    await api.deleteContent(selectedWorkspace.id, contentId);
    await loadContentHistory(selectedWorkspace.id);
    setMessage("Content deleted successfully.");
  } catch (error) {
    setMessage(error.message);
  }
 }

  function handleLogout() {
  setToken(null);
  setUser(null);
  setWorkspaces([]);
  setSelectedWorkspace(null);
  setDocuments([]);
  setSelectedFile(null);
  setGeneratedContent("");
  setTopic("");
  setChatHistory([]);
  setChatInput("");
  setMessage("Logged out.");
}
  return (
    <div className="app">
      <header>
        <h1>AI Study Companion</h1>
      </header>

      <section className="card">
        <h2>System Status</h2>
        <p>
          API: <span className={apiStatus === "ok" ? "ok" : "error"}>{apiStatus}</span>
        </p>
        <p>
          Database:{" "}
          <span className={dbStatus === "connected" ? "ok" : "error"}>{dbStatus}</span>
        </p>
      </section>

      {!user ? (
        <AuthForm
          mode={mode}
          form={form}
          updateField={updateField}
          handleAuth={handleAuth}
          setMode={setMode}
        /> ): (
        <>
          <section className="card">
            <h2>Welcome, {user.name}</h2>
            <p>{user.email}</p>
            <button type="button" onClick={handleLogout}>
              Logout
            </button>
          </section>

          <WorkspacePanel
            form={form}
            updateField={updateField}
            handleCreateWorkspace={handleCreateWorkspace}
            loadWorkspaces={loadWorkspaces}
            workspaces={workspaces}
            handleSelectWorkspace={handleSelectWorkspace}
          />
            {selectedWorkspace && (
           <>
          <DocumentPanel
            selectedWorkspace={selectedWorkspace}
            handleUploadDocument={handleUploadDocument}
            setSelectedFile={setSelectedFile}
            documents={documents}
            handleDeleteDocument={handleDeleteDocument}
          />

          <ContentPanel
            topic={topic}
            setTopic={setTopic}
            handleGenerateRevision={handleGenerateRevision}
            handleGenerateExam={handleGenerateExam}
            handleGenerateQuiz={handleGenerateQuiz}
            generatedContent={generatedContent}
            documents={documents}
            selectedDocumentId={selectedDocumentId}
            setSelectedDocumentId={setSelectedDocumentId}
            questionCount={questionCount}
            setQuestionCount={setQuestionCount}
          />

          <ContentHistoryPanel 
            contentHistory={contentHistory} 
            setGeneratedContent={setGeneratedContent}
            setQuizData={setQuizData}
            handleDeleteContent={handleDeleteContent}
          />

          <QuizPanel
            quizData={quizData}
            currentQuestionIndex={currentQuestionIndex}
            setCurrentQuestionIndex={setCurrentQuestionIndex}
            userAnswers={userAnswers}
            setUserAnswers={setUserAnswers}
            handleSubmitQuiz={handleSubmitQuiz}
            quizScore={quizScore}
            showReview={showReview}
          />

          <ChatPanel
            chatHistory={chatHistory}
            chatInput={chatInput}
            setChatInput={setChatInput}
            handleSendChat={handleSendChat}
          />
        </>
        )}
          {loading && (
          <div className="card">
          <p>⏳ Processing... Please wait</p>
          </div>
         )}
          {message && <p className="message">{message}</p>}
        </>
      )}
    </div>
  );
}