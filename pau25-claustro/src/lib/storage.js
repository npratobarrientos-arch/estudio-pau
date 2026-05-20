const KEY = "pau25-progress-v1";
const SETTINGS_KEY = "pau25-settings-v1";

export function loadProgress() {
  try { return JSON.parse(localStorage.getItem(KEY)) || {}; }
  catch { return {}; }
}

export function saveProgress(progress) {
  localStorage.setItem(KEY, JSON.stringify(progress));
}

export function getTopicStatus(subjectId, topicId) {
  const p = loadProgress();
  return p[subjectId]?.[topicId] || "unseen";
}

export function setTopicStatus(subjectId, topicId, status) {
  const p = loadProgress();
  if (!p[subjectId]) p[subjectId] = {};
  p[subjectId][topicId] = status;
  saveProgress(p);
}

export function loadSettings() {
  try {
    return JSON.parse(localStorage.getItem(SETTINGS_KEY)) || { factoryMode: false, sessionMinutes: 30 };
  } catch {
    return { factoryMode: false, sessionMinutes: 30 };
  }
}

export function saveSettings(settings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}
