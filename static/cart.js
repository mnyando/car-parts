// Cart implementation using localStorage.
// The cart is rendered from state into every [data-cart-root] on the page
// (the slide-out drawer on all pages, plus the main area on /cart).

// Catalog data (makes, price modifiers, spec options) is served by the backend
// in base.html, so prices here always match what /checkout charges.
const CATALOG = window.CATALOG || { makes: {}, makeModifiers: {}, specKinds: {} };

// How long to wait for the customer to enter their M-Pesa PIN
const PAYMENT_POLL_INTERVAL_MS = 4000;
const PAYMENT_POLL_TIMEOUT_MS = 3 * 60 * 1000;

// Each account has its own saved cart on a shared browser
const CART_KEY = `cart:${(window.CURRENT_USER && window.CURRENT_USER.id) || "guest"}`;
const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.content || "";

let cart = loadCart();
// stage: cart | form | submitting | waiting | paid | failed | timeout
let checkoutState = { stage: "cart", phone: (window.CURRENT_USER && window.CURRENT_USER.phone) || "", message: "", orderId: null, reference: null, amount: 0 };
let pollTimer = null;
let selectedBaseProduct = null;

function loadCart() {
  try {
    const stored = JSON.parse(localStorage.getItem(CART_KEY));
    if (!Array.isArray(stored)) return [];
    return stored.filter(item => item && item.id && item.product_id && item.name && Number(item.quantity) > 0)
      .map(item => ({ ...item, price: Number(item.price) || 0, quantity: Number(item.quantity) }));
  } catch (e) {
    return []; // corrupt or unavailable storage shouldn't break the page
  }
}

function saveCart() {
  try {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
  } catch (e) { /* private mode / storage full: cart still works for this page view */ }
  renderCart();
}

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, ch => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
  ));
}

