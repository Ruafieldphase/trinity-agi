(() => {
  const STORAGE_KEY = "rclAdjustSecret";
  const DEFAULT_BRIDGE_URL =
    window.RCL_BRIDGE_URL || `${window.location.protocol}//${window.location.host}`;

  const textEncoder = new TextEncoder();

  function deterministicStringify(value) {
    if (value === null || typeof value !== "object") {
      return JSON.stringify(value);
    }
    if (Array.isArray(value)) {
      return `[${value.map(deterministicStringify).join(",")}]`;
    }
    const keys = Object.keys(value).sort();
    const entries = keys.map((k) => `${JSON.stringify(k)}:${deterministicStringify(value[k])}`);
    return `{${entries.join(",")}}`;
  }

  async function computeSignature(secret, timestamp, payload) {
    const canonicalPayload = deterministicStringify(payload);
    const canonical = `${timestamp}\n${canonicalPayload}`;
    const key = await window.crypto.subtle.importKey(
      "raw",
      textEncoder.encode(secret),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"]
    );
    const signatureBuffer = await window.crypto.subtle.sign(
      "HMAC",
      key,
      textEncoder.encode(canonical)
    );
    const bytes = new Uint8Array(signatureBuffer);
    return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  }

  function loadSecret() {
    return window.localStorage.getItem(STORAGE_KEY) || "";
  }

  function saveSecret(secret) {
    if (secret) {
      window.localStorage.setItem(STORAGE_KEY, secret);
    }
  }

  async function submitAdjust(payload, options = {}) {
    const secret = options.secret || loadSecret();
    if (!secret) {
      throw new Error("Adjust secret missing. Provide one via the input field.");
    }
    const timestamp = new Date().toISOString();
    const body = {
      timestamp,
      payload
    };
    const signature = await computeSignature(secret, timestamp, payload);
    const response = await fetch(`${DEFAULT_BRIDGE_URL}/adjust`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-RCL-Signature": signature
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Adjust failed (${response.status}): ${text}`);
    }
    return response.json();
  }

  function wiring() {
    const secretInput = document.querySelector("[data-rcl-adjust-secret]");
    if (secretInput) {
      const persisted = loadSecret();
      if (persisted) {
        secretInput.value = persisted;
      }
      secretInput.addEventListener("input", (event) => {
        saveSecret(event.target.value.trim());
      });
    }

    const forms = document.querySelectorAll("[data-rcl-adjust-form]");
    forms.forEach((form) => {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(form);
        const payload = {};
        ["sync_rate", "autotune_gain"].forEach((field) => {
          const value = formData.get(field);
          if (value) {
            payload[field] = Number(value);
          }
        });
        const coolingMode = formData.get("cooling_mode");
        if (coolingMode) {
          payload.cooling_mode = coolingMode;
        }
        if (formData.has("feedback_enabled")) {
          payload.feedback_enabled = formData.get("feedback_enabled") === "on";
        }
        const note = formData.get("note");
        if (note) {
          payload.note = note;
        }

        const statusEl = form.querySelector("[data-rcl-adjust-status]");
        try {
          if (statusEl) {
            statusEl.textContent = "Submitting…";
            statusEl.dataset.status = "pending";
          }
          const response = await submitAdjust(payload, { secret: secretInput?.value });
          if (statusEl) {
            statusEl.textContent = `OK • FSM=${response.fsm_state} • Drift=${response.drift_ppm}`;
            statusEl.dataset.status = "ok";
          }
        } catch (error) {
          console.error(error);
          if (statusEl) {
            statusEl.textContent = error.message;
            statusEl.dataset.status = "error";
          }
        }
      });
    });
  }

  window.rclAdjustBridge = {
    submitAdjust,
    computeSignature,
    loadSecret,
    saveSecret
  };

  document.addEventListener("DOMContentLoaded", wiring);
})();

