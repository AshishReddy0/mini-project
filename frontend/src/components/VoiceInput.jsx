import React, { useState, useEffect, useRef } from "react";
import { Mic, MicOff } from "lucide-react";

export default function VoiceInput({ onTranscript, placeholder = "Speak..." }) {
  const [isListening, setIsListening] = useState(false);
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (transcript && onTranscript) {
        onTranscript(transcript);
      }
      setIsListening(false);
    };

    recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
  }, [onTranscript]);

  function toggleListening(e) {
    e.preventDefault();
    if (!supported || !recognitionRef.current) {
      alert("Speech recognition is not supported in this browser. Please use Google Chrome or MS Edge.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        console.error("Failed to start speech recognition", err);
      }
    }
  }

  if (!supported) return null;

  return (
    <button
      type="button"
      className={`voice-input-btn ${isListening ? "listening" : ""}`}
      onClick={toggleListening}
      title={isListening ? "Listening... Click to stop" : "Click to speak (Dictation)"}
    >
      {isListening ? <MicOff size={14} className="mic-icon pulsing" /> : <Mic size={14} className="mic-icon" />}
    </button>
  );
}
