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
        const productDOM = addToCartButtonDOM.parentNode;
        if (productDOM.querySelector(".product-name").innerText === cartItem.name) {
          handleActionButtons(addToCartButtonDOM, cartItem);
        }
      });
    });
  }
}

addToCartButtonsDOM.forEach(addToCartButtonDOM => {
  addToCartButtonDOM.addEventListener("click", () => {
    const productDOM = addToCartButtonDOM.parentNode;
    const product = {
      image: productDOM.querySelector(".product-image").getAttribute("src"),
      name: productDOM.querySelector(".product-name").innerText,
      price: formatPrice(productDOM.querySelector(".product-price").innerText),
      quantity: 1
    };

    const isInCart = cart.filter(cartItem => cartItem.name === product.name).length > 0;

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
    if (cartItemDOM.querySelector(".cart-item-name").innerText === product.name) {
      cartItemDOM.querySelector('[data-action="increase-item"]').addEventListener("click", () => increaseItem(product, cartItemDOM));
      cartItemDOM.querySelector('[data-action="decrease-item"]').addEventListener("click", () => decreaseItem(product, cartItemDOM, addToCartButtonDOM));
      cartItemDOM.querySelector('[data-action="remove-item"]').addEventListener("click", () => removeItem(product, cartItemDOM, addToCartButtonDOM));
    }
  });
}

function increaseItem(product, cartItemDOM) {
  cart.forEach(cartItem => {
    if (cartItem.name === product.name) {
      cartItemDOM.querySelector(".cart-item-quantity").innerText = ++cartItem.quantity;
      saveCart();
    }
  });
}

function decreaseItem(product, cartItemDOM, addToCartButtonDOM) {
  cart.forEach(cartItem => {
    if (cartItem.name === product.name) {
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
  cart = cart.filter(cartItem => cartItem.name !== product.name);
  saveCart();
  if (addToCartButtonDOM) {
    addToCartButtonDOM.innerText = "Add to Cart";
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
  alert("Thank you for shopping with us, Welcome again");
  cart = [];
  localStorage.removeItem("cart");
  location.href = "{{ url_for('index') }}";
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
