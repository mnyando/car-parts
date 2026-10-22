// Cart implementation using localStorage
let cart = JSON.parse(localStorage.getItem("cart")) || [];
const cartDOM = document.querySelector(".cart");
const addToCartButtonsDOM = document.querySelectorAll('[data-action="add-to-cart"]');

// Catalog data (makes, price modifiers, spec options) is served by the backend
// in base.html, so prices here always match what /checkout charges.
const CATALOG = window.CATALOG || { makes: {}, makeModifiers: {}, specProducts: {} };

let selectedBaseProduct = null;

function renderInitialCart(){
  if (cart.length > 0) {
    cart.forEach(cartItem => {
      insertItemToDOM(cartItem);
      countCartTotal();
      wireCartItemListeners(cartItem);
    });
  }
}

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

  const spec = CATALOG.specProducts[baseProduct.id];
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
}

// Set up the generic catalog add-to-cart triggers
addToCartButtonsDOM.forEach(addToCartButtonDOM => {
  addToCartButtonDOM.addEventListener("click", () => {
    const productDOM = addToCartButtonDOM.parentNode;
    openSelectionModal({
      id: addToCartButtonDOM.getAttribute('data-product-id'),
      image: productDOM.querySelector(".product-image").getAttribute("src"),
      name: productDOM.querySelector(".product-name").innerText,
      price: parseFloat(addToCartButtonDOM.getAttribute('data-price')) || 0
    });
  });
});

// Returns {id, name, price} for the current modal selection, or {error} if incomplete.
function currentSelection() {
  const base = selectedBaseProduct;
  const spec = CATALOG.specProducts[base.id];

  if (spec) {
    const [first, second] = spec.groups.map((group, i) => {
      const key = document.getElementById(`select-spec-${i}`).value;
      return key ? { key, ...group.options[key] } : null;
    });
    if (!first || !second) {
      return { error: `Please select both ${spec.groups[0].label} and ${spec.groups[1].label}!` };
    }
    return {
      id: `${base.id}_${first.key}_${second.key}`,
      name: spec.name_format.replace("{first}", first.label).replace("{second}", second.label),
      price: base.price + first.modifier + second.modifier
    };
  }

  const make = document.getElementById("select-make").value;
  const model = document.getElementById("select-model").value;
  if (!make || !model) {
    return { error: "Please select both Make and Model!" };
  }
  // Must match catalog.vehicle_product_id on the backend
  return {
    id: `${base.id}_${make.toLowerCase()}_${model.toLowerCase().replace(/ /g, '_').replace(/-/g, '_')}`,
    name: `${make} ${model} ${base.name}`,
    price: base.price + (CATALOG.makeModifiers[make] || 0)
  };
}

function insertItemToDOM(product) {
  if (!cartDOM) return; // catalog page won't have cartDOM
  cartDOM.insertAdjacentHTML(
    "beforeend",
    `
    <div class="cart-item">
        <img class="cart-item-image" src="${product.image}" alt="${product.name}" loading="lazy" decoding="async" />
        <!-- store product id on the DOM for later reference -->
        <input type="hidden" class="cart-item-id" value="${product.id || ''}" />
        <h2 class="cart-item-name">${product.name}</h2>
        <h3 class="cart-item-price">${product.price.toFixed(2)}</h3>
        <button class="btn btn-primary btn-small" data-action="decrease-item">&minus;</button>
        <h3 class="cart-item-quantity">${product.quantity}</h3>
        <button class="btn btn-primary btn-small" data-action="increase-item">&plus;</button>
        <button class="btn btn-primary btn-small" data-action="remove-item">&times;</button>
    </div>
    `
  );

  addCartFooter();
}

function wireCartItemListeners(product) {
  const cartItemsDOM = document.querySelectorAll(".cart-item");
  cartItemsDOM.forEach(cartItemDOM => {
    const domIdInput = cartItemDOM.querySelector('.cart-item-id');
    const domId = domIdInput ? domIdInput.value : null;
    if (domId && domId === product.id) {
      const incBtn = cartItemDOM.querySelector('[data-action="increase-item"]');
      const decBtn = cartItemDOM.querySelector('[data-action="decrease-item"]');
      const remBtn = cartItemDOM.querySelector('[data-action="remove-item"]');
      
      incBtn?.addEventListener("click", () => increaseItem(product, cartItemDOM));
      decBtn?.addEventListener("click", () => decreaseItem(product, cartItemDOM, null));
      remBtn?.addEventListener("click", () => removeItem(product, cartItemDOM, null));
    }
  });
}

