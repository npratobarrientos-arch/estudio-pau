import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";

const globalStyle = document.createElement("style");
globalStyle.textContent = `
  * { box-sizing: border-box; }
  html, body, #root { margin: 0; padding: 0; min-height: 100%; background: #0f0f23; }
  body { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; color: #e8e0d4; }
  button { font-family: inherit; }
  ::-webkit-scrollbar { width: 10px; height: 10px; }
  ::-webkit-scrollbar-track { background: #0f0f23; }
  ::-webkit-scrollbar-thumb { background: #2d2d4e; border-radius: 5px; }
  ::-webkit-scrollbar-thumb:hover { background: #3d3d5e; }
`;
document.head.appendChild(globalStyle);

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
