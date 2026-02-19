const variants = {
  a: {
    plan: "Variant A - Seat Plan",
    price: "$49 / seat / month",
    note: "14-day free trial. Best for teams validating AI coding workflows.",
  },
  b: {
    plan: "Variant B - Hybrid Plan",
    price: "$99 / seat / month",
    note: "Includes usage-based compute pool for heavy test generation.",
  },
};

const messageVariants = {
  clarity: {
    title: "Ship AI-assisted code with confidence, not guesswork.",
    subtitle:
      "MergeGuard catches risky AI-generated diffs before merge with automated test generation, PR risk heatmaps, and trust scoring.",
  },
  speed: {
    title: "Cut AI PR review time before regressions hit production.",
    subtitle:
      "MergeGuard prioritizes risky AI-generated diffs so reviewers focus on the few changes most likely to break quality.",
  },
};

const METRICS_KEY = "mergeguard_metrics";
const EVENTS_KEY = "mergeguard_events";

function selectVariant() {
  const params = new URLSearchParams(window.location.search);
  const explicit = params.get("variant");
  if (explicit && variants[explicit]) {
    return explicit;
  }

  const stored = window.localStorage.getItem("mergeguard_variant");
  if (stored && variants[stored]) {
    return stored;
  }

  const random = Math.random() < 0.5 ? "a" : "b";
  window.localStorage.setItem("mergeguard_variant", random);
  return random;
}

function selectMessageVariant() {
  const params = new URLSearchParams(window.location.search);
  const explicit = params.get("message");
  if (explicit && messageVariants[explicit]) {
    return explicit;
  }

  const stored = window.localStorage.getItem("mergeguard_message");
  if (stored && messageVariants[stored]) {
    return stored;
  }

  const random = Math.random() < 0.5 ? "clarity" : "speed";
  window.localStorage.setItem("mergeguard_message", random);
  return random;
}

function setPricing(variantKey) {
  const variant = variants[variantKey];
  document.getElementById("plan-name").textContent = variant.plan;
  document.getElementById("plan-price").textContent = variant.price;
  document.getElementById("plan-note").textContent = variant.note;
  document.getElementById("variant-badge").textContent = `Pricing experiment: Variant ${variantKey.toUpperCase()}`;
  document.getElementById("variant-input").value = variantKey;
}

function setMessageVariant(messageKey) {
  const variant = messageVariants[messageKey];
  document.querySelector(".hero h1").textContent = variant.title;
  document.querySelector(".hero .subtitle").textContent = variant.subtitle;
  document.getElementById("message-badge").textContent = `Message experiment: ${messageKey}`;
}

function defaultMetrics() {
  return { views: 0, ctaClicks: 0, submits: 0 };
}

function readMetrics() {
  const parsed = JSON.parse(window.localStorage.getItem(METRICS_KEY) || "null");
  if (!parsed) {
    return defaultMetrics();
  }
  return {
    views: Number(parsed.views || 0),
    ctaClicks: Number(parsed.ctaClicks || 0),
    submits: Number(parsed.submits || 0),
  };
}

function writeMetrics(metrics) {
  window.localStorage.setItem(METRICS_KEY, JSON.stringify(metrics));
}

function recordEvent(type, payload) {
  const events = JSON.parse(window.localStorage.getItem(EVENTS_KEY) || "[]");
  events.push({
    type,
    payload,
    at: new Date().toISOString(),
  });
  window.localStorage.setItem(EVENTS_KEY, JSON.stringify(events));
}

function renderMetrics() {
  const metrics = readMetrics();
  const rate = metrics.views ? ((metrics.submits / metrics.views) * 100).toFixed(1) : "0.0";
  document.getElementById("metric-views").textContent = String(metrics.views);
  document.getElementById("metric-cta").textContent = String(metrics.ctaClicks);
  document.getElementById("metric-submits").textContent = String(metrics.submits);
  document.getElementById("metric-rate").textContent = `${rate}%`;
}

function incrementMetric(key) {
  const metrics = readMetrics();
  metrics[key] += 1;
  writeMetrics(metrics);
  renderMetrics();
}

function setupCTAEvents() {
  const ctaButtons = document.querySelectorAll("[data-cta]");
  ctaButtons.forEach((button) => {
    button.addEventListener("click", () => {
      incrementMetric("ctaClicks");
      recordEvent("cta_click", { cta: button.getAttribute("data-cta") });
    });
  });
}

function setupExperimentConsole() {
  const exportButton = document.getElementById("export-json");
  const resetButton = document.getElementById("reset-metrics");
  exportButton.addEventListener("click", () => {
    const payload = {
      metrics: readMetrics(),
      events: JSON.parse(window.localStorage.getItem(EVENTS_KEY) || "[]"),
      submissions: JSON.parse(window.localStorage.getItem("mergeguard_waitlist") || "[]"),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "mergeguard-experiment-export.json";
    link.click();
    URL.revokeObjectURL(url);
  });

  resetButton.addEventListener("click", () => {
    window.localStorage.removeItem(METRICS_KEY);
    window.localStorage.removeItem(EVENTS_KEY);
    window.localStorage.removeItem("mergeguard_waitlist");
    renderMetrics();
  });
}

function setupForm() {
  const form = document.getElementById("waitlist-form");
  const status = document.getElementById("form-status");

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());

    // Local capture keeps this MVP deployable without backend services.
    const submissions = JSON.parse(window.localStorage.getItem("mergeguard_waitlist") || "[]");
    submissions.push({ ...data, submittedAt: new Date().toISOString() });
    window.localStorage.setItem("mergeguard_waitlist", JSON.stringify(submissions));
    incrementMetric("submits");
    recordEvent("waitlist_submit", { variant: data.variant });

    status.textContent = "Request saved. We will contact you for pilot qualification.";
    form.reset();
  });
}

const variantKey = selectVariant();
const messageKey = selectMessageVariant();
setPricing(variantKey);
setMessageVariant(messageKey);
incrementMetric("views");
recordEvent("page_view", { variant: variantKey, message: messageKey });
renderMetrics();
setupCTAEvents();
setupForm();
setupExperimentConsole();
