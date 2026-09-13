const THEME_KEY = "budge-theme";

function applyStoredTheme() {
  try {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored) document.documentElement.dataset.theme = stored;
  } catch {
    // localStorage unavailable (private browsing, etc.) — system preference still applies.
  }
}

function toggleTheme() {
  const systemPrefersDark = matchMedia("(prefers-color-scheme: dark)").matches;
  const current = document.documentElement.dataset.theme ?? (systemPrefersDark ? "dark" : "light");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try {
    localStorage.setItem(THEME_KEY, next);
  } catch {
    // Ignore — theme just won't persist across reloads.
  }
}

applyStoredTheme();
// Signed-out pages have no nav, so no toggle to wire up.
document.getElementById("theme-toggle")?.addEventListener("click", toggleTheme);
