import { useState, useEffect, useRef } from "react";
import { callClaude } from "../lib/api.js";
import { loadProgress, loadSettings } from "../lib/storage.js";
import { FACTORY_MODE_ADDON, SESSION_TIME_ADDON } from "../data/method.js";
import { HEAD_OF_STUDIES } from "../data/jefe.js";
import { SUBJECTS } from "../data/subjects.js";

const page = {
  minHeight: "100vh", background: "#0f0f23", color: "#e8e0d4",
  fontFamily: "'Segoe UI', system-ui, sans-serif",
  display: "flex", flexDirection: "column"
};
const header = {
  background: "#13132a", borderBottom: `1px solid ${HEAD_OF_STUDIES.color}55`,
  padding: "14px 20px", display: "flex", alignItems: "center", gap: 14,
  position: "sticky", top: 0, zIndex: 10
};
const headerAvatar = {
  background: `${HEAD_OF_STUDIES.color}33`, color: HEAD_OF_STUDIES.color,
  width: 44, height: 44, borderRadius: 22,
  display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22
};
const backBtn = {
  background: "transparent", color: "#888", border: "1px solid #2d2d4e",
  padding: "6px 12px", borderRadius: 8, cursor: "pointer", fontSize: 12
};
const messagesBox = {
  flex: 1, overflowY: "auto", padding: "20px 16px",
  maxWidth: 900, width: "100%", margin: "0 auto"
};
const msgRow = (role) => ({
  display: "flex", justifyContent: role === "user" ? "flex-end" : "flex-start",
  marginBottom: 14
});
const msgBubble = (role) => ({
  maxWidth: "78%", padding: "12px 16px", borderRadius: 14,
  background: role === "user" ? HEAD_OF_STUDIES.color : "#1e1e3a",
  color: role === "user" ? "#fff" : "#e8e0d4",
  fontSize: 15, lineHeight: 1.55, whiteSpace: "pre-wrap", wordBreak: "break-word"
});
const chips = {
  display: "flex", gap: 8, flexWrap: "wrap",
  padding: "10px 16px 0", maxWidth: 900, margin: "0 auto", width: "100%"
};
const chip = {
  background: `${HEAD_OF_STUDIES.color}22`, color: HEAD_OF_STUDIES.color,
  border: `1px solid ${HEAD_OF_STUDIES.color}44`,
  padding: "6px 12px", borderRadius: 16, cursor: "pointer", fontSize: 12
};
const inputBar = {
  display: "flex", gap: 10, padding: 16, borderTop: "1px solid #2d2d4e",
  background: "#0f0f23", maxWidth: 900, margin: "0 auto", width: "100%", boxSizing: "border-box"
};
const textarea = {
  flex: 1, background: "#1a1a2e", color: "#e8e0d4",
  border: "1px solid #2d2d4e", borderRadius: 10, padding: "10px 14px",
  fontSize: 15, fontFamily: "inherit", resize: "none", minHeight: 44, outline: "none"
};
const sendBtn = {
  background: HEAD_OF_STUDIES.color, color: "#fff", border: "none",
  padding: "0 22px", borderRadius: 10, cursor: "pointer", fontWeight: 600, fontSize: 15
};
const dotsRow = { display: "flex", gap: 4, padding: "10px 14px" };
const dot = (i) => ({
  width: 8, height: 8, borderRadius: 4, background: "#888",
  animation: `bounce 1.2s infinite ${i * 0.2}s`
});

const QUICK_CHIPS = [
  "¿Qué estudio hoy?",
  "¿Cómo voy?",
  "Estoy agobiado, ayúdame",
  "Quiero ver mi plan de la semana"
];

function progressSummary() {
  const p = loadProgress();
  const lines = SUBJECTS.map(s => {
    const stats = s.topics.reduce((acc, t) => {
      const st = p[s.id]?.[t.id] || "unseen";
      acc[st] = (acc[st] || 0) + 1;
      return acc;
    }, {});
    return `• ${s.short} (${s.topics.length} puntos): ${stats.mastered || 0} dominados, ${stats["in-progress"] || 0} en progreso, ${stats.unseen || s.topics.length} sin ver`;
  });
  return lines.join("\n");
}

export default function HeadOfStudies({ onBack }) {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  function buildSystemPrompt() {
    const settings = loadSettings();
    let sys = HEAD_OF_STUDIES.systemPrompt;
    if (settings.factoryMode) sys += "\n\n" + FACTORY_MODE_ADDON;
    sys += "\n\n" + SESSION_TIME_ADDON(settings.sessionMinutes);
    sys += `\n\nESTADO ACTUAL DEL ALUMNO (progreso guardado):\n${progressSummary()}\n\nFECHA DE HOY: ${new Date().toLocaleDateString("es-ES", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}`;
    return sys;
  }

  useEffect(() => {
    sendMessage("Hola, ¿qué tal? ¿En qué me orientas hoy?", true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [msgs, loading]);

  async function sendMessage(text, isKickoff = false) {
    if (!text.trim() || loading) return;
    const newUserMsg = { role: "user", content: text };
    const baseMsgs = isKickoff ? [] : msgs;
    const next = [...baseMsgs, newUserMsg];
    setMsgs(isKickoff ? [{ role: "user", content: text, hidden: true }] : next);
    setInput("");
    setLoading(true);
    try {
      const apiMessages = next.map(m => ({ role: m.role, content: m.content }));
      const reply = await callClaude({
        systemPrompt: buildSystemPrompt(),
        messages: apiMessages,
        maxTokens: 1000
      });
      setMsgs(prev => [...(isKickoff ? [] : prev), { role: "assistant", content: reply }]);
    } catch (e) {
      setMsgs(prev => [...prev, { role: "assistant", content: `⚠️ Error: ${e.message}. Comprueba tu API key en .env.local.` }]);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  const visibleMsgs = msgs.filter(m => !m.hidden);

  return (
    <div style={page}>
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-6px); opacity: 1; }
        }
      `}</style>
      <div style={header}>
        <button style={backBtn} onClick={onBack}>←</button>
        <div style={headerAvatar}>{HEAD_OF_STUDIES.emoji}</div>
        <div>
          <div style={{ fontFamily: "Georgia, serif", fontSize: 17 }}>
            {HEAD_OF_STUDIES.professor.name}
          </div>
          <div style={{ color: HEAD_OF_STUDIES.color, fontSize: 12, fontWeight: 600 }}>
            {HEAD_OF_STUDIES.professor.title}
          </div>
        </div>
      </div>

      <div style={messagesBox} ref={scrollRef}>
        {visibleMsgs.map((m, i) => (
          <div key={i} style={msgRow(m.role)}>
            <div style={msgBubble(m.role)}>{m.content}</div>
          </div>
        ))}
        {loading && (
          <div style={msgRow("assistant")}>
            <div style={{ ...msgBubble("assistant"), padding: 0 }}>
              <div style={dotsRow}>
                <div style={dot(0)}></div>
                <div style={dot(1)}></div>
                <div style={dot(2)}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div style={chips}>
        {QUICK_CHIPS.map((c, i) => (
          <button key={i} style={chip} onClick={() => sendMessage(c)} disabled={loading}>{c}</button>
        ))}
      </div>

      <div style={inputBar}>
        <textarea
          style={textarea}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="¿En qué necesitas orientación?"
          rows={1}
        />
        <button style={sendBtn} onClick={() => sendMessage(input)} disabled={loading || !input.trim()}>
          Enviar
        </button>
      </div>
    </div>
  );
}
