const { useState, useEffect, useRef } = React;

// ---------------------------------------------------------------------------
// Icons (hand-rolled inline SVG, no icon package - keeps this dependency-free)
// ---------------------------------------------------------------------------

const ICON_PATHS = {
  dashboard: <><rect x="3" y="3" width="7" height="9" rx="1" /><rect x="14" y="3" width="7" height="5" rx="1" /><rect x="14" y="12" width="7" height="9" rx="1" /><rect x="3" y="16" width="7" height="5" rx="1" /></>,
  trendingUp: <><polyline points="3 17 9 11 13 15 21 6" /><polyline points="14 6 21 6 21 13" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 15 14" /></>,
  package: <><path d="M21 8l-9-5-9 5v8l9 5 9-5V8z" /><polyline points="3.3 7 12 12 20.7 7" /><line x1="12" y1="22" x2="12" y2="12" /></>,
  dollar: <><line x1="12" y1="2" x2="12" y2="22" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></>,
  percent: <><line x1="19" y1="5" x2="5" y2="19" /><circle cx="6.5" cy="6.5" r="2.5" /><circle cx="17.5" cy="17.5" r="2.5" /></>,
  timer: <><line x1="10" y1="2" x2="14" y2="2" /><line x1="12" y1="14" x2="12" y2="9" /><circle cx="12" cy="14" r="8" /></>,
  arrowRight: <><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></>,
  arrowLeft: <><line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" /></>,
  checkCircle: <><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></>,
  xCircle: <><circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" /></>,
  alertTriangle: <><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></>,
  info: <><circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" /></>,
  dot: <circle cx="12" cy="12" r="4" fill="currentColor" stroke="none" />,
  award: <><circle cx="12" cy="8" r="6" /><path d="M8.21 13.89L7 23l5-3 5 3-1.21-9.12" /></>,
  calendar: <><rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></>,
  // --- added for the chatbot widget ---
  message: <><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></>,
  send: <><line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></>,
  close: <><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></>,
  moreVertical: <><circle cx="12" cy="5" r="1.5" fill="currentColor" stroke="none" /><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" /><circle cx="12" cy="19" r="1.5" fill="currentColor" stroke="none" /></>,
  copy: <><rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" /></>,
  trash: <><polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" /><line x1="10" y1="11" x2="10" y2="17" /><line x1="14" y1="11" x2="14" y2="17" /></>,
  printer: <><polyline points="6 9 6 2 18 2 18 9" /><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" /><rect x="6" y="14" width="12" height="8" /></>,
  // --- added for the blog page ---
  newspaper: <><path d="M4 4h13a1 1 0 0 1 1 1v14a2 2 0 0 0 2-2V8h-3" /><path d="M18 19H5a2 2 0 0 1-2-2V4" /><line x1="7" y1="8" x2="14" y2="8" /><line x1="7" y1="12" x2="14" y2="12" /><line x1="7" y1="16" x2="11" y2="16" /></>,
  externalLink: <><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" /></>,
  image: <><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" /></>,
  // --- added for the login screen ---
  user: <><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></>,
  lock: <><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></>,
  logOut: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></>,
  mail: <><path d="M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" /><polyline points="22 6 12 13 2 6" /></>,
  // --- added for the market scraper page ---
  globe: <><circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></>,
  database: <><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" /></>,
  activity: <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />,
};

function Icon({ name, size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {ICON_PATHS[name]}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Auth storage (localStorage - survives refresh and new tabs, unlike
// sessionStorage) + a JWT payload decode so we can read the logged-in
// user's email out of the token without another round trip. This is a
// read-only decode for display/request purposes - the server is what
// actually verifies the signature on every protected call.
// ---------------------------------------------------------------------------

const AUTH_STORAGE_KEY = 'usgroup_auth'; // { token, name, role, email }

function getStoredAuth() {
  try {
    return JSON.parse(localStorage.getItem(AUTH_STORAGE_KEY));
  } catch {
    return null;
  }
}

function setStoredAuth(auth) {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth));
}

function clearStoredAuth() {
  localStorage.removeItem(AUTH_STORAGE_KEY);
}

function decodeJwtPayload(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const json = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + c.charCodeAt(0).toString(16).padStart(2, '0'))
        .join('')
    );
    return JSON.parse(json);
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// API client (same origin - FastAPI serves this frontend, so relative paths)
// ---------------------------------------------------------------------------

// For everything AFTER login: attaches the stored token as a Bearer header
// automatically, and on a 401 (missing/expired/invalid token) clears the
// stored auth and reloads, which drops the app back to the login screen.
async function apiRequest(path, options) {
  const auth = getStoredAuth();
  const headers = { 'Content-Type': 'application/json' };
  if (auth && auth.token) headers.Authorization = `Bearer ${auth.token}`;

  const res = await fetch(path, { ...options, headers });

  if (res.status === 401) {
    clearStoredAuth();
    window.location.reload();
    throw new Error('Session expired. Please log in again.');
  }

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (Array.isArray(body.detail)) message = body.detail.map((d) => d.msg).join('; ');
      else if (typeof body.detail === 'string') message = body.detail;
    } catch {
      // response wasn't JSON - keep the generic message
    }
    throw new Error(message);
  }
  return res.json();
}

// For signup/verify-otp/login only - no token exists yet, and a 401 here
// (e.g. wrong password) is a normal form error, not an expired session.
async function publicApiRequest(path, options) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (Array.isArray(body.detail)) message = body.detail.map((d) => d.msg).join('; ');
      else if (typeof body.detail === 'string') message = body.detail;
    } catch {
      // response wasn't JSON - keep the generic message
    }
    throw new Error(message);
  }
  return res.json();
}

const signupRequest = (name, email, password) =>
  publicApiRequest('/auth/signup', { method: 'POST', body: JSON.stringify({ name, email, password }) });
const verifyOtpRequest = (email, otp) =>
  publicApiRequest('/auth/verify-otp', { method: 'POST', body: JSON.stringify({ email, otp }) });
const loginRequest = (email, password) =>
  publicApiRequest('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
// public auth config (Google client id) for the login page, and the Google
// sign-in exchange: send the GIS credential (ID token) and get back {token,...}
const fetchAuthConfig = () => publicApiRequest('/auth/config');
const googleAuthRequest = (credential) =>
  publicApiRequest('/auth/google', { method: 'POST', body: JSON.stringify({ credential }) });
// GET /auth/all-users and POST /auth/verify-password both require an admin
// Bearer token, which apiRequest already attaches automatically.
const fetchAllUsers = () => apiRequest('/auth/all-users');
const verifyPasswordRequest = (email, password) =>
  apiRequest('/auth/verify-password', { method: 'POST', body: JSON.stringify({ email, password }) });
const approveUserRequest = (id) => apiRequest(`/auth/approve/${id}`, { method: 'POST' });
// DELETE /auth/users/:id -> removes an account (rejects a pending request or
// deletes a created account). Admin accounts are refused by the backend.
const deleteUserRequest = (id) => apiRequest(`/auth/users/${id}`, { method: 'DELETE' });
// GET /audit-log/:id -> { user: {name, email, role, ...}, actions: [{action, details, created_at}] }
// step-by-step activity trail for one user, most recent first. Admin only.
const fetchAuditLog = (id) => apiRequest(`/audit-log/${id}`);
// POST /warnings/generate { user_id, actions } -> { letter } - LLM drafts a
// warning letter from the selected audit-log actions. Admin only.
const generateWarningLetter = (userId, actions) =>
  apiRequest('/warnings/generate', { method: 'POST', body: JSON.stringify({ user_id: userId, actions }) });
// POST /warnings/send { user_id, letter, send_email, actions } -> { id, emailed }
// Saves the (possibly admin-edited) letter and optionally emails it. Admin only.
const sendWarning = (userId, letter, sendEmailFlag, actions) =>
  apiRequest('/warnings/send', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, letter, send_email: sendEmailFlag, actions }),
  });
// GET /warnings/mine -> [{id, letter, emailed, created_at}] for the logged-in user
const fetchMyWarnings = () => apiRequest('/warnings/mine');
// GET /warnings/sent -> [{id, user_name, user_email, letter, emailed, created_at}]
// every warning issued, across all recipients. Admin only.
const fetchSentWarnings = () => apiRequest('/warnings/sent');

const fetchOptions = () => apiRequest('/options');
const fetchDashboardStats = () => apiRequest('/dashboard-stats');
const predictProfitability = (payload) =>
  apiRequest('/predict/profitability', { method: 'POST', body: JSON.stringify(payload) });
const predictPaymentDelay = (payload) =>
  apiRequest('/predict/payment-delay', { method: 'POST', body: JSON.stringify(payload) });
// --- added for the chatbot widget: calls the existing POST /chat endpoint
// (backend/main.py -> backend/chatbot/service.py:ask_chatbot), which returns
// { answer: string, sql: string|null, data: list|null }
// history: recent [{role, content}] turns, sent so the backend can resolve
// follow-up references like "show its picture" / "the most expensive one"
const askChatbot = (question, history) =>
  apiRequest('/chat', { method: 'POST', body: JSON.stringify({ question, history }) });
// GET /chat/history -> [{ id, question, answer, created_at }], most recent first, up to 50
const fetchChatHistory = () => apiRequest('/chat/history');
// DELETE /chat/history/:id -> removes a single past Q&A entry
const deleteChatHistoryItem = (id) => apiRequest(`/chat/history/${id}`, { method: 'DELETE' });
// POST /chat/chart { data } -> { image_base64 }. Renders whatever "data" rows
// a chat answer already returned into a chart image, generated on demand.
const fetchChatChart = (data) => apiRequest('/chat/chart', { method: 'POST', body: JSON.stringify({ data }) });
// POST /report/custom { items: [{ question, answer, chart_image_base64 }] } ->
// { pdf_base64 }. Builds a PDF from a hand-picked set of already-pinned
// charts - each item's answer gets rewritten into report prose server-side,
// so this takes a few seconds per selected chart.
const generateCustomReport = (items) => apiRequest('/report/custom', { method: 'POST', body: JSON.stringify({ items }) });
// GET /blog/news -> [{ title, description, url, image, source, published_at }].
// Fetched live from GNews on every call, nothing is stored server-side, so
// this is re-requested each time the Blog page mounts.
const fetchBlogNews = () => apiRequest('/blog/news');

function base64ToBlob(base64, mimeType) {
  const byteChars = atob(base64);
  const byteNumbers = new Array(byteChars.length);
  for (let i = 0; i < byteChars.length; i++) byteNumbers[i] = byteChars.charCodeAt(i);
  return new Blob([new Uint8Array(byteNumbers)], { type: mimeType });
}

function downloadCustomReportPdf(pdfBase64) {
  const blob = base64ToBlob(pdfBase64, 'application/pdf');
  const url = URL.createObjectURL(blob);
  const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
  const link = document.createElement('a');
  link.href = url;
  link.download = `US_Group_Analytics_Report_${today}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

// POST /warnings/pdf { letter } -> { pdf_base64 } - renders whatever letter
// text the caller has on screen (an admin's draft, or a user's own already-
// saved warning) as a PDF with the same letterhead as the standard report.
const requestWarningPdf = (letterText) =>
  apiRequest('/warnings/pdf', { method: 'POST', body: JSON.stringify({ letter: letterText }) });

function downloadWarningLetterPdf(pdfBase64) {
  const blob = base64ToBlob(pdfBase64, 'application/pdf');
  const url = URL.createObjectURL(blob);
  const today = new Date().toISOString().slice(0, 10);
  const link = document.createElement('a');
  link.href = url;
  link.download = `US_Group_Warning_Letter_${today}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Shared form helpers
// ---------------------------------------------------------------------------

const initialFormData = {
  Sub_Company: '',
  Division: '',
  Unit: '',
  Customer_Country: '',
  Customer_Segment: '',
  Order_Priority: '',
  Product_Category: '',
  UOM: '',
  Order_Quantity: '',
  Unit_Price_USD: '',
  Discount_Pct: 2,
  Payment_Terms: '',
  Shipping_Mode: '',
};

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
}