function increaseItem(product, cartItemDOM) {
  cart.forEach(cartItem => {
    if ((product.id && cartItem.id === product.id) || (!product.id && cartItem.name === product.name)) {
      cartItemDOM.querySelector(".cart-item-quantity").innerText = ++cartItem.quantity;
      saveCart();
    }
  });
}

function decreaseItem(product, cartItemDOM, addToCartButtonDOM) {
  cart.forEach(cartItem => {
    if ((product.id && cartItem.id === product.id) || (!product.id && cartItem.name === product.name)) {
      if (cartItem.quantity > 1) {
        cartItemDOM.querySelector(".cart-item-quantity").innerText = --cartItem.quantity;
        saveCart();
      } else {
        removeItem(product, cartItemDOM, addToCartButtonDOM);
      }
    }
  });
}

function removeItem(product, cartItemDOM, addToCartButtonDOM) {
  cartItemDOM.remove();
  // remove by id if available, otherwise fallback to name
  if (product.id) {
    cart = cart.filter(cartItem => cartItem.id !== product.id);
  } else {
    cart = cart.filter(cartItem => cartItem.name !== product.name);
  }
  saveCart();
  if (addToCartButtonDOM) {
    addToCartButtonDOM.innerText = "Add To Cart";
    addToCartButtonDOM.disabled = false;
  }

  if (cart.length < 1 && document.querySelector(".cart-footer")) {
    document.querySelector(".cart-footer").remove();
  }
}

function addCartFooter() {
  if (document.querySelector(".cart-footer") === null && cartDOM) {
    cartDOM.insertAdjacentHTML(
      "afterend",
      `
        <div class="cart-footer">
          <h2 class="cart-footer-total" data-action="total-price">0</h2>
          <button class="btn btn-primary btn-small btn-danger" data-action="clear-cart">Clear Cart</button>
          <button class="btn btn-primary btn-small btn-danger" id="checkout">Checkout</button>
        </div>
        `
    );

    document.querySelector('[data-action="clear-cart"]').addEventListener("click", () => clearCart());
    document.querySelector('#checkout').addEventListener("click", () => checkout());
  }
}

function clearCart() {
  if (cartDOM) {
    cartDOM.querySelectorAll(".cart-item").forEach(cartItemDOM => { cartItemDOM.remove(); });
  }
  cart = [];
  localStorage.removeItem("cart");
  if (document.querySelector(".cart-footer")) document.querySelector(".cart-footer").remove();
  addToCartButtonsDOM.forEach(addToCartButtonDOM => { addToCartButtonDOM.innerText = "Add To Cart"; addToCartButtonDOM.disabled = false; });
}

function countCartTotal() {
  let cartTotal = 0;
  let itemCount = 0;
  cart.forEach(cartItem => {
    cartTotal += cartItem.quantity * parseFloat(cartItem.price);
    itemCount += cartItem.quantity;
  });
  if (document.querySelector('[data-action="total-price"]')) {
    document.querySelector('[data-action="total-price"]').innerText = `${cartTotal.toFixed(2)}`;
  }
  const cartCountDOM = document.querySelector('[data-cart-count]');
  if (cartCountDOM) {
    cartCountDOM.innerText = itemCount;
  }
}

