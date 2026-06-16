// Cart implementation using localStorage
let cart = JSON.parse(localStorage.getItem("cart")) || [];
const cartDOM = document.querySelector(".cart");
const addToCartButtonsDOM = document.querySelectorAll('[data-action="add-to-cart"]');

function formatPrice(priceStr){
  // remove $ and parse to float
  return parseFloat(priceStr.replace(/[^0-9.\.]/g, '')) || 0;
}

function renderInitialCart(){
  if (cart.length > 0) {
    cart.forEach(cartItem => {
      insertItemToDOM(cartItem);
      countCartTotal();
      // mark buttons as in-cart
      addToCartButtonsDOM.forEach(addToCartButtonDOM => {
        const pid = addToCartButtonDOM.getAttribute('data-product-id');
        // prefer id matching, fallback to name matching for older stored carts
        if ((cartItem.id && pid && cartItem.id === pid) || (!cartItem.id && productMatchesByName(addToCartButtonDOM, cartItem.name))) {
          handleActionButtons(addToCartButtonDOM, cartItem);
        }
      });
    });
  }
}

addToCartButtonsDOM.forEach(addToCartButtonDOM => {
  addToCartButtonDOM.addEventListener("click", () => {
    const productDOM = addToCartButtonDOM.parentNode;
    const productId = addToCartButtonDOM.getAttribute('data-product-id') || null;
    const product = {
      id: productId,
      image: productDOM.querySelector(".product-image").getAttribute("src"),
      name: productDOM.querySelector(".product-name").innerText,
      price: formatPrice(productDOM.querySelector(".product-price").innerText),
      quantity: 1
    };

    // prefer id-based matching; fallback to name
    const isInCart = product.id ? cart.some(ci => ci.id === product.id) : cart.some(ci => ci.name === product.name);

    if (!isInCart) {
      insertItemToDOM(product);
      cart.push(product);
      saveCart();
      handleActionButtons(addToCartButtonDOM, product);
    }
  });
});

function insertItemToDOM(product) {
  if (!cartDOM) return; // catalog page won't have cartDOM
  cartDOM.insertAdjacentHTML(
    "beforeend",
    `
    <div class="cart-item">
        <img class="cart-item-image" src="${product.image}" alt="${product.name}" />
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

function handleActionButtons(addToCartButtonDOM, product) {
  addToCartButtonDOM.innerText = "In Cart";
  addToCartButtonDOM.disabled = true;

  const cartItemsDOM = document.querySelectorAll(".cart-item");
  cartItemsDOM.forEach(cartItemDOM => {
    // match by hidden id first, fallback to name
    const domIdInput = cartItemDOM.querySelector('.cart-item-id');
    const domId = domIdInput ? domIdInput.value : null;
    const domName = cartItemDOM.querySelector('.cart-item-name').innerText;
    const matches = (product.id && domId && product.id === domId) || (!product.id && domName === product.name) || (product.name === domName);
    if (matches) {
      cartItemDOM.querySelector('[data-action="increase-item"]').addEventListener("click", () => increaseItem(product, cartItemDOM));
      cartItemDOM.querySelector('[data-action="decrease-item"]').addEventListener("click", () => decreaseItem(product, cartItemDOM, addToCartButtonDOM));
      cartItemDOM.querySelector('[data-action="remove-item"]').addEventListener("click", () => removeItem(product, cartItemDOM, addToCartButtonDOM));
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
  cart.forEach(cartItem => (cartTotal += cartItem.quantity * parseFloat(cartItem.price)));
  if (document.querySelector('[data-action="total-price"]')) {
    document.querySelector('[data-action="total-price"]').innerText = `${cartTotal.toFixed(2)}`;
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

// Initialize when loaded
document.addEventListener('DOMContentLoaded', function(){
  renderInitialCart();
  countCartTotal();
});