function getUnitOptions(options, subCompany, division) {
  const bySubCompany = options.units_by_sub_company;
  if (!subCompany || !bySubCompany) return [];
  const entry = bySubCompany[subCompany];
  if (!entry) return [];
  if (subCompany === 'USAT') return division ? entry[division] || [] : [];
  return entry;
}

function validateForm(formData) {
  const required = [
    'Sub_Company', 'Unit', 'Customer_Country', 'Customer_Segment',
    'Order_Priority', 'Product_Category', 'UOM', 'Payment_Terms', 'Shipping_Mode',
  ];
  for (const key of required) {
    if (!formData[key]) return `Please fill in all required fields (${key.replaceAll('_', ' ')}).`;
  }
  if (formData.Sub_Company === 'USAT' && !formData.Division) {
    return 'Division is required when Sub-Company is USAT.';
  }
  if (!formData.Order_Quantity || Number(formData.Order_Quantity) <= 0) {
    return 'Order quantity must be greater than 0.';
  }
  if (!formData.Unit_Price_USD || Number(formData.Unit_Price_USD) <= 0) {
    return 'Unit price must be greater than 0.';
  }
  return null;
}

function buildPayload(formData) {
  const payload = {
    Sub_Company: formData.Sub_Company,
    Unit: formData.Unit,
    Customer_Country: formData.Customer_Country,
    Customer_Segment: formData.Customer_Segment,
    Order_Priority: formData.Order_Priority,
    Product_Category: formData.Product_Category,
    UOM: formData.UOM,
    Order_Quantity: Number(formData.Order_Quantity),
    Unit_Price_USD: Number(formData.Unit_Price_USD),
    Discount_Pct: Number(formData.Discount_Pct),
    Payment_Terms: formData.Payment_Terms,
    Shipping_Mode: formData.Shipping_Mode,
  };
  if (formData.Sub_Company === 'USAT') payload.Division = formData.Division;
  return payload;
}

// ---------------------------------------------------------------------------
// Login / signup screen. Real backend auth (backend/auth/services.py) -
// signup issues an OTP (shown on screen, no email sending yet), verifying
// it creates the account, and login returns a JWT that gets attached to
// every subsequent request by apiRequest (see AUTH_STORAGE_KEY above).
// ---------------------------------------------------------------------------

const PINNED_CHARTS_STORAGE_KEY = 'usgroup_pinned_charts';

// Renders a slow, faint drifting particle field behind the login card
// for ambient depth (Three.js). No pointer tracking.
function LoginWatermark() {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!window.THREE || !canvasRef.current) return undefined;
    const THREE = window.THREE;
    const canvas = canvasRef.current;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, canvas.clientWidth / canvas.clientHeight, 0.1, 100);
    camera.position.z = 13;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);

    const particleCount = 100;
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 16;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 16;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 6;
    }
    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particles = new THREE.Points(
      particleGeometry,
      new THREE.PointsMaterial({
        color: 0xb8f7e4,
        size: 0.05,
        transparent: true,
        opacity: 0.5,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      })
    );
    scene.add(particles);

    const clock = new THREE.Clock();
    let frameId;
    function animate() {
      const t = clock.getElapsedTime();
      particles.rotation.z = t * 0.01;
      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    }
    animate();

    function handleResize() {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h, false);
    }
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('resize', handleResize);
      particleGeometry.dispose();
      particles.material.dispose();
      renderer.dispose();
    };
  }, []);

  return <canvas ref={canvasRef} className="login-canvas" />;
}

// Brand chip + watermark background shared by every step of the auth flow.
function LoginShell({ children }) {
  return (
    <div className="login-screen">
      <LoginWatermark />
      <div className="card login-card">
        <div className="login-brand-card">
          <img src="/logo-lion.png" alt="" className="login-brand-lion" />
          <span className="login-brand-divider" />
          <img src="/logo-wordmark.png" alt="US Group" className="login-brand-wordmark" />
        </div>
        {children}
      </div>
    </div>
  );
}

// google.accounts.id.initialize() must run only ONCE per page (it sets a single
// global callback). Since we render the button on BOTH the sign-in and sign-up
// panes, we guard init with this module-level flag; each instance still draws
// its own button via renderButton(). Both use the same handleGoogleCredential.
let _gisInitialized = false;

// Renders Google's "Continue with Google" button. It fetches the public client
// id from /auth/config; if none is set, it renders nothing (feature stays off
// until GOOGLE_CLIENT_ID is configured on the server). Waits for the GIS script
// (loaded in index.html) to be ready, then initializes and draws the button.
function GoogleSignInButton({ onCredential }) {
  const holderRef = useRef(null);
  const [clientId, setClientId] = useState(null); // null = loading, '' = disabled

  useEffect(() => {
    let cancelled = false;
    fetchAuthConfig()
      .then((cfg) => { if (!cancelled) setClientId(cfg.google_client_id || ''); })
      .catch(() => { if (!cancelled) setClientId(''); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!clientId) return; // still loading, or not configured
    let tries = 0;
    const timer = setInterval(() => {
      tries += 1;
      const gis = window.google && window.google.accounts && window.google.accounts.id;
      if (gis) {
        clearInterval(timer);
        if (!_gisInitialized) {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: (resp) => onCredential(resp.credential),
          });
          _gisInitialized = true;
        }
        if (holderRef.current) {
          window.google.accounts.id.renderButton(holderRef.current, {
            theme: 'filled_black', size: 'large', width: 320,
            text: 'continue_with', shape: 'pill',
          });
        }
      } else if (tries > 40) {
        clearInterval(timer); // GIS script didn't load within ~8s
      }
    }, 200);
    return () => clearInterval(timer);
  }, [clientId]);

  if (!clientId) return null;
  return (
    <div className="google-signin">
      <div className="login-divider"><span>or</span></div>
      <div ref={holderRef} className="google-btn-holder" />
    </div>
  );
}