function formatKSh(amount) {
  return `KSh ${Number(amount).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function cartTotal() {
  return cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// --- Cart mutations ---

function addToCart(product) {
  const existing = cart.find(item => item.id === product.id);
  if (existing) {
    existing.quantity += 1;
  } else {
    cart.push({ ...product, quantity: 1 });
  }
  resetCheckout();
  saveCart();
}

function changeQuantity(id, delta) {
  const item = cart.find(ci => ci.id === id);
  if (!item) return;
  item.quantity += delta;
  if (item.quantity < 1) {
    cart = cart.filter(ci => ci.id !== id);
  }
  saveCart();
}

function removeItem(id) {
  cart = cart.filter(ci => ci.id !== id);
  saveCart();
}

function clearCart() {
  cart = [];
  saveCart();
}

// --- Rendering ---

function renderItems() {
  return cart.map(item => `
    <div class="cart-item">
      <img class="cart-item-image" src="${escapeHTML(item.image || "")}" alt="" loading="lazy" decoding="async" />
      <div class="cart-item-info">
        <p class="cart-item-name">${escapeHTML(item.name)}</p>
        <p class="cart-item-price">${formatKSh(item.price)}</p>
      </div>
      <div class="cart-item-controls">
        <button class="cart-qty-btn" data-cart-action="decrease" data-id="${escapeHTML(item.id)}" aria-label="Decrease quantity">&minus;</button>
        <span class="cart-item-quantity">${item.quantity}</span>
        <button class="cart-qty-btn" data-cart-action="increase" data-id="${escapeHTML(item.id)}" aria-label="Increase quantity">&plus;</button>
        <button class="cart-qty-btn cart-remove-btn" data-cart-action="remove" data-id="${escapeHTML(item.id)}" aria-label="Remove item">&times;</button>
      </div>
    </div>`).join("");
}

function renderEmpty() {
  return `
    <div class="cart-empty">
      <p>Your cart is empty.</p>
      <a class="cart-btn" href="/catalog">Browse parts</a>
    </div>`;
}

function renderCheckout() {
  const { stage, phone, message } = checkoutState;
  const busy = stage === "submitting";

  if (stage === "form" || stage === "submitting") {
    return `
      <div class="cart-footer">
        <p class="cart-footer-total">Total: ${formatKSh(cartTotal())}</p>
        <form class="checkout-form-container" data-checkout-form novalidate>
          <div class="field">
            <label>M-Pesa Phone Number
              <input type="tel" name="phone" inputmode="tel" autocomplete="tel" placeholder="e.g. 0712345678" value="${escapeHTML(phone)}" ${busy ? "disabled" : ""} required>
            </label>
          </div>
          <button class="cart-btn" type="submit" ${busy ? "disabled" : ""}>${busy ? "Requesting STK Push..." : "Pay with M-Pesa"}</button>
          <button class="cart-btn cart-btn--ghost" type="button" data-cart-action="back" ${busy ? "disabled" : ""}>Back to Cart</button>
          <div class="checkout-status ${busy ? "" : "error"}" role="status">${escapeHTML(busy ? "Connecting to Safaricom..." : message)}</div>
        </form>
      </div>`;
  }

  if (stage === "waiting") {
    return `
      <div class="checkout-result">
        <p class="checkout-result__title">Check your phone</p>
        <p>Enter your M-Pesa PIN on ${escapeHTML(phone)} to pay ${formatKSh(checkoutState.amount)}.</p>
        <p class="checkout-status" role="status">Waiting for payment confirmation...</p>
        <button class="cart-btn cart-btn--ghost" type="button" data-cart-action="back">Back to Cart</button>
      </div>`;
  }

  if (stage === "paid") {
    return `
      <div class="checkout-result">
        <p class="checkout-result__title">Payment received</p>
        <p class="checkout-status success" role="status">Thank you! Your order ${escapeHTML(checkoutState.reference || "")} is confirmed and will be delivered shortly.</p>
        <a class="cart-btn" href="/catalog" data-cart-action="done">Continue Shopping</a>
      </div>`;
  }

  if (stage === "failed" || stage === "timeout") {
    return `
      <div class="checkout-result">
        <p class="checkout-result__title">${stage === "failed" ? "Payment not completed" : "Still waiting"}</p>
        <p class="checkout-status error" role="status">${escapeHTML(message)}</p>
        <button class="cart-btn" type="button" data-cart-action="checkout">Try Again</button>
        <button class="cart-btn cart-btn--ghost" type="button" data-cart-action="back">Back to Cart</button>
      </div>`;
  }

  return `
    <div class="cart-footer">
      <p class="cart-footer-total">Total: ${formatKSh(cartTotal())}</p>
      <button class="cart-btn" type="button" data-cart-action="checkout">Checkout</button>
      <button class="cart-btn cart-btn--ghost" type="button" data-cart-action="clear">Clear Cart</button>
    </div>`;
}

function renderCart() {
  const showResult = ["waiting", "paid", "failed", "timeout"].includes(checkoutState.stage);
  const html = (cart.length === 0 && !showResult)
    ? renderEmpty()
    : `${showResult ? "" : `<div class="cart">${renderItems()}</div>`}${renderCheckout()}`;

  document.querySelectorAll("[data-cart-root]").forEach(root => { root.innerHTML = html; });

  const count = cart.reduce((sum, item) => sum + item.quantity, 0);
  document.querySelectorAll("[data-cart-count]").forEach(el => { el.innerText = count; });
}

// --- Checkout ---

function setCheckout(changes) {
  checkoutState = { ...checkoutState, ...changes };
  renderCart();
}

function stopPolling() {
  if (pollTimer) clearTimeout(pollTimer);
  pollTimer = null;
}

function resetCheckout() {
  stopPolling();
  checkoutState = { ...checkoutState, stage: "cart", message: "", orderId: null };
}

async function submitCheckout(phoneValue) {
  const phone = phoneValue.replace(/[\s\-()]/g, "");
  // Accepts 07XXXXXXXX, 01XXXXXXXX, 2547XXXXXXXX, +2547XXXXXXXX (server normalizes)
  if (!phone.match(/^(\+?254|0)?[17]\d{8}$/)) {
    setCheckout({ stage: "form", phone: phoneValue, message: "Please enter a valid Safaricom number, e.g. 0712345678 or 254712345678." });
    return;
  }

  setCheckout({ stage: "submitting", phone: phoneValue, message: "" });
  try {
    // Send every cart line; the server re-prices them from the catalog
    const response = await fetch("/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": CSRF_TOKEN },
      body: JSON.stringify({
        phone: phone,
        items: cart.map(item => ({ product_id: item.product_id, options: item.options || {}, quantity: item.quantity }))
      })
    });
    const result = await response.json().catch(() => ({}));
    if (response.status === 401) {
      location.href = result.login_url || "/login";
      return;
    }
    if (!response.ok) {
      throw new Error(result.error || "Failed to start checkout");
    }
    setCheckout({ stage: "waiting", orderId: result.order_id, reference: result.reference, amount: result.amount });
    pollPaymentStatus(result.order_id, Date.now());
  } catch (err) {
    setCheckout({ stage: "form", message: `Error: ${err.message}` });
  }
}

function pollPaymentStatus(orderId, startedAt) {
  stopPolling();
  pollTimer = setTimeout(async () => {
    if (checkoutState.stage !== "waiting" || checkoutState.orderId !== orderId) return;
    let status = "pending";
    try {
      const response = await fetch(`/orders/${encodeURIComponent(orderId)}/status`);
      if (response.ok) status = (await response.json()).status;
    } catch (e) { /* network blip: keep polling */ }

    if (checkoutState.stage !== "waiting" || checkoutState.orderId !== orderId) return;

    if (status === "paid") {
      cart = [];
      try { localStorage.removeItem(CART_KEY); } catch (e) { /* ignore */ }
      setCheckout({ stage: "paid" });
    } else if (status === "cancelled") {
      setCheckout({ stage: "failed", message: "The payment request was cancelled on your phone. Your cart has been kept." });
    } else if (status === "failed") {
      setCheckout({ stage: "failed", message: "The payment did not go through (e.g. wrong PIN, insufficient funds or timeout). Your cart has been kept." });
    } else if (status === "amount_mismatch") {
      setCheckout({ stage: "failed", message: `We received a payment that doesn't match the order total. Please contact us with order reference ${checkoutState.reference}.` });
    } else if (Date.now() - startedAt > PAYMENT_POLL_TIMEOUT_MS) {
      setCheckout({ stage: "timeout", message: `We haven't received confirmation yet. If you completed the payment, please contact us with order reference ${checkoutState.reference}.` });
    } else {
      pollPaymentStatus(orderId, startedAt);
    }
  }, PAYMENT_POLL_INTERVAL_MS);
}

