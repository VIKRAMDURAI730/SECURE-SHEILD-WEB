// API base URL - same origin when on port 5000 or when deployed (e.g. Render)
const API_BASE = (window.location.hostname === 'localhost' && window.location.port !== '5000')
  ? 'http://localhost:5000' : '';

// Auth: token + user in sessionStorage
const AUTH_KEY = 'purchase_auth';

function getAuth() {
  try {
    return JSON.parse(sessionStorage.getItem(AUTH_KEY) || 'null');
  } catch {
    return null;
  }
}

function setAuth(data) {
  sessionStorage.setItem(AUTH_KEY, JSON.stringify(data));
}

function clearAuth() {
  sessionStorage.removeItem(AUTH_KEY);
}

function getToken() {
  const a = getAuth();
  return a && a.token ? a.token : null;
}

function requireAuth() {
  const auth = getAuth();
  if (!auth || !auth.token) {
    window.location.href = 'index.html';
    return null;
  }
  return auth.user;
}

// Map HTTP status to user-friendly messages
function getStatusMessage(status) {
  const map = {
    400: 'Invalid request. Please check your input.',
    401: 'Session expired. Please sign in again.',
    403: 'Access denied.',
    404: 'Resource not found.',
    500: 'Server error. Please try again later.',
    502: 'Server temporarily unavailable.',
    503: 'Service unavailable. Please try again later.'
  };
  return map[status] || 'Something went wrong. Please try again.';
}

// API request helper
async function apiRequest(url, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };
  if (token) headers['Authorization'] = 'Bearer ' + token;
  let res;
  try {
    res = await fetch(API_BASE + url, { ...options, headers });
  } catch (err) {
    throw new Error('Connection failed. Is the server running? Check your network.');
  }
  let data = {};
  try {
    const text = await res.text();
    data = text ? JSON.parse(text) : {};
  } catch {
    data = {};
  }
  if (!res.ok) {
    const msg = (data && data.message) || getStatusMessage(res.status);
    throw new Error(msg);
  }
  return data;
}

// Login via API
async function login(email, password) {
  const e = (email || '').trim().toLowerCase();
  const p = (password || '').trim();
  if (!e || !p) return { ok: false, message: 'Please enter email and password.' };
  try {
    const data = await apiRequest('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email: e, password: p })
    });
    if (data.ok && data.token && data.user) {
      setAuth({ token: data.token, user: data.user });
      return { ok: true };
    }
    return { ok: false, message: data.message || 'Login failed' };
  } catch (err) {
    return { ok: false, message: err.message || 'Connection error. Is the server running?' };
  }
}

// Register via API
async function register(email, password, name) {
  const e = (email || '').trim().toLowerCase();
  const p = (password || '').trim();
  const n = (name || '').trim() || e.split('@')[0];
  if (!e || !p) return { ok: false, message: 'Please enter email and password.' };
  if (p.length < 4) return { ok: false, message: 'Password must be at least 4 characters.' };
  try {
    const data = await apiRequest('/api/register', {
      method: 'POST',
      body: JSON.stringify({ email: e, password: p, name: n })
    });
    if (data.ok && data.token && data.user) {
      setAuth({ token: data.token, user: data.user });
      return { ok: true };
    }
    return { ok: false, message: data.message || 'Registration failed' };
  } catch (err) {
    return { ok: false, message: err.message || 'Connection error. Is the server running?' };
  }
}

// Cart: stored in localStorage (client-side)
const CART_KEY = 'purchase_cart';

function getCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY) || '[]');
  } catch {
    return [];
  }
}

function setCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateCartCount();
}

function addToCart(product, quantity = 1) {
  const cart = getCart();
  const existing = cart.find(i => String(i.id) === String(product.id));
  if (existing) {
    existing.quantity = (existing.quantity || 1) + quantity;
  } else {
    cart.push({
      id: product.id,
      product_id: product.id,
      name: product.name,
      price: product.price,
      image: product.image,
      quantity: quantity
    });
  }
  setCart(cart);
}

function removeFromCart(productId) {
  setCart(getCart().filter(i => String(i.id) !== String(productId)));
}

function setCartItemQuantity(productId, quantity) {
  if (quantity < 1) {
    removeFromCart(productId);
    return;
  }
  const cart = getCart();
  const item = cart.find(i => String(i.id) === String(productId));
  if (item) {
    item.quantity = quantity;
    setCart(cart);
  }
}

function getCartTotal() {
  return getCart().reduce((sum, i) => sum + i.price * (i.quantity || 1), 0);
}

function updateCartCount() {
  const el = document.getElementById('cart-count');
  if (!el) return;
  const total = getCart().reduce((n, i) => n + (i.quantity || 1), 0);
  el.textContent = total;
  el.style.display = total ? 'flex' : 'none';
}

// Fetch products from API
async function fetchProducts() {
  const data = await apiRequest('/api/products');
  return Array.isArray(data) ? data : [];
}

function getProductById(id, products) {
  if (products && products.length) {
    return products.find(p => String(p.id) === String(id));
  }
  return null;
}

// Place order via API
async function placeOrder(items, shippingName, shippingAddress) {
  const payload = {
    items: items.map(i => ({ product_id: i.id, quantity: i.quantity || 1 })),
    shipping_name: shippingName,
    shipping_address: shippingAddress
  };
  return apiRequest('/api/orders', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

async function fetchOrder(orderId) {
  return apiRequest('/api/orders/' + encodeURIComponent(orderId));
}

// Redirect to login if not authenticated
function initProtectedPage() {
  const user = requireAuth();
  if (!user) return;
  updateCartCount();
  return user;
}

function formatPrice(n) {
  return '$' + Number(n).toFixed(2);
}

// XSS prevention: escape HTML when inserting user data into innerHTML
function escapeHtml(str) {
  if (str == null) return '';
  const s = String(str);
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
