import { useState } from "react";
import { loadSettings, saveSettings } from "../lib/storage.js";

const overlay = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,0.65)",
  display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100
};
const panel = {
  background: "#13132a", border: "1px solid #2d2d4e", borderRadius: 14,
  padding: 28, width: "min(440px, 92vw)", color: "#e8e0d4",
  fontFamily: "'Segoe UI', system-ui, sans-serif",
  boxShadow: "0 20px 60px rgba(0,0,0,0.6)"
};
const title = {
  fontFamily: "Georgia, serif", fontSize: 22, margin: 0, marginBottom: 18,
  color: "#e8e0d4"
};
const row = { display: "flex", justifyContent: "space-between", alignItems: "center", margin: "18px 0" };
const label = { color: "#e8e0d4", fontSize: 15 };
const sub = { color: "#888", fontSize: 12, marginTop: 4 };
const toggleOn = { background: "#27AE60", color: "#fff", border: "none", padding: "6px 14px", borderRadius: 20, cursor: "pointer", fontWeight: 600 };
const toggleOff = { background: "#2d2d4e", color: "#888", border: "none", padding: "6px 14px", borderRadius: 20, cursor: "pointer", fontWeight: 600 };
const select = {
  background: "#1a1a2e", color: "#e8e0d4", border: "1px solid #2d2d4e",
  padding: "8px 12px", borderRadius: 8, fontSize: 14, cursor: "pointer"
};
const closeBtn = {
  background: "transparent", color: "#e8e0d4", border: "1px solid #2d2d4e",
  padding: "10px 20px", borderRadius: 8, cursor: "pointer", marginTop: 18,
  width: "100%", fontSize: 14
};

export default function SettingsBar({ onClose }) {
  const [settings, setSettings] = useState(loadSettings());

  function update(next) {
    setSettings(next);
    saveSettings(next);
  }

  return (
    <div style={overlay} onClick={onClose}>
      <div style={panel} onClick={e => e.stopPropagation()}>
        <h2 style={title}>⚙️ Ajustes de sesión</h2>

        <div style={row}>
          <div>
            <div style={label}>Modo Fábrica</div>
            <div style={sub}>Sesiones más cortas y tono más cálido cuando vienes del trabajo.</div>
          </div>
          <button
            style={settings.factoryMode ? toggleOn : toggleOff}
            onClick={() => update({ ...settings, factoryMode: !settings.factoryMode })}
          >
            {settings.factoryMode ? "ON" : "OFF"}
          </button>
        </div>

        <div style={row}>
          <div>
            <div style={label}>Duración de sesión</div>
            <div style={sub}>Ajusta la profundidad del catedrático.</div>
          </div>
          <select
            style={select}
            value={settings.sessionMinutes}
            onChange={e => update({ ...settings, sessionMinutes: parseInt(e.target.value, 10) })}
          >
            <option value={15}>15 min</option>
            <option value={30}>30 min</option>
            <option value={45}>45 min</option>
            <option value={60}>60 min</option>
          </select>
        </div>

        <button style={closeBtn} onClick={onClose}>Cerrar</button>
      </div>
    </div>
  );
}