function LoginSignupPage({ onLoginSuccess }) {
  const [mode, setMode] = useState('login'); // 'login' | 'signup' | 'otp'
  const [banner, setBanner] = useState(null);

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState(null);
  const [loginSubmitting, setLoginSubmitting] = useState(false);

  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupError, setSignupError] = useState(null);
  const [signupSubmitting, setSignupSubmitting] = useState(false);

  const [otp, setOtp] = useState(null);           // dev-fallback code (null once emailed)
  const [otpEmailed, setOtpEmailed] = useState(false);
  const [otpInput, setOtpInput] = useState('');
  const [otpError, setOtpError] = useState(null);
  const [otpSubmitting, setOtpSubmitting] = useState(false);

  function switchMode(next) {
    setMode(next);
    setBanner(null);
    setLoginError(null);
    setSignupError(null);
    setOtpError(null);
  }

  async function handleLoginSubmit(e) {
    e.preventDefault();
    setLoginError(null);
    setLoginSubmitting(true);
    try {
      const result = await loginRequest(loginEmail, loginPassword);
      const payload = decodeJwtPayload(result.token);
      onLoginSuccess({ ...result, email: (payload && payload.email) || loginEmail });
    } catch (err) {
      setLoginError(err.message);
    } finally {
      setLoginSubmitting(false);
    }
  }

  async function handleSignupSubmit(e) {
    e.preventDefault();
    setSignupError(null);
    setSignupSubmitting(true);
    try {
      const result = await signupRequest(signupName, signupEmail, signupPassword);
      setOtp(result.otp || null);        // null when the code was emailed
      setOtpEmailed(!!result.emailed);
      setMode('otp');
    } catch (err) {
      setSignupError(err.message);
    } finally {
      setSignupSubmitting(false);
    }
  }

  // Continue-with-Google: exchange the GIS credential (ID token) for our JWT.
  async function handleGoogleCredential(credential) {
    setLoginError(null);
    setBanner(null);
    try {
      const result = await googleAuthRequest(credential);
      const payload = decodeJwtPayload(result.token);
      onLoginSuccess({ ...result, email: (payload && payload.email) || '' });
    } catch (err) {
      // a pending-approval account comes back as a 403 with an approval message
      if (err.message && err.message.toLowerCase().includes('approval')) {
        setBanner(err.message);
      } else {
        setLoginError(err.message);
      }
      setMode('login');
    }
  }

  async function handleOtpSubmit(e) {
    e.preventDefault();
    setOtpError(null);
    setOtpSubmitting(true);
    try {
      await verifyOtpRequest(signupEmail, otpInput);
      setLoginEmail(signupEmail);
      setSignupName('');
      setSignupPassword('');
      setOtp(null);
      setOtpInput('');
      setBanner('Account created - your account is waiting for admin approval. You can log in once approved.');
      setMode('login');
    } catch (err) {
      setOtpError(err.message);
    } finally {
      setOtpSubmitting(false);
    }
  }

  if (mode === 'otp') {
    return (
      <LoginShell>
        <h1 className="login-title">Verify your email</h1>
        <p className="login-subtitle">Enter the verification code to confirm your account.</p>

        {otpEmailed ? (
          <div className="otp-display">
            <span className="otp-display-label">Check your inbox</span>
            <span className="otp-display-note">
              We've emailed a 6-digit code to <strong>{signupEmail}</strong>. It expires in 10 minutes.
              Don't forget to check spam.
            </span>
          </div>
        ) : (
          <div className="otp-display">
            <span className="otp-display-label">Your verification code</span>
            <span className="otp-display-code">{otp}</span>
            <span className="otp-display-note">
              Email isn't configured on the server, so the code is shown here. Copy it below.
            </span>
          </div>
        )}

        <form onSubmit={handleOtpSubmit}>
          <div className="login-field">
            <label>Verification code</label>
            <div className="login-input-wrap">
              <Icon name="lock" size={16} />
              <input
                type="text"
                inputMode="numeric"
                value={otpInput}
                onChange={(e) => setOtpInput(e.target.value)}
                placeholder="6-digit code"
                autoFocus
                required
              />
            </div>
          </div>

          {otpError && <div className="form-error">{otpError}</div>}

          <button type="submit" className="btn btn-primary btn-full login-submit" disabled={otpSubmitting}>
            {otpSubmitting && <span className="spinner" />}
            {otpSubmitting ? 'Verifying...' : 'Verify & Create Account'}
          </button>
        </form>

        <p className="login-footer">Internal tool &middot; Authorized personnel only</p>
      </LoginShell>
    );
  }

  // Login + Signup share one sliding split-panel card. mode === 'signup'
  // activates the swipe via the auth-active-signup class; the overlay's ghost
  // buttons flip the mode. (The OTP step is the separate branch above.)
  const activeSignup = mode === 'signup';
  return (
    <div className="login-screen">
      <LoginWatermark />
      <div className={`auth-slider${activeSignup ? ' auth-active-signup' : ''}`}>

        {/* ---- Sign Up form (slides in from the left when active) ---- */}
        <div className="auth-pane auth-pane-signup">
          <form className="auth-form" onSubmit={handleSignupSubmit}>
            <h1 className="auth-title">Create account</h1>
            <p className="auth-subtitle">Sign up to request access.</p>

            <div className="login-field">
              <label>Name</label>
              <div className="login-input-wrap">
                <Icon name="user" size={16} />
                <input type="text" value={signupName} onChange={(e) => setSignupName(e.target.value)}
                  placeholder="Jane Doe" autoComplete="name" required />
              </div>
            </div>
            <div className="login-field">
              <label>Email</label>
              <div className="login-input-wrap">
                <Icon name="mail" size={16} />
                <input type="email" value={signupEmail} onChange={(e) => setSignupEmail(e.target.value)}
                  placeholder="jane@usgroup.com" autoComplete="email" required />
              </div>
            </div>
            <div className="login-field">
              <label>Password</label>
              <div className="login-input-wrap">
                <Icon name="lock" size={16} />
                <input type="password" value={signupPassword} onChange={(e) => setSignupPassword(e.target.value)}
                  placeholder="••••••••" autoComplete="new-password" required />
              </div>
            </div>

            {signupError && <div className="form-error">{signupError}</div>}

            <button type="submit" className="btn btn-primary btn-full login-submit" disabled={signupSubmitting}>
              {signupSubmitting && <span className="spinner" />}
              {signupSubmitting ? 'Signing up...' : 'Sign Up'}
            </button>

            <GoogleSignInButton onCredential={handleGoogleCredential} />

            <p className="auth-switch-mobile">
              Already have an account?{' '}
              <button type="button" className="login-toggle-link" onClick={() => switchMode('login')}>Log in</button>
            </p>
          </form>
        </div>

        {/* ---- Sign In form (default view) ---- */}
        <div className="auth-pane auth-pane-signin">
          <form className="auth-form" onSubmit={handleLoginSubmit}>
            <h1 className="auth-title">Welcome back</h1>
            <p className="auth-subtitle">Sign in to access the dashboard.</p>

            {banner && <div className="login-banner">{banner}</div>}

            <div className="login-field">
              <label>Email</label>
              <div className="login-input-wrap">
                <Icon name="mail" size={16} />
                <input type="text" value={loginEmail} onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="admin or jane@usgroup.com" autoComplete="username" required />
              </div>
            </div>
            <div className="login-field">
              <label>Password</label>
              <div className="login-input-wrap">
                <Icon name="lock" size={16} />
                <input type="password" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="••••••••" autoComplete="current-password" required />
              </div>
            </div>

            {loginError && <div className="form-error">{loginError}</div>}

            <button type="submit" className="btn btn-primary btn-full login-submit" disabled={loginSubmitting}>
              {loginSubmitting && <span className="spinner" />}
              {loginSubmitting ? 'Signing in...' : 'Log In'}
            </button>

            <p className="auth-switch-mobile">
              Don't have an account?{' '}
              <button type="button" className="login-toggle-link" onClick={() => switchMode('signup')}>Sign up</button>
            </p>
          </form>
        </div>

        {/* ---- Sliding overlay with the mint gradient + swap buttons ---- */}
        <div className="auth-overlay-container">
          <div className="auth-overlay">
            <div className="auth-overlay-panel auth-overlay-left">
              <div className="login-brand-card auth-overlay-brand">
                <img src="/logo-lion.png" alt="" className="login-brand-lion" />
                <span className="login-brand-divider" />
                <img src="/logo-wordmark.png" alt="US Group" className="login-brand-wordmark" />
              </div>
              <h1 className="auth-overlay-title">Welcome back!</h1>
              <p className="auth-overlay-text">Already have an account? Sign in and pick up where you left off.</p>
              <button type="button" className="auth-ghost-btn" onClick={() => switchMode('login')}>Sign In</button>
            </div>
            <div className="auth-overlay-panel auth-overlay-right">
              <div className="login-brand-card auth-overlay-brand">
                <img src="/logo-lion.png" alt="" className="login-brand-lion" />
                <span className="login-brand-divider" />
                <img src="/logo-wordmark.png" alt="US Group" className="login-brand-wordmark" />
              </div>
              <h1 className="auth-overlay-title">Hello there!</h1>
              <p className="auth-overlay-text">New to US Group Analytics? Create an account to request access.</p>
              <button type="button" className="auth-ghost-btn" onClick={() => switchMode('signup')}>Sign Up</button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Small presentational components
// ---------------------------------------------------------------------------

function Sidebar({ page, onNavigate, onLogout, role }) {
  const linkClass = (target) => `sidebar-link${page === target ? ' active' : ''}`;
  return (
    <aside className="sidebar">
      <div className="sidebar-brand-card">
        <img src="/logo-lion.png" alt="" className="brand-lion" />
        <span className="brand-divider" />
        <img src="/logo-wordmark.png" alt="US Group" className="brand-wordmark" />
      </div>
      <div className="sidebar-app-label">Analytics</div>
      <nav className="sidebar-nav">
        <button className={linkClass('dashboard')} onClick={() => onNavigate('dashboard')}>
          <Icon name="dashboard" size={17} />
          <span>Dashboard</span>
        </button>
        <button className={linkClass('profitability')} onClick={() => onNavigate('profitability')}>
          <Icon name="trendingUp" size={17} />
          <span>Profitability Predictor</span>
        </button>
        <button className={linkClass('payment-delay')} onClick={() => onNavigate('payment-delay')}>
          <Icon name="clock" size={17} />
          <span>Payment Delay Predictor</span>
        </button>
        <button className={linkClass('chat')} onClick={() => onNavigate('chat')}>
          <Icon name="message" size={17} />
          <span>Ask US Group</span>
        </button>
        <button className={linkClass('blog')} onClick={() => onNavigate('blog')}>
          <Icon name="newspaper" size={17} />
          <span>Blog</span>
        </button>
        {/* added: market scraper tab */}
        <button className={linkClass('scraper')} onClick={() => onNavigate('scraper')}>
          <Icon name="globe" size={17} />
          <span>Market Scraper</span>
        </button>
        <button className={linkClass('warnings')} onClick={() => onNavigate('warnings')}>
          <Icon name="alertTriangle" size={17} />
          <span>Warnings</span>
        </button>
        {role === 'admin' && (
          <button className={linkClass('admin')} onClick={() => onNavigate('admin')}>
            <Icon name="lock" size={17} />
            <span>Accounts</span>
          </button>
        )}
        {role === 'admin' && (
          <button className={linkClass('audit-log')} onClick={() => onNavigate('audit-log')}>
            <Icon name="activity" size={17} />
            <span>Audit Log</span>
          </button>
        )}
      </nav>
      <div className="sidebar-footer">
        <span>v1.0 &middot; Internal Tool</span>
        <button className="sidebar-logout" onClick={onLogout}>
          <Icon name="logOut" size={14} />
          <span>Log out</span>
        </button>
      </div>
    </aside>
  );
}

function KpiCard({ icon, label, value, note }) {
  return (
    <div className="card kpi-card">
      <div className="kpi-icon"><Icon name={icon} size={17} /></div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
      {note && <div className="kpi-note">{note}</div>}
    </div>
  );
}

function ConfidenceRing({ value, color }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;
  return (
    <div className="confidence-ring">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} className="ring-track" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          className="ring-progress"
          style={{ stroke: color, strokeDasharray: circumference, strokeDashoffset: offset }}
        />
      </svg>
      <div className="ring-label">
        <span className="ring-value">{value}%</span>
        <span className="ring-caption">confidence</span>
      </div>
    </div>
  );
}

function ResultCard({ result, negativeTone }) {
  const tone = result.is_positive ? 'success' : negativeTone;
  const color =
    tone === 'success' ? 'var(--color-success)' : tone === 'warning' ? 'var(--color-warning)' : 'var(--color-danger)';
  const iconName = result.is_positive ? 'checkCircle' : negativeTone === 'warning' ? 'alertTriangle' : 'xCircle';

  return (
    <div className={`card result-card tone-${tone} result-enter`}>
      <ConfidenceRing value={result.confidence} color={color} />
      <div>
        <span className="result-badge">
          <Icon name={iconName} size={15} />
          {result.prediction}
        </span>
        <p className="result-explanation">{result.explanation}</p>
        <div className="result-factors">
          {result.key_factors.map((factor, i) => (
            <div className="result-factor" key={i}>
              <Icon name="dot" size={8} />
              <span>{factor}</span>
            </div>
          ))}
        </div>
        <span className="result-source-tag">
          <Icon name="info" size={12} />
          {result.model_source === 'model' ? 'Live model prediction (notebook)' : 'Heuristic preview (model not connected yet)'}
        </span>
      </div>
    </div>
  );
}

