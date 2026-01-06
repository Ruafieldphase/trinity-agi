#!/usr/bin/env node
/**
 * Forecast Feedback Worker v1.2 (self-healing)
 *
 * Polls the Harmony Core Runner metrics and toggles the feedback loop based on
 * RMSE/Drift thresholds. When RMSE spikes the worker disables feedback and
 * enforces a cooldown. After stability is maintained for a configurable window
 * the loop is re-enabled automatically.
 */

const crypto = require("node:crypto");

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const config = {
  runnerStatusUrl: process.env.HARMONY_STATUS_URL || "http://127.0.0.1:8090/status",
  bridgeUrl: process.env.RCL_BRIDGE_URL || "http://127.0.0.1:8091",
  adjustSecret: process.env.ADJUST_SECRET || process.env.RCL_ADJUST_SECRET || "",
  intervalSeconds: Number(process.env.RCL_FEEDBACK_INTERVAL || 5),
  rmseCritical: Number(process.env.RCL_RMSE_CRITICAL || 1.5),
  rmseStable: Number(process.env.RCL_RMSE_STABLE || 0.6),
  driftCritical: Number(process.env.RCL_DRIFT_CRITICAL_PPM || 120000),
  driftStable: Number(process.env.RCL_DRIFT_STABLE_PPM || 20000),
  resumeDelaySeconds: Number(process.env.RCL_RESUME_DELAY || 15)
};

if (!globalThis.fetch) {
  throw new Error("Node 18+ required (fetch API missing).");
}

if (!config.adjustSecret) {
  console.warn("[feedback_worker] Warning: ADJUST_SECRET missing. Requests will fail.");
}

const deterministicStringify = (value) => {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map(deterministicStringify).join(",")}]`;
  }
  const keys = Object.keys(value).sort();
  const entries = keys.map((key) => `${JSON.stringify(key)}:${deterministicStringify(value[key])}`);
  return `{${entries.join(",")}}`;
};

const computeSignature = (secret, timestamp, payload) => {
  const canonicalPayload = deterministicStringify(payload);
  const canonical = `${timestamp}\n${canonicalPayload}`;
  return crypto.createHmac("sha256", secret).update(canonical).digest("hex");
};

async function sendAdjust(payload) {
  if (!config.adjustSecret) {
    throw new Error("ADJUST_SECRET missing for feedback worker.");
  }
  const timestamp = new Date().toISOString();
  const signature = computeSignature(config.adjustSecret, timestamp, payload);
  const response = await fetch(`${config.bridgeUrl}/adjust`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-RCL-Signature": signature
    },
    body: JSON.stringify({
      timestamp,
      payload
    })
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Bridge responded with ${response.status}: ${text}`);
  }
  return response.json();
}

async function fetchStatus() {
  const response = await fetch(config.runnerStatusUrl);
  if (!response.ok) {
    throw new Error(`Runner status failed (${response.status})`);
  }
  return response.json();
}

class FeedbackWorker {
  constructor() {
    this.state = "LOCKED";
    this.stateEnteredAt = Date.now();
    this.lastSentCommand = null;
  }

  get stateDurationSeconds() {
    return (Date.now() - this.stateEnteredAt) / 1000;
  }

  async loopOnce() {
    const status = await fetchStatus();
    const rmse = status.forecast_rmse;
    const drift = Math.abs(status.drift_ppm);

    let desiredState = "LOCKED";
    if (rmse > config.rmseCritical || drift > config.driftCritical) {
      desiredState = "DRIFT";
    } else if (rmse > config.rmseStable || drift > config.driftStable) {
      desiredState = "RECOVER";
    }

    if (desiredState !== this.state) {
      this.state = desiredState;
      this.stateEnteredAt = Date.now();
      console.log(`[feedback_worker] state -> ${this.state}`);
    }

    if (this.state === "DRIFT") {
      await this.ensureFeedbackDisabled("drift");
    } else if (this.state === "RECOVER") {
      await this.ensureFeedbackDisabled("recover");
    } else if (
      this.state === "LOCKED" &&
      this.stateDurationSeconds >= config.resumeDelaySeconds &&
      status.feedback_enabled === false
    ) {
      await this.enableFeedback("stable");
    }

    return { status, state: this.state };
  }

  async ensureFeedbackDisabled(reason) {
    if (this.lastSentCommand === "disable") {
      return;
    }
    console.log(`[feedback_worker] disabling feedback (${reason})`);
    await sendAdjust({
      feedback_enabled: false,
      cooling_mode: "cooldown",
      autotune_gain: 0.8,
      note: `auto_off:${reason}`
    });
    this.lastSentCommand = "disable";
  }

  async enableFeedback(reason) {
    console.log(`[feedback_worker] enabling feedback (${reason})`);
    await sendAdjust({
      feedback_enabled: true,
      cooling_mode: "normal",
      autotune_gain: 1.0,
      note: `auto_on:${reason}`
    });
    this.lastSentCommand = "enable";
  }

  async run() {
    while (true) {
      try {
        await this.loopOnce();
      } catch (error) {
        console.error("[feedback_worker] cycle error:", error.message);
      }
      await sleep(config.intervalSeconds * 1000);
    }
  }
}

function parseArgs(argv) {
  const args = new Set(argv);
  return {
    once: args.has("--once")
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const worker = new FeedbackWorker();
  if (args.once) {
    await worker.loopOnce();
  } else {
    await worker.run();
  }
}

if (require.main === module) {
  main().catch((error) => {
    console.error("[feedback_worker] fatal:", error);
    process.exit(1);
  });
}
