// Cart implementation using localStorage
let cart = JSON.parse(localStorage.getItem("cart")) || [];
const cartDOM = document.querySelector(".cart");
const addToCartButtonsDOM = document.querySelectorAll('[data-action="add-to-cart"]');

function formatPrice(priceStr){
  // remove $ and parse to float
  return parseFloat(priceStr.replace(/[^0-9.\.]/g, '')) || 0;
}

const MAKES_AND_MODELS = {
  "Toyota": ["Vitz", "Fielder", "Corolla", "Harrier", "Land Cruiser", "Probox"],
  "Nissan": ["X-Trail", "Note", "Sylphy", "Wingroad"],
  "Subaru": ["Impreza", "Forester", "Legacy"],
  "Honda": ["Fit", "Civic", "CR-V"],
  "Mazda": ["Demio", "Axela", "CX-5"],
  "Mitsubishi": ["Outlander", "Lancer", "Pajero"],
  "Volkswagen": ["Golf", "Tiguan", "Polo", "Passat"],
  "Mercedes-Benz": ["C-Class", "E-Class", "GLC"],
  "BMW": ["3 Series", "5 Series", "X3", "X5"],
  "Hyundai": ["Tucson", "Elantra", "Santa Fe"]
};

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

// Set up the generic catalog add-to-cart triggers
addToCartButtonsDOM.forEach(addToCartButtonDOM => {
  addToCartButtonDOM.addEventListener("click", () => {
    const productDOM = addToCartButtonDOM.parentNode;
    const productId = addToCartButtonDOM.getAttribute('data-product-id') || null;
    
    selectedBaseProduct = {
      button: addToCartButtonDOM,
      id: productId,
      image: productDOM.querySelector(".product-image").getAttribute("src"),
      name: productDOM.querySelector(".product-name").innerText,
      price: formatPrice(productDOM.querySelector(".product-price").innerText)
    };

    // Open vehicle selector modal
    const vehicleModal = document.getElementById("vehicle-modal");
    if (vehicleModal) {
      vehicleModal.classList.add("is-open");
      vehicleModal.setAttribute("aria-hidden", "false");
      
      // Reset dropdowns
      const selectMake = document.getElementById("select-make");
      const selectModel = document.getElementById("select-model");
      const previewDiv = document.getElementById("modal-price-preview");
      
      if (selectMake) selectMake.value = "";
      if (selectModel) {
        selectModel.value = "";
        selectModel.disabled = true;
      }
      if (previewDiv) previewDiv.style.display = "none";
    }
  });
});

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
        <input type="tel" id="checkout-phone" placeholder="e.g. 254712345678" value="2547" required>
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
    const phone = phoneInput.value.trim();
    const statusDiv = document.querySelector(".checkout-status");
    const payBtn = document.getElementById("trigger-stk-push");
    const cancelBtn = document.getElementById("cancel-checkout");
    
    if (!phone.match(/^2547\d{8}$/) && !phone.match(/^2541\d{8}$/)) {
      statusDiv.className = "checkout-status error";
      statusDiv.innerText = "Please enter a valid Safaricom number starting with 2547 or 2541 (12 digits total).";
      return;
    }
    
    payBtn.disabled = true;
    cancelBtn.disabled = true;
    payBtn.innerText = "Requesting STK Push...";
    statusDiv.className = "checkout-status";
    statusDiv.innerText = "Connecting to Safaricom Daraja API...";
    
    try {
      // Use the first item in the cart for checkout
      const response = await fetch("/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: phone,
          product_id: cart[0].id
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
  
  if (!selectMake) return; // not on catalog page

  // Clear and add placeholder
  selectMake.innerHTML = '<option value="">-- Choose Make --</option>';
  Object.keys(MAKES_AND_MODELS).forEach(make => {
    const opt = document.createElement("option");
    opt.value = make;
    opt.innerText = make;
    selectMake.appendChild(opt);
  });

  selectMake.addEventListener("change", () => {
    const make = selectMake.value;
    selectModel.innerHTML = '<option value="">-- Choose Model --</option>';
    if (make) {
      selectModel.disabled = false;
      MAKES_AND_MODELS[make].forEach(model => {
        const opt = document.createElement("option");
        opt.value = model;
        opt.innerText = model;
        selectModel.appendChild(opt);
      });
    } else {
      selectModel.disabled = true;
    }
    updatePricePreview();
  });

  selectModel.addEventListener("change", updatePricePreview);

  closeBtn?.addEventListener("click", () => {
    vehicleModal.classList.remove("is-open");
    vehicleModal.setAttribute("aria-hidden", "true");
  });

  confirmBtn?.addEventListener("click", () => {
    const make = selectMake.value;
    const model = selectModel.value;
    if (!make || !model) {
      alert("Please select both Make and Model!");
      return;
    }

    // Generate specific ID
    const specId = `${selectedBaseProduct.id}_${make.toLowerCase()}_${model.toLowerCase().replace(/ /g, '_').replace(/-/g, '_')}`;
    const specName = `${make} ${model} ${selectedBaseProduct.name}`;
    
    // Calculate price modifier
    let priceModifier = 0;
    if (make === "Mercedes-Benz" || make === "BMW") {
      priceModifier = 2500;
    } else if (make === "Toyota" || make === "Subaru") {
      priceModifier = 400;
    } else if (make === "Nissan" || make === "Mazda") {
      priceModifier = -200;
    }
    const specPrice = selectedBaseProduct.price + priceModifier;

    const product = {
      id: specId,
      image: selectedBaseProduct.image,
      name: specName,
      price: specPrice,
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
  const selectMake = document.getElementById("select-make");
  const selectModel = document.getElementById("select-model");
  const previewDiv = document.getElementById("modal-price-preview");
  if (!selectMake || !previewDiv) return;

  const make = selectMake.value;
  const model = selectModel.value;
  if (make && model && selectedBaseProduct) {
    let priceModifier = 0;
    if (make === "Mercedes-Benz" || make === "BMW") {
      priceModifier = 2500;
    } else if (make === "Toyota" || make === "Subaru") {
      priceModifier = 400;
    } else if (make === "Nissan" || make === "Mazda") {
      priceModifier = -200;
    }
    const finalPrice = selectedBaseProduct.price + priceModifier;
    previewDiv.innerText = `Price: KSh ${finalPrice.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    previewDiv.style.display = "block";
  } else {
    previewDiv.style.display = "none";
  }
}

// Initialize when loaded
document.addEventListener('DOMContentLoaded', function(){
  renderInitialCart();
  countCartTotal();
  initVehicleModal();
});