function openCartDrawer() {
  const drawer = document.querySelector(".cart-drawer");
  if (drawer) {
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
  }
}

// One delegated handler for every cart root
document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-cart-action]");
  if (!btn || !btn.closest("[data-cart-root]")) return;
  const id = btn.getAttribute("data-id");

  switch (btn.getAttribute("data-cart-action")) {
    case "increase": changeQuantity(id, 1); break;
    case "decrease": changeQuantity(id, -1); break;
    case "remove": removeItem(id); break;
    case "clear": clearCart(); break;
    case "checkout": stopPolling(); setCheckout({ stage: "form", message: "" }); break;
    case "back": resetCheckout(); renderCart(); break;
    case "done": resetCheckout(); break;
  }
});

document.addEventListener("submit", (e) => {
  const form = e.target.closest("[data-checkout-form]");
  if (!form) return;
  e.preventDefault();
  submitCheckout(form.elements.phone.value);
});

// Keep the typed phone number when the cart re-renders (e.g. drawer and page both open)
document.addEventListener("input", (e) => {
  if (e.target.matches("[data-checkout-form] input[name=phone]")) {
    checkoutState.phone = e.target.value;
  }
});

// Another tab changed the cart
window.addEventListener("storage", (e) => {
  if (e.key === CART_KEY) {
    cart = loadCart();
    renderCart();
  }
});

// --- Selection modal (vehicle make/model or part specifications) ---

function fillSelect(selectEl, placeholder, options) {
  selectEl.innerHTML = "";
  const first = document.createElement("option");
  first.value = "";
  first.innerText = placeholder;
  selectEl.appendChild(first);
  Object.entries(options).forEach(([value, text]) => {
    const opt = document.createElement("option");
    opt.value = value;
    opt.innerText = text;
    selectEl.appendChild(opt);
  });
}

function openSelectionModal(baseProduct) {
  selectedBaseProduct = baseProduct;
  const vehicleModal = document.getElementById("vehicle-modal");
  if (!vehicleModal) return;

  const spec = CATALOG.specKinds[baseProduct.kind];
  const panelVehicle = document.getElementById("modal-fields-vehicle");
  const panelSpec = document.getElementById("modal-fields-spec");

  document.getElementById("modal-price-preview").style.display = "none";

  if (spec) {
    document.getElementById("modal-title").innerText = spec.title;
    document.getElementById("modal-desc").innerText = spec.description;
    panelVehicle.style.display = "none";
    panelSpec.style.display = "block";
    spec.groups.forEach((group, i) => {
      document.getElementById(`label-spec-${i}`).innerText = group.label;
      const hints = {};
      Object.entries(group.options).forEach(([key, opt]) => { hints[key] = opt.hint; });
      fillSelect(document.getElementById(`select-spec-${i}`), group.placeholder, hints);
    });
  } else {
    document.getElementById("modal-title").innerText = "Select Your Vehicle";
    document.getElementById("modal-desc").innerText = "Select your car make and model to match the exact compatible part for your vehicle.";
    panelVehicle.style.display = "block";
    panelSpec.style.display = "none";
    document.getElementById("select-make").value = "";
    const selectModel = document.getElementById("select-model");
    fillSelect(selectModel, "-- Choose Model --", {});
    selectModel.disabled = true;
  }

  vehicleModal.classList.add("is-open");
  vehicleModal.setAttribute("aria-hidden", "false");
  (spec ? document.getElementById("select-spec-0") : document.getElementById("select-make")).focus();
}

