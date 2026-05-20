import { useState } from "react";
import { SUBJECTS } from "../data/subjects.js";
import SettingsBar from "./SettingsBar.jsx";

const page = {
  minHeight: "100vh", background: "#0f0f23", color: "#e8e0d4",
  fontFamily: "'Segoe UI', system-ui, sans-serif",
  padding: "40px 24px 80px"
};
const container = { maxWidth: 1100, margin: "0 auto" };
const header = { textAlign: "center", marginBottom: 32 };
const h1 = {
  fontFamily: "Georgia, 'Times New Roman', serif", fontSize: 44,
  margin: 0, color: "#e8e0d4", letterSpacing: 0.5
};
const subtitle = { color: "#888", fontSize: 16, marginTop: 8 };

const topBar = {
  display: "flex", justifyContent: "space-between", alignItems: "center",
  maxWidth: 1100, margin: "0 auto 24px"
};

const jefeBtn = {
  background: "linear-gradient(135deg, #7F8C8D, #95A5A6)",
  color: "#fff", border: "none", padding: "12px 22px",
  borderRadius: 30, fontSize: 15, fontWeight: 600, cursor: "pointer",
  boxShadow: "0 4px 14px rgba(127, 140, 141, 0.3)",
  display: "inline-flex", alignItems: "center", gap: 8
};
const settingsBtn = {
  background: "transparent", color: "#888", border: "1px solid #2d2d4e",
  padding: "10px 14px", borderRadius: 8, cursor: "pointer", fontSize: 14
};

const grid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
  gap: 18,
  marginTop: 16
};

const stats = {
  marginTop: 48, padding: "20px 0", borderTop: "1px solid #2d2d4e",
  display: "flex", justifyContent: "center", gap: 36, flexWrap: "wrap",
  color: "#7a7a7a", fontSize: 13, letterSpacing: 0.4
};
const statItem = { display: "flex", flexDirection: "column", alignItems: "center" };
const statNum = { fontFamily: "Georgia, serif", fontSize: 24, color: "#e8e0d4" };

function SubjectCard({ subject, onClick }) {
  const [hover, setHover] = useState(false);
  const cardStyle = {
    background: hover ? `linear-gradient(135deg, ${subject.color}22, #13132a)` : "#13132a",
    border: `1px solid ${hover ? subject.color : "#2d2d4e"}`,
    borderRadius: 14, padding: 22, cursor: "pointer",
    transition: "transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease",
    transform: hover ? "translateY(-4px)" : "translateY(0)",
    boxShadow: hover ? `0 12px 28px ${subject.color}33` : "0 2px 6px rgba(0,0,0,0.2)"
  };
  return (
    <div
      style={cardStyle}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onClick={onClick}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ fontSize: 42 }}>{subject.emoji}</div>
        <span style={{
          background: `${subject.color}22`, color: subject.color,
          padding: "4px 10px", borderRadius: 14, fontSize: 11,
          fontWeight: 600, letterSpacing: 0.3
        }}>{subject.tag}</span>
      </div>
      <h3 style={{
        fontFamily: "Georgia, serif", color: "#e8e0d4",
        fontSize: 22, margin: "12px 0 4px"
      }}>{subject.name}</h3>
      <div style={{ color: subject.color, fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
        {subject.professor.name}
      </div>
      <div style={{ color: "#888", fontSize: 13, lineHeight: 1.5 }}>{subject.desc}</div>
    </div>
  );
}

export default function Home({ onPickSubject, onPickJefe }) {
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div style={page}>
      <div style={topBar}>
        <button style={jefeBtn} onClick={onPickJefe}>🎩 Hablar con el Jefe de Estudios</button>
        <button style={settingsBtn} onClick={() => setShowSettings(true)}>⚙️ Ajustes</button>
      </div>

      <div style={container}>
        <div style={header}>
          <h1 style={h1}>Claustro de Catedráticos</h1>
          <div style={subtitle}>Tu equipo PAU+25 · Artes y Humanidades · UV</div>
        </div>

        <div style={grid}>
          {SUBJECTS.map(s => (
            <SubjectCard key={s.id} subject={s} onClick={() => onPickSubject(s)} />
          ))}
        </div>

        <div style={stats}>
          <div style={statItem}><div style={statNum}>6</div>catedráticos</div>
          <div style={statItem}><div style={statNum}>55</div>puntos de temario</div>
          <div style={statItem}><div style={statNum}>16</div>exámenes analizados</div>
        </div>
      </div>

      {showSettings && <SettingsBar onClose={() => setShowSettings(false)} />}
    </div>
  );
}