function checkout(){
  if (cart.length === 0) {
    alert("Your cart is empty!");
    return;
  }
  
  // Find cart container in DOM
  const container = document.querySelector(".cart");
  if (!container) {
    alert("Cart container not found!");
    return;
  }
  
  // Hide the standard cart footer temporarily
  const footer = document.querySelector(".cart-footer");
  if (footer) footer.style.display = "none";
  
  // Hide current cart items
  const items = container.querySelectorAll(".cart-item");
  items.forEach(el => el.style.display = "none");
  
  // Render M-Pesa checkout form inline
  container.insertAdjacentHTML(
    "beforeend",
    `
    <div class="checkout-form-container">
      <div class="field">
        <label for="checkout-phone">M-Pesa Phone Number</label>
        <input type="tel" id="checkout-phone" placeholder="e.g. 0712345678" required>
      </div>
      <button class="btn btn-primary" id="trigger-stk-push" style="width:100%; margin-top: 10px;">Pay with M-Pesa</button>
      <button class="btn btn-secondary" id="cancel-checkout" style="background: none; border: 1px solid var(--line-strong); color: var(--ink); width: 100%; padding: 12px; margin-top: 8px;">Back to Cart</button>
      <div class="checkout-status"></div>
    </div>
    `
  );
  
  // Handle Back to Cart
  document.getElementById("cancel-checkout").addEventListener("click", () => {
    document.querySelector(".checkout-form-container").remove();
    items.forEach(el => el.style.display = "grid");
    if (footer) footer.style.display = "flex";
  });
  
  // Handle STK Push trigger
  document.getElementById("trigger-stk-push").addEventListener("click", async () => {
    const phoneInput = document.getElementById("checkout-phone");
    const phone = phoneInput.value.replace(/[\s\-()]/g, "");
    const statusDiv = document.querySelector(".checkout-status");
    const payBtn = document.getElementById("trigger-stk-push");
    const cancelBtn = document.getElementById("cancel-checkout");
    
    // Accepts 07XXXXXXXX, 01XXXXXXXX, 2547XXXXXXXX, +2547XXXXXXXX (server normalizes)
    if (!phone.match(/^(\+?254|0)?[17]\d{8}$/)) {
      statusDiv.className = "checkout-status error";
      statusDiv.innerText = "Please enter a valid Safaricom number, e.g. 0712345678 or 254712345678.";
      return;
    }
    
    payBtn.disabled = true;
    cancelBtn.disabled = true;
    payBtn.innerText = "Requesting STK Push...";
    statusDiv.className = "checkout-status";
    statusDiv.innerText = "Connecting to Safaricom Daraja API...";
    
    try {
      // Send every cart line; the server re-prices them from the catalog
      const response = await fetch("/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: phone,
          items: cart.map(item => ({ id: item.id, quantity: item.quantity }))
        })
      });
      
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "Failed to trigger checkout");
      }
      
      statusDiv.className = "checkout-status success";
      statusDiv.innerText = "STK Push initiated! Please enter your M-Pesa PIN on your phone to complete the transaction.";
      
      // Clear cart
      setTimeout(() => {
        cart = [];
        localStorage.removeItem("cart");
        location.href = '/';
      }, 5000);
      
    } catch (err) {
      payBtn.disabled = false;
      cancelBtn.disabled = false;
      payBtn.innerText = "Pay with M-Pesa";
      statusDiv.className = "checkout-status error";
      statusDiv.innerText = "Error: " + err.message;
    }
  });
}

function saveCart() {
  localStorage.setItem("cart", JSON.stringify(cart));
  countCartTotal();
}

// Populate Makes dropdown on load & bind modal events
function initVehicleModal() {
  const selectMake = document.getElementById("select-make");
  const selectModel = document.getElementById("select-model");
  const closeBtn = document.getElementById("close-vehicle-modal");
  const confirmBtn = document.getElementById("confirm-vehicle");
  const vehicleModal = document.getElementById("vehicle-modal");

  if (!selectMake) return;

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

  closeBtn?.addEventListener("click", () => {
    vehicleModal.classList.remove("is-open");
    vehicleModal.setAttribute("aria-hidden", "true");
  });

  confirmBtn?.addEventListener("click", () => {
    const selection = currentSelection();
    if (selection.error) {
      alert(selection.error);
      return;
    }

    const product = {
      id: selection.id,
      image: selectedBaseProduct.image,
      name: selection.name,
      price: selection.price,
      quantity: 1
    };

    // Add to cart
    const existingIndex = cart.findIndex(ci => ci.id === product.id);
    if (existingIndex !== -1) {
      cart[existingIndex].quantity += 1;
      const cartItemsDOM = document.querySelectorAll(".cart-item");
      cartItemsDOM.forEach(cartItemDOM => {
        const idInput = cartItemDOM.querySelector('.cart-item-id');
        if (idInput && idInput.value === product.id) {
          cartItemDOM.querySelector('.cart-item-quantity').innerText = cart[existingIndex].quantity;
        }
      });
      saveCart();
    } else {
      insertItemToDOM(product);
      cart.push(product);
      saveCart();
      wireCartItemListeners(product);
    }

    // Close modal & open cart drawer
    vehicleModal.classList.remove("is-open");
    vehicleModal.setAttribute("aria-hidden", "true");
    document.querySelector(".cart-drawer")?.classList.add("is-open");
  });
}

function updatePricePreview() {
  const previewDiv = document.getElementById("modal-price-preview");
  if (!previewDiv || !selectedBaseProduct) return;

  const selection = currentSelection();
  if (selection.error) {
    previewDiv.style.display = "none";
  } else {
    previewDiv.innerText = `Price: KSh ${selection.price.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    previewDiv.style.display = "block";
  }
}

// Initialize when loaded
document.addEventListener('DOMContentLoaded', function(){
  renderInitialCart();
  countCartTotal();
  initVehicleModal();
});