function closeSelectionModal() {
  const vehicleModal = document.getElementById("vehicle-modal");
  if (!vehicleModal) return;
  vehicleModal.classList.remove("is-open");
  vehicleModal.setAttribute("aria-hidden", "true");
}

// Returns {options, name, price} for the current modal selection, or {error} if incomplete.
// Must stay in sync with catalog.resolve_variant on the backend (which has the final say).
function currentSelection() {
  const base = selectedBaseProduct;
  const spec = CATALOG.specKinds[base.kind];

  if (spec) {
    const [first, second] = spec.groups.map((group, i) => {
      const key = document.getElementById(`select-spec-${i}`).value;
      return key ? { key, ...group.options[key] } : null;
    });
    if (!first || !second) {
      return { error: `Please select both ${spec.groups[0].label} and ${spec.groups[1].label}!` };
    }
    return {
      options: { first: first.key, second: second.key },
      name: `${base.name} - ${first.label} / ${second.label}`,
      price: base.price + first.modifier + second.modifier
    };
  }

  const make = document.getElementById("select-make").value;
  const model = document.getElementById("select-model").value;
  if (!make || !model) {
    return { error: "Please select both Make and Model!" };
  }
  return {
    options: { make, model },
    name: `${make} ${model} ${base.name}`,
    price: base.price + (CATALOG.makeModifiers[make] || 0)
  };
}

function addSelectionToCart(base, selection) {
  const optionKey = Object.values(selection.options).join("|");
  addToCart({
    id: optionKey ? `${base.id}:${optionKey}` : base.id,
    product_id: base.id,
    options: selection.options,
    image: base.image,
    name: selection.name,
    price: selection.price
  });
  openCartDrawer();
}

function updatePricePreview() {
  const previewDiv = document.getElementById("modal-price-preview");
  if (!previewDiv || !selectedBaseProduct) return;

  const selection = currentSelection();
  if (selection.error) {
    previewDiv.style.display = "none";
  } else {
    previewDiv.innerText = `Price: ${formatKSh(selection.price)}`;
    previewDiv.style.display = "block";
  }
}

// Populate Makes dropdown & bind modal events
function initVehicleModal() {
  const selectMake = document.getElementById("select-make");
  const selectModel = document.getElementById("select-model");
  const vehicleModal = document.getElementById("vehicle-modal");
  if (!selectMake || !vehicleModal) return;

  const makes = {};
  Object.keys(CATALOG.makes).forEach(make => { makes[make] = make; });
  fillSelect(selectMake, "-- Choose Make --", makes);

  selectMake.addEventListener("change", () => {
    const make = selectMake.value;
    const models = {};
    (CATALOG.makes[make] || []).forEach(model => { models[model] = model; });
    fillSelect(selectModel, "-- Choose Model --", models);
    selectModel.disabled = !make;
    updatePricePreview();
  });

  [selectModel, document.getElementById("select-spec-0"), document.getElementById("select-spec-1")]
    .forEach(el => el?.addEventListener("change", updatePricePreview));

  document.getElementById("close-vehicle-modal")?.addEventListener("click", closeSelectionModal);

  // Clicking the dimmed backdrop (outside the dialog) closes the modal
  vehicleModal.addEventListener("click", (e) => {
    if (e.target === vehicleModal) closeSelectionModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeSelectionModal();
  });

  document.getElementById("confirm-vehicle")?.addEventListener("click", () => {
    const selection = currentSelection();
    if (selection.error) {
      alert(selection.error);
      return;
    }
    closeSelectionModal();
    addSelectionToCart(selectedBaseProduct, selection);
  });

  // Catalog "Add To Cart" buttons open the modal (simple products go straight to the cart)
  document.querySelectorAll('[data-action="add-to-cart"]').forEach(button => {
    button.addEventListener("click", () => {
      const productDOM = button.closest(".product");
      const base = {
        id: button.getAttribute("data-product-id"),
        kind: button.getAttribute("data-kind") || "simple",
        image: productDOM.querySelector(".product-image").getAttribute("src"),
        name: productDOM.querySelector(".product-name").textContent.trim(),
        price: parseFloat(button.getAttribute("data-price")) || 0
      };
      if (base.kind === "simple") {
        addSelectionToCart(base, { options: {}, name: base.name, price: base.price });
      } else {
        openSelectionModal(base);
      }
    });
  });
}

// This script is loaded with `defer`, so the DOM is ready here
renderCart();
initVehicleModal();
