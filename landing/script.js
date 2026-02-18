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

function setPricing(variantKey) {
  const variant = variants[variantKey];
  document.getElementById("plan-name").textContent = variant.plan;
  document.getElementById("plan-price").textContent = variant.price;
  document.getElementById("plan-note").textContent = variant.note;
  document.getElementById("variant-badge").textContent = `Pricing experiment: Variant ${variantKey.toUpperCase()}`;
  document.getElementById("variant-input").value = variantKey;
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

    status.textContent = "Request saved. We will contact you for pilot qualification.";
    form.reset();
  });
}

const variantKey = selectVariant();
setPricing(variantKey);
setupForm();
