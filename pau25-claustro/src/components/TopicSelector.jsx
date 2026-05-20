import { useState, useEffect } from "react";
import { loadProgress } from "../lib/storage.js";
import { BRIDGES } from "../data/connections.js";
import { SUBJECTS } from "../data/subjects.js";

const page = {
  minHeight: "100vh", background: "#0f0f23", color: "#e8e0d4",
  fontFamily: "'Segoe UI', system-ui, sans-serif",
  padding: "32px 24px 80px"
};
const container = { maxWidth: 900, margin: "0 auto" };
const backBtn = {
  background: "transparent", color: "#888", border: "1px solid #2d2d4e",
  padding: "8px 14px", borderRadius: 8, cursor: "pointer", fontSize: 13,
  marginBottom: 18
};
const profCard = (color) => ({
  background: "#13132a", border: `1px solid ${color}55`,
  borderRadius: 14, padding: 22, marginBottom: 24,
  display: "flex", gap: 18, alignItems: "center"
});
const avatar = (color) => ({
  background: `${color}33`, color, width: 64, height: 64, borderRadius: 32,
  display: "flex", alignItems: "center", justifyContent: "center",
  fontSize: 32, flexShrink: 0
});
const topicRow = (color) => ({
  background: "#13132a", border: "1px solid #2d2d4e",
  borderRadius: 12, padding: 16, marginBottom: 10, cursor: "pointer",
  display: "flex", alignItems: "center", gap: 14,
  transition: "border-color 0.15s ease, transform 0.15s ease"
});
const topicChip = (color) => ({
  background: color, color: "#fff", width: 36, height: 36, borderRadius: 18,
  display: "flex", alignItems: "center", justifyContent: "center",
  fontWeight: 700, flexShrink: 0
});
const examBtn = (color) => ({
  background: `${color}22`, color, border: `1px solid ${color}`,
  padding: "12px 18px", borderRadius: 10, cursor: "pointer",
  fontWeight: 600, marginTop: 18, fontSize: 14, width: "100%"
});
const bridgeBtn = (color) => ({
  background: "transparent", color, border: `1px solid ${color}55`,
  padding: "10px 14px", borderRadius: 8, cursor: "pointer",
  fontSize: 13, marginLeft: 8
});
const bridgeBox = (color) => ({
  background: "#13132a", border: `1px dashed ${color}55`,
  borderRadius: 10, padding: 14, marginTop: 12, fontSize: 13,
  color: "#cccccc", lineHeight: 1.6
});

const STATUS_ICON = { unseen: "⚪", "in-progress": "🟡", mastered: "🟢" };
const STATUS_LABEL = { unseen: "Sin ver", "in-progress": "En progreso", mastered: "Dominado" };

export default function TopicSelector({ subject, onPickTopic, onBack, onSurpriseExam }) {
  const [progress, setProgress] = useState({});
  const [showBridges, setShowBridges] = useState(false);

  useEffect(() => {
    setProgress(loadProgress());
  }, [subject]);

  const status = (topicId) => progress[subject.id]?.[topicId] || "unseen";

  const hasBridges = subject.id === "historia" || subject.id === "filosofia";
  const myBridges = BRIDGES.filter(b =>
    b.from.subject === subject.id || b.to.subject === subject.id
  );

  function pickSurprise() {
    const eligible = subject.topics.filter(t => {
      const s = status(t.id);
      return s === "in-progress" || s === "mastered";
    });
    if (eligible.length === 0) {
      alert("Aún no has estudiado ningún punto. Estudia primero alguno.");
      return;
    }
    const pick = eligible[Math.floor(Math.random() * eligible.length)];
    onSurpriseExam(pick);
  }

  return (
    <div style={page}>
      <div style={container}>
        <button style={backBtn} onClick={onBack}>← Volver al claustro</button>

        <div style={profCard(subject.color)}>
          <div style={avatar(subject.color)}>{subject.emoji}</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: "Georgia, serif", fontSize: 22, color: "#e8e0d4" }}>
              {subject.professor.name}
            </div>
            <div style={{ color: subject.color, fontSize: 13, fontWeight: 600, margin: "2px 0 6px" }}>
              {subject.professor.title}
            </div>
            <div style={{ color: "#888", fontSize: 12, lineHeight: 1.5 }}>
              {subject.professor.credentials}
            </div>
          </div>
          {hasBridges && (
            <button
              style={bridgeBtn(subject.color)}
              onClick={() => setShowBridges(v => !v)}
            >
              🌉 {showBridges ? "Ocultar" : "Ver"} puentes
            </button>
          )}
        </div>

        {hasBridges && showBridges && (
          <div style={{ marginBottom: 22 }}>
            {myBridges.map((b, i) => {
              const otherSubjId = b.from.subject === subject.id ? b.to.subject : b.from.subject;
              const otherSubj = SUBJECTS.find(s => s.id === otherSubjId);
              const myTopicId = b.from.subject === subject.id ? b.from.topic : b.to.topic;
              const myTopic = subject.topics.find(t => t.id === myTopicId);
              const otherTopicId = b.from.subject === subject.id ? b.to.topic : b.from.topic;
              const otherTopic = otherSubj?.topics.find(t => t.id === otherTopicId);
              return (
                <div key={i} style={bridgeBox(subject.color)}>
                  <div style={{ fontWeight: 600, marginBottom: 6, color: subject.color }}>
                    {subject.emoji} Punto {myTopicId} — {myTopic?.title}
                    {" ↔ "}
                    {otherSubj?.emoji} Punto {otherTopicId} — {otherTopic?.title}
                  </div>
                  {b.note}
                </div>
              );
            })}
          </div>
        )}

        <h2 style={{ fontFamily: "Georgia, serif", color: "#e8e0d4", fontSize: 24, margin: "8px 0 16px" }}>
          Temario · {subject.short}
        </h2>

        {subject.topics.map(t => {
          const s = status(t.id);
          return (
            <div
              key={t.id}
              style={topicRow(subject.color)}
              onClick={() => onPickTopic(t)}
              onMouseEnter={e => { e.currentTarget.style.borderColor = subject.color; e.currentTarget.style.transform = "translateX(4px)"; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "#2d2d4e"; e.currentTarget.style.transform = "translateX(0)"; }}
            >
              <div style={topicChip(subject.color)}>{t.id}</div>
              <div style={{ flex: 1 }}>
                <div style={{ color: "#e8e0d4", fontSize: 15, fontWeight: 600 }}>{t.title}</div>
                <div style={{ color: "#888", fontSize: 12, marginTop: 4 }}>{t.sub}</div>
              </div>
              <div style={{ textAlign: "right", fontSize: 12, color: "#888", flexShrink: 0 }}>
                <div style={{ fontSize: 18 }}>{STATUS_ICON[s]}</div>
                <div>{STATUS_LABEL[s]}</div>
              </div>
            </div>
          );
        })}

        <button style={examBtn(subject.color)} onClick={pickSurprise}>
          🎲 Examen sorpresa — un punto al azar de los ya vistos
        </button>
      </div>
    </div>
  );
}
