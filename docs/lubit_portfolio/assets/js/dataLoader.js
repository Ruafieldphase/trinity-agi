const DEFAULT_INLINE_ID = "lubit-data";

function parseJson(text, contextLabel) {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch (error) {
    console.warn(`[LubitDataLoader] Failed to parse ${contextLabel}`, error);
    return null;
  }
}

function readInlinePayload(inlineDataId) {
  const targetId = inlineDataId || DEFAULT_INLINE_ID;
  const node = targetId ? document.getElementById(targetId) : null;
  if (!node) return { payload: null, source: null };
  const payload = parseJson(node.textContent, `inline payload (${targetId})`);
  return payload ? { payload, source: `inline:${targetId}` } : { payload: null, source: null };
}

export function showStatusMessage(message, options = {}) {
  const { containerId = "chart-status", tone = "info" } = options;
  if (!message) return;
  let container = document.getElementById(containerId);
  if (!container) {
    container = document.createElement("div");
    container.id = containerId;
    container.style.marginTop = "1.2rem";
    container.style.padding = "1rem 1.3rem";
    container.style.borderRadius = "12px";
    container.style.border = "1px solid rgba(255,255,255,0.14)";
    container.style.background = "rgba(127, 90, 240, 0.12)";
    container.style.color = "var(--text-muted, #94a3b8)";
    container.style.fontSize = "0.95rem";
    const anchor = document.querySelector("main, body");
    (anchor || document.body).prepend(container);
  }
  container.dataset.tone = tone;
  container.textContent = message;
}

export async function loadLubitData(options = {}) {
  const {
    jsonPath,
    inlineDataId = DEFAULT_INLINE_ID,
    fetchOptions,
    onStatus,
    fallbackMessage = "로컬 JSON을 직접 열고 있다면 간단한 web server (`python -m http.server`)를 사용해 주세요."
  } = options;

  const notify = (message, tone = "info") => {
    if (typeof onStatus === "function") onStatus(message, tone);
  };

  const inline = readInlinePayload(inlineDataId);
  if (!jsonPath) {
    if (inline.payload) {
      notify("inline data loaded (no remote path provided)");
      return { data: inline.payload, source: inline.source || "inline" };
    }
    throw new Error("No jsonPath provided and inline payload missing");
  }

  try {
    const response = await fetch(jsonPath, fetchOptions);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    notify(`Live JSON loaded from ${jsonPath}`);
    return { data, source: `remote:${jsonPath}` };
  } catch (error) {
    console.warn("[LubitDataLoader] Remote fetch failed, trying inline payload", error);
    if (inline.payload) {
      notify("원격 JSON을 불러오지 못해 inline 데이터로 대체합니다.", "warn");
      return { data: inline.payload, source: inline.source || "inline" };
    }
    notify(fallbackMessage, "error");
    throw error;
  }
}
