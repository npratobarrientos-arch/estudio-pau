import { useState } from "react";
import Home from "./components/Home.jsx";
import TopicSelector from "./components/TopicSelector.jsx";
import ChatView from "./components/ChatView.jsx";
import HeadOfStudies from "./components/HeadOfStudies.jsx";

export default function App() {
  const [view, setView] = useState("home");
  const [subject, setSubject] = useState(null);
  const [topic, setTopic] = useState(null);
  const [mode, setMode] = useState("study");

  function pickSubject(s) {
    setSubject(s);
    setView("topics");
  }
  function pickTopic(t) {
    setTopic(t);
    setMode("study");
    setView("chat");
  }
  function surpriseExam(t) {
    setTopic(t);
    setMode("exam");
    setView("chat");
  }
  function backToHome() {
    setView("home");
    setSubject(null);
    setTopic(null);
  }
  function backToTopics() {
    setView("topics");
    setTopic(null);
  }

  if (view === "home") {
    return <Home onPickSubject={pickSubject} onPickJefe={() => setView("head")} />;
  }
  if (view === "head") {
    return <HeadOfStudies onBack={backToHome} />;
  }
  if (view === "topics") {
    return (
      <TopicSelector
        subject={subject}
        onPickTopic={pickTopic}
        onBack={backToHome}
        onSurpriseExam={surpriseExam}
      />
    );
  }
  if (view === "chat") {
    return (
      <ChatView
        subject={subject}
        topic={topic}
        mode={mode}
        onBack={backToTopics}
      />
    );
  }
  return null;
}
