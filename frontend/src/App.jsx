import { useEffect, useRef, useState } from "react";
import { api, getToken, setToken } from "./api.js";
import AuthForm from "./components/AuthForm";
import WorkspaceSidebar from "./components/WorkspaceSidebar";
import TabManager from "./components/TabManager";
import AnimatedRoadmap from "./components/AnimatedRoadmap";
import { BookOpen, Sun, Moon, User, FolderClosed, LogOut, Plus, MessageSquare, FileText, Layers } from "lucide-react";

// Default tab that is always present (pinned, cannot be closed)
const CHAT_TAB = { id: "chat", type: "chat", label: "Chat", icon: <MessageSquare size={14} /> };

export default function App() {
  const [form, setForm] = useState({ name: "", email: "", password: "", workspaceName: "" });
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState("login");
  const [user, setUser] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);

  // Theme
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");

  // Chat state
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [activeNodeContext, setActiveNodeContext] = useState(null);

  // Tab management
  const [tabs, setTabs] = useState([CHAT_TAB]);
  const [activeTabId, setActiveTabId] = useState("chat");

  // Roadmap state
  const [activeNodeId, setActiveNodeId] = useState(null);
  const [masteries, setMasteries] = useState({});
  const [roadmapExpanded, setRoadmapExpanded] = useState(false);

  // Roadmap format config — passed to AnimatedRoadmap
  const [roadmapConfig, setRoadmapConfig] = useState(null);

  const toastRef = useRef(null);
  function showToast(msg) {
    setMessage(msg);
    clearTimeout(toastRef.current);
    toastRef.current = setTimeout(() => setMessage(""), 3500);
  }

  // Apply theme to <html> element
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  // ─── Session restore ────────────────────────────────────────────
  useEffect(() => {
    if (getToken()) {
      api.me()
        .then((u) => { setUser(u); loadWorkspaces(); })
        .catch(() => setToken(null));
    }
  }, []);

  // ─── Auth ───────────────────────────────────────────────────────
  function updateField(field, val) { setForm((p) => ({ ...p, [field]: val })); }

  async function handleAuth(e) {
    e.preventDefault();
    try {
      if (mode === "register") {
        await api.register({ name: form.name, email: form.email, password: form.password });
        showToast("Account created — you can log in now.");
        setMode("login");
        return;
      }
      const result = await api.login({ email: form.email, password: form.password });
      setToken(result.access_token);
      const profile = await api.me();
      setUser(profile);
      await loadWorkspaces();
    } catch (err) {
      showToast(err.message);
    }
  }

  function handleLogout() {
    setToken(null);
    setUser(null);
    setWorkspaces([]);
    setSelectedWorkspace(null);
    setDocuments([]);
    setChatHistory([]);
    setTabs([CHAT_TAB]);
    setActiveTabId("chat");
    setActiveNodeId(null);
    setMasteries({});
    setRoadmapExpanded(false);
    setRoadmapConfig(null);
    showToast("Logged out.");
  }

  // ─── Workspaces ─────────────────────────────────────────────────
  async function loadWorkspaces() {
    try {
      const data = await api.listWorkspaces();
      setWorkspaces(data);
    } catch (err) {
      showToast(err.message);
    }
  }

  async function handleCreateWorkspace(e) {
    e.preventDefault();
    try {
      await api.createWorkspace({ name: form.workspaceName });
      updateField("workspaceName", "");
      await loadWorkspaces();
      showToast("Workspace created.");
    } catch (err) {
      showToast(err.message);
    }
  }

  async function handleSelectWorkspace(ws) {
    setSelectedWorkspace(ws);
    setTabs([CHAT_TAB]);
    setActiveTabId("chat");
    setActiveNodeId(null);
    setActiveNodeContext(null);
    setMasteries({});
    setRoadmapExpanded(false);
    setRoadmapConfig(null);
    try {
      const [docs, chat] = await Promise.all([
        api.listDocuments(ws.id),
        api.getChatHistory(ws.id),
      ]);
      setDocuments(docs);
      setChatHistory(chat);
    } catch (err) {
      showToast(err.message);
    }
  }

  function handleBackToWorkspaces() {
    setSelectedWorkspace(null);
    setDocuments([]);
    setChatHistory([]);
    setTabs([CHAT_TAB]);
    setActiveTabId("chat");
    setActiveNodeId(null);
    setActiveNodeContext(null);
    setRoadmapExpanded(false);
    setRoadmapConfig(null);
  }

  // ─── Documents ──────────────────────────────────────────────────
  async function handleAddFile(file) {
    if (!selectedWorkspace) return;
    setLoading(true);
    try {
      await api.uploadDocument(selectedWorkspace.id, file);
      const docs = await api.listDocuments(selectedWorkspace.id);
      setDocuments(docs);
      showToast("File uploaded successfully.");
    } catch (err) {
      showToast(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteFile(docId) {
    if (!selectedWorkspace) return;
    try {
      await api.deleteDocument(selectedWorkspace.id, docId);
      const docs = await api.listDocuments(selectedWorkspace.id);
      setDocuments(docs);
      setTabs((prev) => prev.filter((t) => !(t.type === "document" && t.data?.id === docId)));
      showToast("File removed.");
    } catch (err) {
      showToast(err.message);
    }
  }

  // ─── Open document as a tab ─────────────────────────────────────
  async function handleOpenFileTab(doc) {
    const tabId = `doc-${doc.id}`;
    if (tabs.find((t) => t.id === tabId)) { setActiveTabId(tabId); return; }

    let extractedText = null;
    try {
      const result = await api.getDocumentText(selectedWorkspace.id, doc.id);
      extractedText = result?.content || null;
    } catch (_) {}

    setTabs((prev) => [...prev, { id: tabId, type: "document", label: doc.filename, icon: <FileText size={14} />, data: { ...doc, extractedText } }]);
    setActiveTabId(tabId);
  }

  // ─── Open node answer as a tab ──────────────────────────────────
  async function handleOpenNodeTab(node, currentMasteries) {
    const tabId = `node-${node.id}`;
    if (currentMasteries) setMasteries(currentMasteries);
    setActiveNodeId(node.id);
    setActiveNodeContext({ title: node.title, summary: node.summary });

    if (tabs.find((t) => t.id === tabId)) { setActiveTabId(tabId); return; }

    const pendingTab = {
      id: tabId, type: "node_answer", label: node.title, icon: <BookOpen size={14} />,
      data: { nodeId: node.id, title: node.title, summary: node.summary, difficulty: node.difficulty, subPoints: node.sub_points || [], loadingAnswer: true, answer: null },
    };
    setTabs((prev) => [...prev, pendingTab]);
    setActiveTabId(tabId);

    try {
      const result = await api.getNodeAnswer(selectedWorkspace.id, node.id);
      setTabs((prev) => prev.map((t) => t.id === tabId ? { ...t, data: { ...t.data, answer: result.answer, loadingAnswer: false } } : t));
    } catch (err) {
      setTabs((prev) => prev.map((t) => t.id === tabId ? { ...t, data: { ...t.data, answer: `**Error:** ${err.message}`, loadingAnswer: false } } : t));
    }
  }

  // ─── Tab management ─────────────────────────────────────────────
  function handleTabClose(tabId) {
    setTabs((prev) => prev.filter((t) => t.id !== tabId));
    if (activeTabId === tabId) setActiveTabId("chat");
    if (tabId.startsWith("node-")) {
      const nodeId = tabId.replace("node-", "");
      if (activeNodeId === nodeId) { setActiveNodeId(null); setActiveNodeContext(null); }
    }
  }

  // ─── Chat ────────────────────────────────────────────────────────
  async function handleSendChat(e) {
    e?.preventDefault();
    if (!chatInput.trim() || !selectedWorkspace) return;
    setChatLoading(true);
    try {
      await api.sendChatMessage(selectedWorkspace.id, {
        message: chatInput,
        active_node_title: activeNodeContext?.title || null,
        active_node_summary: activeNodeContext?.summary || null,
      });
      setChatInput("");
      const data = await api.getChatHistory(selectedWorkspace.id);
      setChatHistory(data);
    } catch (err) {
      showToast(err.message);
    } finally {
      setChatLoading(false);
    }
  }

  function handleOpenChatWithNode(nodeCtx) {
    setActiveNodeContext(nodeCtx);
    setActiveTabId("chat");
  }

  // ─── Mastery ─────────────────────────────────────────────────────
  async function handleMarkMastered(nodeId) {
    try {
      await api.markNodeMastered(selectedWorkspace.id, nodeId);
      const graph = await api.getGraph(selectedWorkspace.id);
      if (graph?.masteries) setMasteries(graph.masteries);
      showToast("Concept marked as mastered! 🎉");
    } catch (err) {
      showToast(err.message);
    }
  }

  // ─── Roadmap expand / config ─────────────────────────────────────
  function handleRoadmapConfigured(config) {
    setRoadmapConfig(config);
    setRoadmapExpanded(true);
  }

  // ─── Render ──────────────────────────────────────────────────────
  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo-section">
          <BookOpen className="app-logo-icon" size={18} style={{ color: "var(--accent)" }} />
          <h2>AI Study Companion</h2>
        </div>
        <div className="header-spacer" />
        {/* Theme toggle always visible */}
        <button
          className="theme-toggle-btn"
          onClick={() => setTheme(t => t === "dark" ? "light" : "dark")}
          title="Toggle theme"
        >
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
        </button>
        {user && (
          <div className="header-user-chip">
            <User size={12} /> {user.name}
          </div>
        )}
      </header>

      {!user ? (
        <div className="auth-container">
          <AuthForm mode={mode} form={form} updateField={updateField} handleAuth={handleAuth} setMode={setMode} />
          {message && <p className="message-toast">{message}</p>}
        </div>
      ) : !selectedWorkspace ? (
        /* ─── Workspace Landing ─── */
        <div className="main-layout">
          <div className="workspace-landing">
            <div className="landing-hero">
              <h2>Your Study Workspaces</h2>
              <p>Select a subject to continue, or create a new workspace below.</p>
            </div>

            {workspaces.length > 0 && (
              <div className="workspaces-grid">
                {workspaces.map((ws) => (
                  <div key={ws.id} className="workspace-card" onClick={() => handleSelectWorkspace(ws)}>
                    <div className="workspace-card-icon">
                      <Layers size={24} style={{ color: "var(--accent)" }} />
                    </div>
                    <div className="workspace-card-name">{ws.name}</div>
                    <div className="workspace-card-meta">Open →</div>
                  </div>
                ))}
              </div>
            )}

            <form className="create-workspace-section" onSubmit={handleCreateWorkspace}>
              <input
                className="create-ws-input"
                type="text"
                placeholder="New workspace name (e.g. Operating Systems)"
                value={form.workspaceName}
                onChange={(e) => updateField("workspaceName", e.target.value)}
                required
              />
              <button type="submit" className="create-ws-btn">+ Create</button>
            </form>

            <div style={{ marginTop: 16 }}>
              <button className="secondary-btn" onClick={handleLogout}>Log out</button>
            </div>
          </div>
        </div>
      ) : (
        /* ─── Three-Column Workspace View ─── */
        <div className="main-layout">
          <div className={`workspace-view ${roadmapExpanded ? "roadmap-open" : "roadmap-collapsed"}`}>
            {/* Left: File sidebar */}
            <WorkspaceSidebar
              workspace={selectedWorkspace}
              documents={documents}
              activeDocId={tabs.find((t) => t.id === activeTabId && t.type === "document")?.data?.id}
              onBackClick={handleBackToWorkspaces}
              onFileClick={handleOpenFileTab}
              onAddFile={handleAddFile}
              onDeleteFile={handleDeleteFile}
              onLogout={handleLogout}
            />

            {/* Center: Tab Manager */}
            <TabManager
              tabs={tabs}
              activeTabId={activeTabId}
              onTabClick={setActiveTabId}
              onTabClose={handleTabClose}
              chatHistory={chatHistory}
              chatInput={chatInput}
              setChatInput={setChatInput}
              handleSendChat={handleSendChat}
              chatLoading={chatLoading}
              activeNodeContext={activeNodeContext}
              onClearNodeContext={() => setActiveNodeContext(null)}
              onOpenChatWithNode={handleOpenChatWithNode}
              onMarkMastered={handleMarkMastered}
              masteries={masteries}
            />

            {/* Right: Animated Roadmap */}
            <AnimatedRoadmap
              workspaceId={selectedWorkspace.id}
              documents={documents}
              activeNodeId={activeNodeId}
              onNodeClick={handleOpenNodeTab}
              expanded={roadmapExpanded}
              onToggleExpand={() => setRoadmapExpanded(e => !e)}
              roadmapConfig={roadmapConfig}
              onRoadmapConfigured={handleRoadmapConfigured}
              onMasteriesUpdate={(m) => setMasteries(m)}
            />
          </div>
        </div>
      )}

      {loading && (
        <div className="global-loader-toast">
          <div className="loading-spinner" style={{ width: 20, height: 20, flexShrink: 0 }} />
          Processing…
        </div>
      )}
      {message && <div className="toast-notification">{message}</div>}
    </div>
  );
}