function OrderForm({ options, formData, onChange, onSubmit, loading, error, submitLabel }) {
  const unitOptions = getUnitOptions(options, formData.Sub_Company, formData.Division);
  const showDivision = formData.Sub_Company === 'USAT';

  return (
    <form className="card card-padded" onSubmit={onSubmit}>
      <div className="field-grid">
        <div className="field">
          <label>Sub-Company</label>
          <select value={formData.Sub_Company} onChange={(e) => onChange('Sub_Company', e.target.value)} required>
            <option value="" disabled>Select sub-company</option>
            {options.sub_companies?.map((sc) => <option key={sc} value={sc}>{sc}</option>)}
          </select>
        </div>

        {showDivision && (
          <div className="field">
            <label>Division</label>
            <select value={formData.Division} onChange={(e) => onChange('Division', e.target.value)} required>
              <option value="" disabled>Select division</option>
              <option value="USA">USA</option>
              <option value="UK">UK</option>
            </select>
          </div>
        )}

        <div className="field">
          <label>Unit</label>
          <select
            value={formData.Unit}
            onChange={(e) => onChange('Unit', e.target.value)}
            required
            disabled={unitOptions.length === 0}
          >
            <option value="" disabled>Select unit</option>
            {unitOptions.map((u) => <option key={u} value={u}>{u}</option>)}
          </select>
        </div>

        <div className="field">
          <label>Customer Country</label>
          <select value={formData.Customer_Country} onChange={(e) => onChange('Customer_Country', e.target.value)} required>
            <option value="" disabled>Select country</option>
            {options.customer_countries?.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div className="field">
          <label>Customer Segment</label>
          <select value={formData.Customer_Segment} onChange={(e) => onChange('Customer_Segment', e.target.value)} required>
            <option value="" disabled>Select segment</option>
            {options.customer_segments?.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="field">
          <label>Order Priority</label>
          <select value={formData.Order_Priority} onChange={(e) => onChange('Order_Priority', e.target.value)} required>
            <option value="" disabled>Select priority</option>
            {options.order_priorities?.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        <div className="field">
          <label>Product Category</label>
          <select value={formData.Product_Category} onChange={(e) => onChange('Product_Category', e.target.value)} required>
            <option value="" disabled>Select category</option>
            {options.product_categories?.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        <div className="field">
          <label>Unit of Measure</label>
          <select value={formData.UOM} onChange={(e) => onChange('UOM', e.target.value)} required>
            <option value="" disabled>Select UOM</option>
            {options.uom_options?.map((u) => <option key={u} value={u}>{u}</option>)}
          </select>
        </div>

        <div className="field">
          <label>Order Quantity</label>
          <input
            type="number"
            min="1"
            step="1"
            value={formData.Order_Quantity}
            onChange={(e) => onChange('Order_Quantity', e.target.value)}
            required
          />
        </div>

        <div className="field">
          <label>Unit Price (USD)</label>
          <input
            type="number"
            min="0.01"
            step="0.01"
            value={formData.Unit_Price_USD}
            onChange={(e) => onChange('Unit_Price_USD', e.target.value)}
            required
          />
        </div>

        <div className="field field-span-2">
          <label>
            Discount % <span className="field-hint">0-10%</span>
          </label>
          <div className="slider-row">
            <input
              type="range"
              min="0"
              max="10"
              step="0.1"
              value={formData.Discount_Pct}
              onChange={(e) => onChange('Discount_Pct', e.target.value)}
            />
            <span className="slider-value">{Number(formData.Discount_Pct).toFixed(1)}%</span>
          </div>
        </div>

        <div className="field">
          <label>Payment Terms</label>
          <select value={formData.Payment_Terms} onChange={(e) => onChange('Payment_Terms', e.target.value)} required>
            <option value="" disabled>Select payment terms</option>
            {options.payment_terms?.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        <div className="field">
          <label>Shipping Mode</label>
          <select value={formData.Shipping_Mode} onChange={(e) => onChange('Shipping_Mode', e.target.value)} required>
            <option value="" disabled>Select shipping mode</option>
            {options.shipping_modes?.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {error && <div className="form-error">{error}</div>}

      <div className="form-footer">
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading && <span className="spinner" />}
          {loading ? 'Running notebook...' : submitLabel}
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Pages
// ---------------------------------------------------------------------------

function TopCustomersCard({ customers }) {
  return (
    <div className="card card-padded">
      <div className="panel-heading">
        <div className="panel-icon"><Icon name="award" size={18} /></div>
        <div>
          <div className="panel-title">Top 5 Customers</div>
          <div className="panel-subtitle">By total profit, all sub-companies, full dataset</div>
        </div>
      </div>
      <ol className="customer-list">
        {customers.map((c, i) => (
          <li className="customer-row" key={c.name}>
            <span className="customer-rank">{i + 1}</span>
            <span className="customer-name">{c.name}</span>
            <span className="customer-profit">{formatCurrency(c.total_profit_usd)}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function ProfitTrendCard({ trend }) {
  const monthLabel = `${MONTH_NAMES[trend.forecast_month - 1]} ${trend.forecast_year}`;
  return (
    <div className="card card-padded">
      <div className="panel-heading">
        <div className="panel-icon"><Icon name="calendar" size={18} /></div>
        <div>
          <div className="panel-title">Next Month Profit Trend</div>
          <div className="panel-subtitle">{monthLabel} estimate</div>
        </div>
      </div>
      <div className="trend-value">{formatCurrency(trend.forecast_usd)}</div>
      <div className="trend-basis">
        {trend.basis_months.map((m) => `${MONTH_NAMES[m.month - 1].slice(0, 3)} ${formatCurrency(m.total_profit_usd)}`).join('  ·  ')}
      </div>
      <p className="trend-caveat">
        Simple 3-month rolling average, not a validated ML model - every regression model tried in the notebook
        (Linear Regression, Decision Tree, SVR, KNN, ANN) scored a negative R&sup2; on this dataset's ~18 months of
        history, meaning each performed worse than this average. Treat this as a rough trend, not a forecast.
      </p>
    </div>
  );
}

// "Print Report" trigger + selection dropdown next to the Pinned Charts
// heading. Lets the user hand-pick which pinned charts go into a polished
// PDF (POST /report/custom), rather than always bundling all of them.
function PrintReportPanel({ pinnedCharts }) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(() => new Set());
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const panelRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const handleClickOutside = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  function toggleOne(id) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected((prev) =>
      prev.size === pinnedCharts.length ? new Set() : new Set(pinnedCharts.map((c) => c.id))
    );
  }

  async function handleConfirm() {
    const items = pinnedCharts
      .filter((c) => selected.has(c.id))
      .map((c) => ({ question: c.heading, answer: c.explanation, chart_image_base64: c.image }));
    if (items.length === 0) return;

    setGenerating(true);
    setError(null);
    try {
      const { pdf_base64 } = await generateCustomReport(items);
      downloadCustomReportPdf(pdf_base64);
      setOpen(false);
      setSelected(new Set());
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  }

  const allSelected = pinnedCharts.length > 0 && selected.size === pinnedCharts.length;

  return (
    <div className="print-report-menu" ref={panelRef}>
      <button type="button" className="btn chat-history-toggle" onClick={() => setOpen((v) => !v)}>
        <Icon name="printer" size={15} />
        Print Report
      </button>

      {open && (
        <div className="print-report-dropdown">
          <label className="print-report-item print-report-select-all">
            <input type="checkbox" checked={allSelected} onChange={toggleAll} />
            <span>Select All</span>
          </label>

          <div className="print-report-list">
            {pinnedCharts.map((chart) => (
              <label className="print-report-item" key={chart.id}>
                <input type="checkbox" checked={selected.has(chart.id)} onChange={() => toggleOne(chart.id)} />
                <span>{chart.heading}</span>
              </label>
            ))}
          </div>

          {error && <div className="print-report-error">Could not generate PDF: {error}</div>}

          <button
            type="button"
            className="btn btn-primary btn-full"
            onClick={handleConfirm}
            disabled={generating || selected.size === 0}
          >
            {generating && <span className="spinner" />}
            {generating ? 'Generating...' : `Generate PDF (${selected.size})`}
          </button>
        </div>
      )}
    </div>
  );
}

// A chart pinned from the "Ask US Group" chat (see ChatDashboardPinButton)
// shows up here as its own card - heading (the question that was asked),
// a short explanation (the chat answer), and the chart image itself.
function PinnedChartCard({ chart, onRemove }) {
  return (
    <div className="card card-padded pinned-chart-card">
      <div className="pinned-chart-header">
        <div className="pinned-chart-title">{chart.heading}</div>
        <button
          type="button"
          className="pinned-chart-remove"
          onClick={() => onRemove(chart.id)}
          aria-label="Remove from dashboard"
        >
          <Icon name="close" size={14} />
        </button>
      </div>
      <p className="pinned-chart-explanation">{chart.explanation}</p>
      <div className="pinned-chart-image-wrap">
        <img className="pinned-chart-image" src={`data:image/png;base64,${chart.image}`} alt={chart.heading} />
      </div>
    </div>
  );
}

function DashboardPage({ onNavigate, pinnedCharts, onRemovePinnedChart }) {
  const [stats, setStats] = useState(null);
  const [statsError, setStatsError] = useState(null);

  useEffect(() => {
    fetchDashboardStats()
      .then(setStats)
      .catch((err) => setStatsError(err.message));
  }, []);

  return (
    <div className="app-content">
      <header className="page-header">
        <div className="page-eyebrow">Overview</div>
        <h1 className="page-title">Analytics dashboard</h1>
        <p className="page-subtitle">
          Analysis of the whole company stands here
        </p>
      </header>

      <div className="kpi-grid">
        <KpiCard icon="package" label="Total Orders" value="4,845" note="FY2025-FY2026 dataset" />
        <KpiCard icon="dollar" label="Total Dispatch Value" value="$314.2M" />
        <KpiCard icon="percent" label="Net Margin" value="4.3%" />
        <KpiCard icon="timer" label="On-Time Payment Rate" value="83.0%" />
      </div>

      <div className="section-heading">Prediction Tools</div>
      <div className="tool-nav-grid">
        <button className="card tool-nav-card" onClick={() => onNavigate('profitability')}>
          <div className="tool-nav-icon"><Icon name="trendingUp" size={19} /></div>
          <div className="tool-nav-title">Profitability Predictor</div>
          <div className="tool-nav-desc">Estimate whether a new order will be profitable before you confirm it.</div>
          <span className="tool-nav-cta">Open tool <Icon name="arrowRight" size={14} /></span>
        </button>
        <button className="card tool-nav-card" onClick={() => onNavigate('payment-delay')}>
          <div className="tool-nav-icon"><Icon name="clock" size={19} /></div>
          <div className="tool-nav-title">Payment Delay Predictor</div>
          <div className="tool-nav-desc">
            Check the odds a customer pays late so you can plan cash flow ahead of time.
          </div>
          <span className="tool-nav-cta">Open tool <Icon name="arrowRight" size={14} /></span>
        </button>
      </div>

      <div className="section-heading">Insights</div>
      {statsError && <div className="form-error">Could not load dashboard insights ({statsError}).</div>}
      {stats && (
        <div className="insights-grid">
          <TopCustomersCard customers={stats.top_customers} />
          <ProfitTrendCard trend={stats.profit_trend} />
        </div>
      )}

      {pinnedCharts.length > 0 && (
        <>
          <div className="section-heading-row">
            <div className="section-heading">Pinned Charts</div>
            <PrintReportPanel pinnedCharts={pinnedCharts} />
          </div>
          <div className="pinned-charts-grid">
            {pinnedCharts.map((chart) => (
              <PinnedChartCard chart={chart} onRemove={onRemovePinnedChart} key={chart.id} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function PredictorPage({ options, title, subtitle, submitLabel, negativeTone, predictFn }) {
  const [formData, setFormData] = useState(initialFormData);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function handleChange(name, value) {
    setFormData((prev) => {
      const next = { ...prev, [name]: value };
      if (name === 'Sub_Company') {
        next.Division = '';
        next.Unit = '';
      }
      if (name === 'Division') next.Unit = '';
      return next;
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const validationError = validateForm(formData);
    setError(validationError);
    if (validationError) return;

    setLoading(true);
    setResult(null);
    try {
      const data = await predictFn(buildPayload(formData));
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-content">
      <header className="page-header">
        <div className="page-eyebrow">Prediction Tool</div>
        <h1 className="page-title">{title}</h1>
        <p className="page-subtitle">{subtitle}</p>
      </header>

      <OrderForm
        options={options}
        formData={formData}
        onChange={handleChange}
        onSubmit={handleSubmit}
        loading={loading}
        error={error}
        submitLabel={submitLabel}
      />

      {result && <ResultCard result={result} negativeTone={negativeTone} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Blog - live textile industry headlines from GET /blog/news (GNews). Fetched
// fresh on every mount; there is no persistence behind this page, so what you
// see is whatever GNews returned in that request.
// ---------------------------------------------------------------------------

function formatArticleDate(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function ArticleCard({ article }) {
  // GNews hands back image URLs that are sometimes dead by the time we render
  // them, so a load failure falls back to the same placeholder used when the
  // article had no image at all - never a broken-image icon.
  const [imageFailed, setImageFailed] = useState(false);
  const showImage = article.image && !imageFailed;
  const published = formatArticleDate(article.published_at);

  return (
    <a className="card article-card" href={article.url} target="_blank" rel="noopener noreferrer">
      <div className="article-thumb">
        {showImage ? (
          <img src={article.image} alt="" loading="lazy" onError={() => setImageFailed(true)} />
        ) : (
          <div className="article-thumb-placeholder">
            <Icon name="image" size={22} />
          </div>
        )}
      </div>
      <div className="article-body">
        <h3 className="article-title">{article.title}</h3>
        {article.description && <p className="article-description">{article.description}</p>}
        <div className="article-meta">
          <span className="article-source">{article.source}</span>
          {published && (
            <>
              <span className="article-meta-dot">&middot;</span>
              <span>{published}</span>
            </>
          )}
          <span className="article-open">
            <Icon name="externalLink" size={13} />
          </span>
        </div>
      </div>
    </a>
  );
}

// The backend hands back every article it fetched in one response; splitting
// them across pages here is purely presentational, so paging is instant and
// costs no extra GNews requests.
const ARTICLES_PER_PAGE = 10;

function BlogPagination({ page, pageCount, onChange }) {
  if (pageCount <= 1) return null;
  const pages = Array.from({ length: pageCount }, (_, i) => i + 1);

  return (
    <nav className="blog-pagination">
      <button
        type="button"
        className="btn blog-page-btn"
        disabled={page === 1}
        onClick={() => onChange(page - 1)}
      >
        <Icon name="arrowLeft" size={14} />
        <span>Previous</span>
      </button>
      <div className="blog-page-numbers">
        {pages.map((n) => (
          <button
            type="button"
            key={n}
            className={`btn blog-page-btn blog-page-number${n === page ? ' active' : ''}`}
            onClick={() => onChange(n)}
          >
            {n}
          </button>
        ))}
      </div>
      <button
        type="button"
        className="btn blog-page-btn"
        disabled={page === pageCount}
        onClick={() => onChange(page + 1)}
      >
        <span>Next</span>
        <Icon name="arrowRight" size={14} />
      </button>
    </nav>
  );
}

// ---------------------------------------------------------------------------
// Market Scraper page (added)
// Two-step flow: (1) Scrape a category URL -> results are staged server-side in
// a JSON file and shown here; (2) Save to Database -> those staged rows are
// inserted into the scraped_products table, which the chatbot can then query.
// ---------------------------------------------------------------------------
function ScraperPage() {
  const [url, setUrl] = useState('');
  const [brand, setBrand] = useState('');
  const [scraped, setScraped] = useState(null); // products from the latest scrape
  const [scraping, setScraping] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null); // success line after a DB save
  const [recent, setRecent] = useState([]); // rows already in the database

  function loadRecent() {
    apiRequest('/market-data/')
      .then(setRecent)
      .catch(() => {}); // a failed refresh of the recent list isn't worth an error banner
  }

  useEffect(loadRecent, []);

  async function handleScrape(e) {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setScraped(null);
    setScraping(true);
    try {
      const res = await apiRequest('/market-data/scrape', {
        method: 'POST',
        body: JSON.stringify({ url, brand }),
      });
      setScraped(res.products);
      if (res.count === 0) {
        setNotice('Scrape ran but found no products - the page markup may not match the scraper selectors.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setScraping(false);
    }
  }

  async function handleSave() {
    setError(null);
    setNotice(null);
    setSaving(true);
    try {
      const res = await apiRequest('/market-data/save', { method: 'POST' });
      setNotice(`Saved ${res.inserted} product(s) to the database.`);
      loadRecent();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="app-content">
      <header className="page-header">
        <div className="page-eyebrow">Live Web Scraping</div>
        <h1 className="page-title">Market Scraper</h1>
        <p className="page-subtitle">
          Scrape product and pricing data from a retail brand category page, review it, then save it
          to the database so the assistant can answer questions about it.
        </p>
      </header>

      <form className="card scraper-form" onSubmit={handleScrape}>
        <div className="scraper-field scraper-field-wide">
          <label>Category page URL</label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="http://books.toscrape.com/catalogue/category/books/fiction_10/index.html"
            required
          />
        </div>
        <div className="scraper-field">
          <label>Brand</label>
          <input value={brand} onChange={(e) => setBrand(e.target.value)} placeholder="Levi's" required />
        </div>
        <button type="submit" className="btn btn-primary scraper-scrape-btn" disabled={scraping}>
          {scraping && <span className="spinner" />}
          {scraping ? 'Scraping...' : 'Scrape'}
        </button>
      </form>

      {error && <div className="form-error">{error}</div>}
      {notice && <div className="scraper-notice">{notice}</div>}

      {scraped && scraped.length > 0 && (
        <div className="card scraper-results">
          <div className="scraper-results-head">
            <h2>Scraped results ({scraped.length})</h2>
            <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
              {saving && <span className="spinner" />}
              <Icon name="database" size={15} />
              {saving ? 'Saving...' : 'Save to Database'}
            </button>
          </div>
          <ScrapedTable rows={scraped} showImage />
        </div>
      )}

      <div className="card scraper-results">
        <div className="scraper-results-head">
          <h2>Already in database</h2>
          <button className="btn btn-ghost" onClick={loadRecent}>Refresh</button>
        </div>
        {recent.length === 0
          ? <p className="scraper-empty">No saved products yet.</p>
          : <ScrapedTable rows={recent} />}
      </div>
    </div>
  );
}

// added: shared table for both freshly-scraped rows and saved DB rows
function ScrapedTable({ rows, showImage }) {
  return (
    <div className="scraper-table-wrap">
      <table className="scraper-table">
        <thead>
          <tr>
            {showImage && <th>Image</th>}
            <th>Brand</th>
            <th>Name</th>
            <th>Price</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.id || i}>
              {showImage && (
                <td>{r.image_url ? <img className="scraper-thumb" src={r.image_url} alt="" /> : '-'}</td>
              )}
              <td>{r.brand}</td>
              <td>{r.name}</td>
              <td>{r.price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BlogPage() {
  const [articles, setArticles] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    let cancelled = false; // ignore a late response if the user navigated away
    fetchBlogNews()
      .then((data) => {
        if (!cancelled) setArticles(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const total = articles ? articles.length : 0;
  const pageCount = Math.ceil(total / ARTICLES_PER_PAGE);
  const firstOnPage = (page - 1) * ARTICLES_PER_PAGE;
  const visibleArticles = articles ? articles.slice(firstOnPage, firstOnPage + ARTICLES_PER_PAGE) : [];

  function goToPage(next) {
    setPage(next);
    // Paging swaps the whole grid out - without this you land mid-list on the
    // new page, having scrolled down to reach the controls in the first place.
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <div className="app-content">
      <header className="page-header">
        <div className="page-eyebrow">Industry News</div>
        <h1 className="page-title">Blog</h1>
        <p className="page-subtitle">
          Live textile, denim and garment export headlines, pulled fresh each time you open this page.
        </p>
      </header>

      {loading && (
        <div className="blog-status">
          <span className="spinner spinner-accent" />
          <span>Fetching the latest industry news...</span>
        </div>
      )}

      {!loading && error && <div className="form-error">Could not load the news feed: {error}</div>}

      {!loading && !error && articles && articles.length === 0 && (
        <div className="blog-status blog-empty">
          <Icon name="newspaper" size={22} />
          <span>No articles came back for these topics right now. Check again a little later.</span>
        </div>
      )}

      {!loading && !error && total > 0 && (
        <>
          <div className="blog-count">
            Showing {firstOnPage + 1}&ndash;{firstOnPage + visibleArticles.length} of {total} articles
          </div>
          <div className="article-grid">
            {visibleArticles.map((article, i) => (
              <ArticleCard article={article} key={article.url || `${page}-${i}`} />
            ))}
          </div>
          <BlogPagination page={page} pageCount={pageCount} onChange={goToPage} />
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Admin - All Accounts. Only reachable from the sidebar when role === 'admin'
// (App() also double-checks this before rendering the route at all). Gated
// behind a password re-entry step (POST /auth/verify-password) before the
// account list is fetched or shown - this is a step-up confirmation using
// the currently logged-in admin's own email, not a way to check other
// people's passwords (the backend rejects any other email with a 403).
// ---------------------------------------------------------------------------

function AdminPage({ auth }) {
  const [verified, setVerified] = useState(false);
  const [password, setPassword] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState(null);

  const [users, setUsers] = useState(null);
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersError, setUsersError] = useState(null);
  const [approvingId, setApprovingId] = useState(null);
  const [approveError, setApproveError] = useState(null);
  const [removingId, setRemovingId] = useState(null);
  const [removeError, setRemoveError] = useState(null);

  async function handleVerify(e) {
    e.preventDefault();
    setVerifying(true);
    setVerifyError(null);
    try {
      const { verified: ok } = await verifyPasswordRequest(auth.email, password);
      if (!ok) {
        setVerifyError('Incorrect password.');
        return;
      }
      setVerified(true);
      setUsersLoading(true);
      try {
        setUsers(await fetchAllUsers());
      } catch (err) {
        setUsersError(err.message);
      } finally {
        setUsersLoading(false);
      }
    } catch (err) {
      setVerifyError(err.message);
    } finally {
      setVerifying(false);
    }
  }

  async function handleApprove(id) {
    setApprovingId(id);
    setApproveError(null);
    try {
      await approveUserRequest(id);
      setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, is_approved: true } : u)));
    } catch (err) {
      setApproveError(err.message);
    } finally {
      setApprovingId(null);
    }
  }

  // Shared by "Reject" (pending) and "Delete" (created) - both delete the row.
  async function handleRemove(id, isReject) {
    const confirmMsg = isReject
      ? 'Reject and remove this pending sign-up? This cannot be undone.'
      : 'Delete this account permanently? This cannot be undone.';
    if (!window.confirm(confirmMsg)) return;
    setRemovingId(id);
    setRemoveError(null);
    try {
      await deleteUserRequest(id);
      setUsers((prev) => prev.filter((u) => u.id !== id));
    } catch (err) {
      setRemoveError(err.message);
    } finally {
      setRemovingId(null);
    }
  }

  if (!verified) {
    return (
      <div className="app-content admin-verify-screen">
        <header className="page-header">
          <div className="page-eyebrow">Admin</div>
          <h1 className="page-title">Confirm your password</h1>
          <p className="page-subtitle">For your security, re-enter your password to view all accounts.</p>
        </header>

        <form className="card card-padded admin-verify-card" onSubmit={handleVerify}>
          <div className="login-field">
            <label>Password</label>
            <div className="login-input-wrap">
              <Icon name="lock" size={16} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                autoFocus
                required
              />
            </div>
          </div>

          {verifyError && <div className="form-error">{verifyError}</div>}

          <button type="submit" className="btn btn-primary" disabled={verifying}>
            {verifying && <span className="spinner" />}
            {verifying ? 'Confirming...' : 'Confirm'}
          </button>
        </form>
      </div>
    );
  }

  const pending = users ? users.filter((u) => !u.is_approved) : [];
  const created = users ? users.filter((u) => u.is_approved) : [];

  return (
    <div className="app-content">
      <header className="page-header">
        <div className="page-eyebrow">Admin</div>
        <h1 className="page-title">Accounts</h1>
        <p className="page-subtitle">Review pending sign-ups and manage existing accounts.</p>
      </header>

      {usersLoading && (
        <div className="chat-history-status">
          <span className="spinner spinner-accent" />
          <span>Loading accounts...</span>
        </div>
      )}
      {usersError && <div className="form-error">Could not load accounts: {usersError}</div>}

      {users && (
        <>
          <div className="section-heading">
            Pending Approval{pending.length > 0 ? ` (${pending.length})` : ''}
          </div>
          <div className="card card-padded">
            {pending.length === 0 ? (
              <div className="chat-history-status">No accounts waiting for approval.</div>
            ) : (
              <div className="admin-table-wrap">
                <table className="admin-users-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Created</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {pending.map((u) => (
                      <tr key={u.id}>
                        <td>{u.name}</td>
                        <td>{u.email}</td>
                        <td>{formatHistoryTimestamp(u.created_at)}</td>
                        <td>
                          <div className="admin-actions">
                            <button
                              type="button"
                              className="btn btn-primary admin-row-btn"
                              onClick={() => handleApprove(u.id)}
                              disabled={approvingId === u.id || removingId === u.id}
                            >
                              {approvingId === u.id && <span className="spinner" />}
                              {approvingId === u.id ? 'Approving...' : 'Approve'}
                            </button>
                            <button
                              type="button"
                              className="btn btn-danger admin-row-btn"
                              onClick={() => handleRemove(u.id, true)}
                              disabled={removingId === u.id || approvingId === u.id}
                            >
                              {removingId === u.id ? 'Rejecting...' : 'Reject'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {approveError && <div className="form-error">Could not approve: {approveError}</div>}
          </div>

          <div className="section-heading">Created Accounts</div>
          <div className="card card-padded">
            {created.length === 0 ? (
              <div className="chat-history-status">No approved accounts yet.</div>
            ) : (
              <div className="admin-table-wrap">
                <table className="admin-users-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Created</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {created.map((u) => (
                      <tr key={u.id}>
                        <td>{u.name}</td>
                        <td>{u.email}</td>
                        <td>
                          <span className={`admin-role-badge admin-role-${u.role}`}>{u.role}</span>
                        </td>
                        <td>{formatHistoryTimestamp(u.created_at)}</td>
                        <td>
                          {/* admin accounts are protected - no delete button */}
                          {u.role !== 'admin' && (
                            <button
                              type="button"
                              className="btn btn-danger admin-row-btn"
                              onClick={() => handleRemove(u.id, false)}
                              disabled={removingId === u.id}
                            >
                              {removingId === u.id ? 'Deleting...' : 'Delete'}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {removeError && <div className="form-error">Could not remove account: {removeError}</div>}
          </div>
        </>
      )}
    </div>
  );
}

// Human-readable labels + a rough grouping (for the colored badge) per raw
// action string stored in audit_log/chat_history. Falls back to the raw
// action name for anything not listed here, so a new action type never
// renders blank.
const AUDIT_ACTION_LABELS = {
  login: 'Login', signup: 'Signup', chat: 'Chat',
  predict_profitability: 'Prediction', predict_payment_delay: 'Prediction',
  generate_report: 'Report', custom_report: 'Report',
  scrape: 'Scrape', save_scrape: 'Scrape',
  approve_user: 'Admin', reject_user: 'Admin', delete_user: 'Admin',
};
const AUDIT_ACTION_TONES = {
  login: 'success', signup: 'success',
  approve_user: 'success', reject_user: 'danger', delete_user: 'danger',
};

// Audit Log - Only reachable from the sidebar when role === 'admin'; the
// backend's own /audit-log/:id route re-checks admin on every call regardless.
// Re-verifies the admin's password before showing anything, same as the
// Accounts page, since this exposes every user's activity.
function AuditLogPage({ auth }) {
  const [verified, setVerified] = useState(false);
  const [password, setPassword] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState(null);

  const [users, setUsers] = useState(null);
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersError, setUsersError] = useState(null);

  const [selectedUser, setSelectedUser] = useState(null);
  const [actions, setActions] = useState(null);
  const [actionsLoading, setActionsLoading] = useState(false);
  const [actionsError, setActionsError] = useState(null);

  // Warning-letter flow: pick flagged actions -> LLM drafts a letter (editable)
  // -> Send Warning (saved, shows on the user's own Warnings tab) or Send
  // Email (saved + emailed).
  const [warningMode, setWarningMode] = useState(false);
  const [selectedActionIdx, setSelectedActionIdx] = useState(() => new Set());
  const [letter, setLetter] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState(null);
  const [sendingWarning, setSendingWarning] = useState(false);
  const [sendWarningError, setSendWarningError] = useState(null);
  const [warningSentMsg, setWarningSentMsg] = useState(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [pdfError, setPdfError] = useState(null);

  function resetWarningFlow() {
    setWarningMode(false);
    setSelectedActionIdx(new Set());
    setLetter(null);
    setGenerateError(null);
    setSendWarningError(null);
    setWarningSentMsg(null);
    setPdfError(null);
  }

  function toggleWarningMode() {
    if (warningMode) resetWarningFlow();
    else setWarningMode(true);
  }

  function toggleActionSelected(i) {
    setSelectedActionIdx((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i); else next.add(i);
      return next;
    });
  }

  function chosenActions() {
    return [...selectedActionIdx].sort((a, b) => a - b).map((i) => actions[i]);
  }

  async function handleGenerateLetter() {
    setGenerating(true);
    setGenerateError(null);
    try {
      const data = await generateWarningLetter(selectedUser.id, chosenActions());
      setLetter(data.letter);
    } catch (err) {
      setGenerateError(err.message);
    } finally {
      setGenerating(false);
    }
  }

  async function handleSendWarning(viaEmail) {
    setSendingWarning(true);
    setSendWarningError(null);
    try {
      const data = await sendWarning(selectedUser.id, letter, viaEmail, chosenActions());
      setWarningSentMsg(
        viaEmail
          ? (data.emailed ? 'Warning saved and emailed to the user.' : 'Warning saved, but the email failed to send.')
          : "Warning saved - it now appears on the user's Warnings tab."
      );
      setWarningMode(false);
      setSelectedActionIdx(new Set());
      setLetter(null);
    } catch (err) {
      setSendWarningError(err.message);
    } finally {
      setSendingWarning(false);
    }
  }

  async function handleDownloadPdf() {
    setDownloadingPdf(true);
    setPdfError(null);
    try {
      const data = await requestWarningPdf(letter);
      downloadWarningLetterPdf(data.pdf_base64);
    } catch (err) {
      setPdfError(err.message);
    } finally {
      setDownloadingPdf(false);
    }
  }

  function closeUser() {
    setSelectedUser(null);
    resetWarningFlow();
  }

  async function handleVerify(e) {
    e.preventDefault();
    setVerifying(true);
    setVerifyError(null);
    try {
      const { verified: ok } = await verifyPasswordRequest(auth.email, password);
      if (!ok) {
        setVerifyError('Incorrect password.');
        return;
      }
      setVerified(true);
      setUsersLoading(true);
      try {
        setUsers(await fetchAllUsers());
      } catch (err) {
        setUsersError(err.message);
      } finally {
        setUsersLoading(false);
      }
    } catch (err) {
      setVerifyError(err.message);
    } finally {
      setVerifying(false);
    }
  }

  async function openUser(u) {
    setSelectedUser(u);
    resetWarningFlow();
    setActions(null);
    setActionsError(null);
    setActionsLoading(true);
    try {
      const data = await fetchAuditLog(u.id);
      setActions(data.actions);
    } catch (err) {
      setActionsError(err.message);
    } finally {
      setActionsLoading(false);
    }
  }

  if (!verified) {
    return (
      <div className="app-content admin-verify-screen">
        <header className="page-header">
          <div className="page-eyebrow">Admin</div>
          <h1 className="page-title">Confirm your password</h1>
          <p className="page-subtitle">For your security, re-enter your password to view the audit log.</p>
        </header>

        <form className="card card-padded admin-verify-card" onSubmit={handleVerify}>
          <div className="login-field">
            <label>Password</label>
            <div className="login-input-wrap">
              <Icon name="lock" size={16} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                autoFocus
                required
              />
            </div>
          </div>

          {verifyError && <div className="form-error">{verifyError}</div>}

          <button type="submit" className="btn btn-primary" disabled={verifying}>
            {verifying && <span className="spinner" />}
            {verifying ? 'Confirming...' : 'Confirm'}
          </button>
        </form>
      </div>
    );
  }

  if (selectedUser) {
    const chosenCount = selectedActionIdx.size;
    return (
      <div className="app-content">
        <button type="button" className="btn btn-ghost audit-back-btn" onClick={closeUser}>
          <Icon name="arrowLeft" size={16} />
          <span>Back to all users</span>
        </button>

        <header className="page-header audit-detail-header">
          <div>
            <div className="page-eyebrow">Audit Log</div>
            <h1 className="page-title">{selectedUser.name}</h1>
            <p className="page-subtitle">
              {selectedUser.email}
              {' · '}
              <span className={`admin-role-badge admin-role-${selectedUser.role}`}>{selectedUser.role}</span>
            </p>
          </div>
          {actions && actions.length > 0 && letter === null && (
            <button type="button" className={`btn ${warningMode ? 'btn-ghost' : 'btn-danger'}`} onClick={toggleWarningMode}>
              <Icon name="alertTriangle" size={16} />
              <span>{warningMode ? 'Cancel' : 'Send Warning'}</span>
            </button>
          )}
        </header>

        {warningSentMsg && <div className="form-success">{warningSentMsg}</div>}

        <div className="card card-padded">
          {actionsLoading && (
            <div className="chat-history-status">
              <span className="spinner spinner-accent" />
              <span>Loading activity...</span>
            </div>
          )}
          {!actionsLoading && actionsError && (
            <div className="form-error">Could not load activity: {actionsError}</div>
          )}
          {!actionsLoading && !actionsError && actions && actions.length === 0 && (
            <div className="chat-history-status">No recorded activity for this user yet.</div>
          )}
          {!actionsLoading && !actionsError && actions && actions.length > 0 && (
            <ul className="audit-timeline">
              {actions.map((item, i) => (
                <li
                  className={`audit-timeline-item${warningMode ? ' audit-timeline-item-selectable' : ''}`}
                  key={i}
                  onClick={warningMode ? () => toggleActionSelected(i) : undefined}
                >
                  {warningMode && (
                    <input
                      type="checkbox"
                      className="audit-timeline-checkbox"
                      checked={selectedActionIdx.has(i)}
                      onChange={() => toggleActionSelected(i)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  )}
                  <span className={`audit-action-badge audit-tone-${AUDIT_ACTION_TONES[item.action] || 'neutral'}`}>
                    {AUDIT_ACTION_LABELS[item.action] || item.action}
                  </span>
                  <div className="audit-timeline-body">
                    <div className="audit-timeline-details">{item.details}</div>
                    <div className="audit-timeline-time">{formatHistoryTimestamp(item.created_at)}</div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {warningMode && letter === null && (
          <div className="card card-padded warning-compose-bar">
            <span>{chosenCount} action{chosenCount === 1 ? '' : 's'} selected</span>
            <button
              type="button"
              className="btn btn-primary"
              disabled={chosenCount === 0 || generating}
              onClick={handleGenerateLetter}
            >
              {generating && <span className="spinner" />}
              {generating ? 'Drafting letter...' : 'Generate Warning Letter'}
            </button>
            {generateError && <div className="form-error">{generateError}</div>}
          </div>
        )}

        {letter !== null && (
          <div className="card card-padded warning-letter-card">
            <div className="section-heading">Warning letter (review and edit before sending)</div>
            <textarea
              className="warning-letter-editor"
              value={letter}
              onChange={(e) => setLetter(e.target.value)}
              rows={16}
            />
            {pdfError && <div className="form-error">{pdfError}</div>}
            {sendWarningError && <div className="form-error">{sendWarningError}</div>}
            <div className="warning-letter-actions">
              <button type="button" className="btn btn-ghost" onClick={handleDownloadPdf} disabled={downloadingPdf}>
                {downloadingPdf && <span className="spinner" />}
                <Icon name="printer" size={14} />
                <span>{downloadingPdf ? 'Preparing...' : 'Download PDF'}</span>
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setLetter(null)} disabled={sendingWarning}>
                Discard
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => handleSendWarning(false)} disabled={sendingWarning}>
                {sendingWarning && <span className="spinner" />}
                <span>Send Warning</span>
              </button>
              <button type="button" className="btn btn-primary" onClick={() => handleSendWarning(true)} disabled={sendingWarning}>
                {sendingWarning && <span className="spinner" />}
                <span>Send Email</span>
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="app-content">
      <header className="page-header">
        <div className="page-eyebrow">Admin</div>
        <h1 className="page-title">Audit Log</h1>
        <p className="page-subtitle">Select a user to see everything they've done in the system, step by step.</p>
      </header>

      {usersLoading && (
        <div className="chat-history-status">
          <span className="spinner spinner-accent" />
          <span>Loading accounts...</span>
        </div>
      )}
      {usersError && <div className="form-error">Could not load accounts: {usersError}</div>}

      {users && (
        <div className="card card-padded">
          <div className="admin-table-wrap">
            <table className="admin-users-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="audit-user-row" onClick={() => openUser(u)}>
                    <td>{u.name}</td>
                    <td>{u.email}</td>
                    <td><span className={`admin-role-badge admin-role-${u.role}`}>{u.role}</span></td>
                    <td>{u.is_approved ? 'Approved' : 'Pending'}</td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-ghost admin-row-btn"
                        onClick={(e) => { e.stopPropagation(); openUser(u); }}
                      >
                        View activity
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// Warnings - visible to every logged-in user (not admin-gated). Admins see
// every warning that's gone out ("Warnings Sent" - no one sends the admin a
// warning); everyone else sees just their own, from the Audit Log page's
// "Send Warning" flow.
function WarningsPage({ auth }) {
  const isAdmin = auth?.role === 'admin';
  const [warnings, setWarnings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);
  const [pdfError, setPdfError] = useState(null);

  useEffect(() => {
    const fetcher = isAdmin ? fetchSentWarnings : fetchMyWarnings;
    fetcher()
      .then(setWarnings)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [isAdmin]);

  async function handleDownload(w) {
    setDownloadingId(w.id);
    setPdfError(null);
    try {
      const data = await requestWarningPdf(w.letter);
      downloadWarningLetterPdf(data.pdf_base64);
    } catch (err) {
      setPdfError(err.message);
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <div className="app-content">
      <header className="page-header">
        <div className="page-eyebrow">{isAdmin ? 'Admin' : 'Notices'}</div>
        <h1 className="page-title">{isAdmin ? 'Warnings Sent' : 'Warnings'}</h1>
        <p className="page-subtitle">
          {isAdmin
            ? "Every formal notice your administration has issued, across all users."
            : 'Formal notices issued to your account by an administrator.'}
        </p>
      </header>

      {loading && (
        <div className="chat-history-status">
          <span className="spinner spinner-accent" />
          <span>Loading warnings...</span>
        </div>
      )}
      {!loading && error && <div className="form-error">Could not load warnings: {error}</div>}
      {!loading && !error && warnings && warnings.length === 0 && (
        <div className="card card-padded chat-history-status">
          {isAdmin ? 'No warnings have been sent yet.' : 'No warnings on your account.'}
        </div>
      )}
      {pdfError && <div className="form-error">Could not prepare PDF: {pdfError}</div>}
      {!loading && !error && warnings && warnings.length > 0 && (
        <div className="warnings-list">
          {warnings.map((w) => (
            <div className="card card-padded warning-card" key={w.id}>
              <div className="warning-card-top">
                <span className="audit-action-badge audit-tone-danger">Warning</span>
                <div className="warning-card-top-right">
                  <span className="warning-card-time">{formatHistoryTimestamp(w.created_at)}</span>
                  <button
                    type="button"
                    className="btn btn-ghost admin-row-btn"
                    onClick={() => handleDownload(w)}
                    disabled={downloadingId === w.id}
                  >
                    {downloadingId === w.id ? <span className="spinner" /> : <Icon name="printer" size={14} />}
                    <span>{downloadingId === w.id ? 'Preparing...' : 'Download PDF'}</span>
                  </button>
                </div>
              </div>
              {isAdmin && (
                <div className="warning-card-recipient">
                  To: <strong>{w.user_name}</strong> ({w.user_email})
                  {w.emailed && <span className="warning-emailed-badge">Emailed</span>}
                </div>
              )}
              <pre className="warning-letter-text">{w.letter}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chatbot widget (ADDED - new feature, everything else in this file is
// unchanged). Floating button in the bottom-right corner that opens a chat
// panel. Talks to the already-existing POST /chat endpoint in
// backend/main.py, which forwards to backend/chatbot/service.py:ask_chatbot
// (natural language -> SQL -> query -> natural language answer). That
// backend piece was not touched or built by this change - this component
// only consumes it.
// ---------------------------------------------------------------------------

const CHAT_GREETING =
  "Hi! Ask me anything about US Group's orders, e.g. \"Which sub-company had the highest profit last month?\"";

// Shared send/receive logic for both the floating ChatWidget and the full
// ChatPage tab - each keeps its own independent conversation history, this
// just avoids duplicating the request/error handling.
function useChatbot() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([{ role: 'bot', text: CHAT_GREETING }]);
  const [sending, setSending] = useState(false);

  async function handleSend(e) {
    e.preventDefault();
    const question = input.trim();
    if (!question || sending) return;

    // recent turns (excluding the greeting and pending bubbles) for follow-up context
    const history = messages
      .filter((m) => m.text && (m.role === 'user' || m.role === 'bot'))
      .slice(-6)
      .map((m) => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.text }));

    setMessages((prev) => [...prev, { role: 'user', text: question }, { role: 'bot', pending: true }]);
    setInput('');
    setSending(true);

    try {
      const data = await askChatbot(question, history);
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: 'bot',
          text: data.answer,
          sql: data.sql,
          data: data.data,
          canChart: !!data.can_chart,
          question, // used as the heading if this answer's chart gets pinned to the dashboard
        };
        return next;
      });
    } catch (err) {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { role: 'bot', text: `Sorry, something went wrong: ${err.message}` };
        return next;
      });
    } finally {
      setSending(false);
    }
  }

  function removeMessage(index) {
    setMessages((prev) => prev.filter((_, i) => i !== index));
  }

  // Fetches a chart image for a message's own "data" rows, on demand -
  // POST /chat/chart (backend/chatbot/chart_generator.py) reuses whatever
  // rows that answer already returned, so this works for any chartable
  // question, not just a fixed set of report sections.
  async function showChart(index, rows) {
    setMessages((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], chartLoading: true, chartError: null };
      return next;
    });
    try {
      const { image_base64 } = await fetchChatChart(rows);
      setMessages((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], chartLoading: false, chartImage: image_base64 };
        return next;
      });
    } catch (err) {
      setMessages((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], chartLoading: false, chartError: err.message };
        return next;
      });
    }
  }

  return { input, setInput, messages, sending, handleSend, removeMessage, showChart };
}

// Per-bubble "..." menu in the live conversation - offers Copy and Remove.
// Remove only clears the bubble from this in-memory conversation view; it
// does NOT delete the saved chat_history row (that's what History's own
// per-item Delete is for). A saved row holds one Q+A pair but renders as two
// separate bubbles here, so there's no single bubble-to-row mapping to
// safely delete against.
function ChatBubbleMenu({ text, onRemove }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      // clipboard access denied - nothing sensible to do here
    }
    setOpen(false);
  };

  const handleRemove = () => {
    setOpen(false);
    onRemove();
  };

  return (
    <div className="chat-bubble-menu" ref={menuRef}>
      <button
        type="button"
        className="chat-bubble-menu-btn"
        onClick={() => setOpen((v) => !v)}
        aria-label="Message options"
      >
        <Icon name="moreVertical" size={14} />
      </button>
      {open && (
        <div className="chat-bubble-menu-dropdown">
          <button type="button" onClick={handleCopy}>
            <Icon name="copy" size={13} />
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          <button type="button" onClick={handleRemove}>
            <Icon name="trash" size={13} />
            <span>Remove</span>
          </button>
        </div>
      )}
    </div>
  );
}

// Renders scraped-product rows (anything with an image_url) as thumbnail cards.
// Returns nothing when the answer's rows have no images, so ordinary text
// answers are unaffected.
function ChatProductCards({ rows }) {
  if (!Array.isArray(rows)) return null;
  const products = rows.filter((r) => r && r.image_url);
  if (products.length === 0) return null;
  return (
    <div className="chat-products">
      {products.slice(0, 12).map((r, i) => (
        <a
          key={i}
          className="chat-product-card"
          href={r.url || r.image_url}
          target="_blank"
          rel="noreferrer"
        >
          <img src={r.image_url} alt={r.name || 'product'} loading="lazy" />
          {r.name && <div className="chat-product-name">{r.name}</div>}
          {r.price != null && r.price !== '' && (
            <div className="chat-product-price">
              {typeof r.price === 'number' ? `$${r.price}` : r.price}
            </div>
          )}
        </a>
      ))}
    </div>
  );
}

function ChatMessage({ message, index, onRemove, onShowChart, onAddToDashboard }) {
  const isUser = message.role === 'user';
  return (
    <div className={`chat-message ${isUser ? 'chat-message-user' : 'chat-message-bot'}`}>
      <div className="chat-message-col">
        <div className="chat-bubble">
          {message.pending ? (
            <span className="spinner spinner-accent" />
          ) : (
            <>
              <ChatBubbleMenu text={message.text} onRemove={() => onRemove(index)} />
              <p className="chat-bubble-text">{message.text}</p>
              {/* sql/data are optional debug context returned by ask_chatbot -
                  shown collapsed so the primary answer stays the focus */}
              {message.sql && (
                <details className="chat-bubble-details">
                  <summary>View generated SQL</summary>
                  <pre>{message.sql}</pre>
                </details>
              )}
            </>
          )}
        </div>

        {/* product cards: rendered when the answer's rows carry image_url
            (e.g. scraped_products results) so "show me the product" shows
            actual thumbnails instead of a raw URL */}
        {!isUser && !message.pending && <ChatProductCards rows={message.data} />}

        {!isUser && message.canChart && !message.chartImage && (
          <button
            type="button"
            className="chat-chart-btn"
            onClick={() => onShowChart(index, message.data)}
            disabled={message.chartLoading}
          >
            {message.chartLoading ? (
              <>
                <span className="spinner spinner-accent" />
                <span>Generating chart...</span>
              </>
            ) : (
              <span>📊 Show as chart</span>
            )}
          </button>
        )}

        {!isUser && message.chartError && (
          <div className="chat-chart-error">Could not build chart: {message.chartError}</div>
        )}

        {!isUser && message.chartImage && (
          <>
            <div className="chat-bubble chat-chart-bubble">
              <img
                className="chat-chart-image"
                src={`data:image/png;base64,${message.chartImage}`}
                alt="Chart for this answer"
              />
            </div>
            <div className="chat-chart-actions">
              <ChatDashboardPinButton
                heading={message.question}
                explanation={message.text}
                image={message.chartImage}
                onAdd={onAddToDashboard}
              />
              <ChatSaveAsPdfButton
                heading={message.question}
                explanation={message.text}
                image={message.chartImage}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// Sends a generated chart (+ the question that produced it, as a heading,
// and the chat answer, as a short explanation) to the Dashboard page, where
// it shows up as its own pinned card (see PinnedChartCard).
function ChatDashboardPinButton({ heading, explanation, image, onAdd }) {
  const [added, setAdded] = useState(false);

  function handleClick() {
    onAdd({ id: `${Date.now()}-${Math.random()}`, heading: heading || 'Chart', explanation, image });
    setAdded(true);
  }

  return (
    <button type="button" className="chat-chart-btn" onClick={handleClick} disabled={added}>
      {added ? (
        <>
          <Icon name="checkCircle" size={13} />
          <span>Added to Dashboard</span>
        </>
      ) : (
        <>
          <Icon name="dashboard" size={13} />
          <span>Add to Dashboard</span>
        </>
      )}
    </button>
  );
}

// Exports just this one chart (+ the question/answer that produced it) as a
// standalone PDF, via the same POST /report/custom endpoint the dashboard's
// "Print Report" panel uses - just with a single-item list.
function ChatSaveAsPdfButton({ heading, explanation, image }) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  async function handleClick() {
    setGenerating(true);
    setError(null);
    try {
      const { pdf_base64 } = await generateCustomReport([
        { question: heading || 'Chart', answer: explanation, chart_image_base64: image },
      ]);
      downloadCustomReportPdf(pdf_base64);
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <>
      <button type="button" className="chat-chart-btn" onClick={handleClick} disabled={generating}>
        {generating ? (
          <>
            <span className="spinner spinner-accent" />
            <span>Generating PDF...</span>
          </>
        ) : (
          <>
            <Icon name="printer" size={13} />
            <span>Save as PDF</span>
          </>
        )}
      </button>
      {error && <div className="chat-chart-error">Could not generate PDF: {error}</div>}
    </>
  );
}

function formatHistoryTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const datePart = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  const timePart = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  return `${datePart}, ${timePart}`;
}

// Per-item "..." menu on a history entry - offers Copy (question + answer to
// the clipboard) and Delete (calls DELETE /chat/history/:id, then asks the
// parent to drop it from state via onDelete).
function ChatHistoryItemMenu({ item, onDelete }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(`Q: ${item.question}\nA: ${item.answer}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      // clipboard access denied - nothing sensible to do here
    }
    setOpen(false);
  };

  const handleDelete = async () => {
    setOpen(false);
    try {
      await deleteChatHistoryItem(item.id);
      onDelete(item.id);
    } catch (err) {
      console.error('Failed to delete history item:', err.message);
    }
  };

  return (
    <div className="chat-history-menu" ref={menuRef}>
      <button
        type="button"
        className="chat-history-menu-btn"
        onClick={() => setOpen((v) => !v)}
        aria-label="More options"
      >
        <Icon name="moreVertical" size={16} />
      </button>
      {open && (
        <div className="chat-history-menu-dropdown">
          <button type="button" onClick={handleCopy}>
            <Icon name="copy" size={14} />
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          <button type="button" className="chat-history-menu-danger" onClick={handleDelete}>
            <Icon name="trash" size={14} />
            <span>Delete</span>
          </button>
        </div>
      )}
    </div>
  );
}

// Read-only past-conversation list shown inside the chat widget when its
// header history toggle is on. Fetches fresh every time it's opened so it
// reflects questions asked since the last time it was viewed.
function ChatHistoryView({ loading, error, items, onDelete }) {
  return (
    <div className="chat-panel-body">
      {loading && (
        <div className="chat-history-status">
          <span className="spinner spinner-accent" />
          <span>Loading history...</span>
        </div>
      )}
      {!loading && error && (
        <div className="chat-history-status chat-history-error">Could not load history: {error}</div>
      )}
      {!loading && !error && items && items.length === 0 && (
        <div className="chat-history-status">No previous questions yet.</div>
      )}
      {!loading && !error && items && items.length > 0 && (
        <ul className="chat-history-list">
          {items.map((item, i) => (
            <li className="chat-history-item" key={item.id ?? `${item.created_at}-${i}`}>
              <div className="chat-history-item-top">
                <div className="chat-history-question">{item.question}</div>
                <ChatHistoryItemMenu item={item} onDelete={onDelete} />
              </div>
              <div className="chat-history-answer">{item.answer}</div>
              <div className="chat-history-time">
                {formatHistoryTimestamp(item.created_at)}
                {item.user_name && ` · asked by ${item.user_name}`}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ChatWidget({ onAddToDashboard }) {
  const [open, setOpen] = useState(false);
  const [view, setView] = useState('chat'); // 'chat' | 'history'
  const [history, setHistory] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState(null);
  const { input, setInput, messages, sending, handleSend, removeMessage, showChart } = useChatbot();

  useEffect(() => {
    if (view !== 'history') return undefined;
    let cancelled = false;
    setHistoryLoading(true);
    setHistoryError(null);
    fetchChatHistory()
      .then((data) => {
        if (!cancelled) setHistory(data);
      })
      .catch((err) => {
        if (!cancelled) setHistoryError(err.message);
      })
      .finally(() => {
        if (!cancelled) setHistoryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [view]);

  const handleHistoryDelete = (id) => {
    setHistory((prev) => (prev ? prev.filter((item) => item.id !== id) : prev));
  };

  return (
    <>
      {open && (
        <div className="chat-panel card">
          <div className="chat-panel-header">
            <div className="chat-panel-title">
              <Icon name="message" size={16} />
              <span>{view === 'history' ? 'History' : 'Ask US Group'}</span>
            </div>
            <div className="chat-panel-header-actions">
              <button
                className="chat-panel-icon-btn"
                onClick={() => setView((v) => (v === 'chat' ? 'history' : 'chat'))}
                aria-label={view === 'chat' ? 'View history' : 'Back to chat'}
              >
                <Icon name={view === 'chat' ? 'clock' : 'arrowLeft'} size={16} />
              </button>
              <button className="chat-panel-close" onClick={() => setOpen(false)} aria-label="Close chat">
                <Icon name="close" size={16} />
              </button>
            </div>
          </div>

          {view === 'chat' ? (
            <>
              <div className="chat-panel-body">
                {messages.map((m, i) => (
                  <ChatMessage
                    message={m}
                    index={i}
                    onRemove={removeMessage}
                    onShowChart={showChart}
                    onAddToDashboard={onAddToDashboard}
                    key={i}
                  />
                ))}
              </div>

              <form className="chat-panel-footer" onSubmit={handleSend}>
                <input
                  type="text"
                  placeholder="Ask a question..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={sending}
                />
                <button type="submit" className="chat-send-btn" disabled={sending || !input.trim()} aria-label="Send">
                  <Icon name="send" size={16} />
                </button>
              </form>
            </>
          ) : (
            <ChatHistoryView
              loading={historyLoading}
              error={historyError}
              items={history}
              onDelete={handleHistoryDelete}
            />
          )}
        </div>
      )}

      <button className="chat-fab" onClick={() => setOpen((v) => !v)} aria-label="Toggle chat">
        <Icon name={open ? 'close' : 'message'} size={22} />
      </button>
    </>
  );
}

// Full-page version of the same assistant, reachable from the sidebar - the
// floating ChatWidget above stays in place too, this is just a second way
// in with more room to read longer answers. Independent conversation
// history from the widget (see useChatbot).
function ChatPage({ onAddToDashboard }) {
  const { input, setInput, messages, sending, handleSend, removeMessage, showChart } = useChatbot();
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState(null);

  // Only loads once the History panel is opened, then refreshes right
  // after each question finishes sending while it stays open.
  useEffect(() => {
    if (!showHistory || sending) return undefined;
    let cancelled = false;
    setHistoryLoading(true);
    setHistoryError(null);
    fetchChatHistory()
      .then((data) => {
        if (!cancelled) setHistory(data);
      })
      .catch((err) => {
        if (!cancelled) setHistoryError(err.message);
      })
      .finally(() => {
        if (!cancelled) setHistoryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [showHistory, sending]);

  const handleHistoryDelete = (id) => {
    setHistory((prev) => (prev ? prev.filter((item) => item.id !== id) : prev));
  };

  return (
    <div className="app-content chat-page-content">
      <header className="page-header chat-page-header">
        <div>
          <div className="page-eyebrow">Assistant</div>
          <h1 className="page-title">Ask US Group</h1>
          <p className="page-subtitle">
            Ask questions about orders, profitability, and payment performance in plain English.
          </p>
        </div>
        <button className="btn chat-history-toggle" onClick={() => setShowHistory((v) => !v)}>
          <Icon name="clock" size={15} />
          {showHistory ? 'Hide History' : 'History'}
        </button>
      </header>

      <div className="chat-page-layout">
        <div className="card chat-page-card">
          <div className="chat-panel-body">
            {messages.map((m, i) => (
              <ChatMessage
                message={m}
                index={i}
                onRemove={removeMessage}
                onShowChart={showChart}
                onAddToDashboard={onAddToDashboard}
                key={i}
              />
            ))}
          </div>

          <form className="chat-panel-footer" onSubmit={handleSend}>
            <input
              type="text"
              placeholder="Ask a question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={sending}
            />
            <button type="submit" className="chat-send-btn" disabled={sending || !input.trim()} aria-label="Send">
              <Icon name="send" size={16} />
            </button>
          </form>
        </div>

        {showHistory && (
          <div className="card chat-page-history">
            <div className="chat-panel-header">
              <div className="chat-panel-title">
                <Icon name="clock" size={16} />
                <span>History</span>
              </div>
            </div>
            <ChatHistoryView
              loading={historyLoading}
              error={historyError}
              items={history}
              onDelete={handleHistoryDelete}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

// Live clock pinned to the top-right corner of every page. Updates each second.
function LiveClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const date = now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
  return (
    <div className="live-clock" title={now.toString()}>
      <Icon name="clock" size={14} />
      <span className="live-clock-time">{time}</span>
      <span className="live-clock-date">{date}</span>
    </div>
  );
}

function App() {
  const [auth, setAuth] = useState(() => getStoredAuth()); // { token, name, role, email } | null
  const [page, setPage] = useState('dashboard');
  const [options, setOptions] = useState({});
  const [optionsError, setOptionsError] = useState(null);
  // Charts pinned from the chat widget (see ChatDashboardPinButton), shown
  // on the Dashboard page. Persisted to sessionStorage so they survive a
  // page refresh, but reset when the tab closes.
  const [pinnedCharts, setPinnedCharts] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem(PINNED_CHARTS_STORAGE_KEY)) || [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    if (!auth) return;
    fetchOptions()
      .then(setOptions)
      .catch((err) => setOptionsError(err.message));
  }, [auth]);

  useEffect(() => {
    try {
      sessionStorage.setItem(PINNED_CHARTS_STORAGE_KEY, JSON.stringify(pinnedCharts));
    } catch {
      // sessionStorage full (chart images are base64 PNGs) or unavailable -
      // pinned charts just won't survive a refresh in that case
    }
  }, [pinnedCharts]);

  function handleLoginSuccess(authData) {
    setStoredAuth(authData);
    setAuth(authData);
  }

  function handleLogout() {
    clearStoredAuth();
    setAuth(null);
    setPage('dashboard');
  }

  function addPinnedChart(chart) {
    setPinnedCharts((prev) => [chart, ...prev]);
  }

  function removePinnedChart(id) {
    setPinnedCharts((prev) => prev.filter((c) => c.id !== id));
  }

  if (!auth) {
    return <LoginSignupPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="app-shell">
      <LiveClock />
      <Sidebar page={page} onNavigate={setPage} onLogout={handleLogout} role={auth.role} />
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        {optionsError && (
          <div className="api-warning">
            Could not reach the backend ({optionsError}). Make sure it's running with <code>uvicorn main:app --reload</code>.
          </div>
        )}
        {page === 'dashboard' && (
          <DashboardPage onNavigate={setPage} pinnedCharts={pinnedCharts} onRemovePinnedChart={removePinnedChart} />
        )}
        {page === 'profitability' && (
          <PredictorPage
            options={options}
            title="Profitability Predictor"
            subtitle="Enter the order details below to estimate whether it will be profitable."
            submitLabel="Predict Profitability"
            negativeTone="danger"
            predictFn={predictProfitability}
          />
        )}
        {page === 'payment-delay' && (
          <PredictorPage
            options={options}
            title="Payment Delay Predictor"
            subtitle="Enter the order details below to estimate whether this customer is likely to pay late."
            submitLabel="Predict Payment Delay"
            negativeTone="warning"
            predictFn={predictPaymentDelay}
          />
        )}
        {page === 'chat' && <ChatPage onAddToDashboard={addPinnedChart} />}
        {page === 'blog' && <BlogPage />}
        {page === 'scraper' && <ScraperPage />}
        {page === 'warnings' && <WarningsPage auth={auth} />}
        {page === 'admin' && auth.role === 'admin' && <AdminPage auth={auth} />}
        {page === 'audit-log' && auth.role === 'admin' && <AuditLogPage auth={auth} />}
      </div>
      {/* added: floating chat widget, rendered at the App level so it's available on every page */}
      <ChatWidget onAddToDashboard={addPinnedChart} />
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
