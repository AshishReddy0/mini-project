import React, { useState, useEffect } from "react";
import { Play, Pause, RotateCcw, Timer, Minimize2, Maximize2, Volume2 } from "lucide-react";

export default function FocusTimer({ onTimeUpdate }) {
  const [seconds, setSeconds] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const [mode, setMode] = useState("stopwatch"); // 'stopwatch' | 'pomodoro'
  const [pomodoroMinutes, setPomodoroMinutes] = useState(25);
  const [isExpanded, setIsExpanded] = useState(false);

  // Timer loop
  useEffect(() => {
    let interval = null;
    if (isActive) {
      interval = setInterval(() => {
        setSeconds((prev) => {
          if (mode === "pomodoro") {
            if (prev <= 1) {
              setIsActive(false);
              // Play alert tone if supported
              try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = ctx.createOscillator();
                osc.type = "sine";
                osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
                osc.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + 0.5);
              } catch (_) {}
              alert("🎯 Pomodoro Session Completed! Take a 5-minute break.");
              return 0;
            }
            return prev - 1;
          } else {
            const next = prev + 1;
            if (onTimeUpdate) onTimeUpdate(next);
            return next;
          }
        });
      }, 1000);
    } else {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isActive, mode, onTimeUpdate]);

  function toggleTimer() {
    setIsActive(!isActive);
  }

  function resetTimer() {
    setIsActive(false);
    setSeconds(mode === "pomodoro" ? pomodoroMinutes * 60 : 0);
  }

  function handleModeChange(newMode) {
    setIsActive(false);
    setMode(newMode);
    setSeconds(newMode === "pomodoro" ? pomodoroMinutes * 60 : 0);
  }

  function formatTime(totalSeconds) {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }

  function handleSetPomodoroMinutes(mins) {
    setPomodoroMinutes(mins);
    setIsActive(false);
    setMode("pomodoro");
    setSeconds(mins * 60);
  }

  return (
    <div className="focus-timer-header-widget">
      {/* Compact Pill Bar */}
      <div className="timer-pill" onClick={() => setIsExpanded(!isExpanded)} title="Click to open timer controls">
        <Timer size={14} className={`timer-icon ${isActive ? "pulsing" : ""}`} />
        <span className="timer-display-text">{formatTime(seconds)}</span>
        <span className="timer-mode-badge">{mode === "pomodoro" ? `${pomodoroMinutes}m` : "Focus"}</span>
        <button
          className="timer-inline-play"
          onClick={(e) => {
            e.stopPropagation();
            toggleTimer();
          }}
          title={isActive ? "Pause" : "Start Focus Session"}
        >
          {isActive ? <Pause size={12} /> : <Play size={12} />}
        </button>
      </div>

      {/* Expanded Controls Popover */}
      {isExpanded && (
        <div className="timer-popover">
          <div className="timer-popover-header">
            <h4>Focus Session Timer</h4>
            <button className="icon-btn-small" onClick={() => setIsExpanded(false)}>
              <Minimize2 size={13} />
            </button>
          </div>

          <div className="timer-mode-tabs">
            <button
              className={`mode-tab ${mode === "stopwatch" ? "active" : ""}`}
              onClick={() => handleModeChange("stopwatch")}
            >
              Stopwatch
            </button>
            <button
              className={`mode-tab ${mode === "pomodoro" ? "active" : ""}`}
              onClick={() => handleModeChange("pomodoro")}
            >
              Pomodoro
            </button>
          </div>

          {mode === "pomodoro" && (
            <div className="timer-duration-selector" style={{ display: "flex", gap: 4, marginBottom: 10, justifyContent: "center" }}>
              {[15, 25, 45, 60].map((m) => (
                <button
                  key={m}
                  className={`duration-chip ${pomodoroMinutes === m ? "active" : ""}`}
                  onClick={() => handleSetPomodoroMinutes(m)}
                  style={{
                    padding: "3px 8px",
                    fontSize: "0.72rem",
                    borderRadius: "4px",
                    border: "1px solid var(--border-color)",
                    background: pomodoroMinutes === m ? "var(--primary)" : "var(--bg-sidebar)",
                    color: pomodoroMinutes === m ? "white" : "var(--text-muted)",
                    cursor: "pointer"
                  }}
                >
                  {m}m
                </button>
              ))}
            </div>
          )}

          <div className="timer-big-display">{formatTime(seconds)}</div>

          <div className="timer-controls-row">
            <button className={`timer-action-btn primary ${isActive ? "active" : ""}`} onClick={toggleTimer}>
              {isActive ? <Pause size={14} /> : <Play size={14} />}
              {isActive ? "Pause" : "Start"}
            </button>
            <button className="timer-action-btn secondary" onClick={resetTimer}>
              <RotateCcw size={14} /> Reset
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
