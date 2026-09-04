import React, { useEffect, useMemo, useState } from 'react';

type Product = {
  id: number;
  name: string;
  description: string;
  price: number;
  stock: number;
  category: string;
  image_url?: string | null;
};

type Message = {
  from: 'you' | 'agent';
  text: string;
};

type AgentResponse = {
  message: string;
  status: string;
  reasoning: string;
  guardrail_status: string;
  proposed_amount?: number;
  product_id?: number;
  candidates_considered?: Array<{
    name?: string;
    category?: string;
    price?: number;
    reason?: string;
  }>;
};

type CheckoutResult = {
  success: boolean;
  status: string;
  message: string;
  reasoning: string;
  bounds_passed: boolean;
  payment_url?: string | null;
  retry_available?: boolean;
};

type AuditEvent = {
  id: number;
  action_type: string;
  reasoning: string;
  amount?: number;
  bounds_passed: boolean;
  candidates_considered?: Array<{
    name?: string;
    category?: string;
    price?: number;
    reason?: string;
  }>;
  outcome?: string;
  timestamp: string;
};

type AuditSummary = {
  actions_today: number;
  orders_approved: number;
  total_value: number;
  session_total_spend: number;
  session_total_cap: number;
  session_remaining: number;
  guardrail_pass_rate: number;
  failed_payments: number;
};

type OrderStatus = {
  id: string;
  productName: string;
  amount: number;
  status: 'Confirmed' | 'Packed' | 'Dispatched' | 'Delivered';
  eta: string;
};

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';
const SESSION_ID = 'demo-session';

const productEmoji: Record<string, string> = {
  moisturizer: '🫧',
  sunscreen: '☀️',
  serum: '✨',
  cleanser: '🧼',
  facewash: '💧',
  mist: '🌿',
  default: '🌸',
};

const styles = `
  :root {
    --bg: #f6f1ea;
    --panel: #fffdf9;
    --card: #f2ebdf;
    --ink: #1d2d2a;
    --muted: #5f6d69;
    --green: #145c4f;
    --green-soft: #dfeee7;
    --orange: #ef865d;
    --orange-soft: #ffe2d1;
    --red: #bf4f43;
    --red-soft: #fbe1de;
    --gold: #e5c36d;
    --border: #d7cbb7;
  }

  * { box-sizing: border-box; }
  html, body, #root { margin: 0; min-height: 100%; font-family: Inter, Segoe UI, sans-serif; background: var(--bg); color: var(--ink); }
  body { min-height: 100vh; }
  button, input, textarea { font: inherit; }
  a { color: inherit; text-decoration: none; }
  .app-shell { min-height: 100vh; }
  .topbar { display: flex; justify-content: space-between; align-items: center; padding: 18px 32px; border-bottom: 1px solid var(--border); background: rgba(246, 241, 234, 0.9); position: sticky; top: 0; z-index: 5; backdrop-filter: blur(10px); }
  .brand { display: flex; align-items: center; gap: 12px; font-weight: 800; letter-spacing: 0.18em; text-transform: uppercase; }
  .brand-mark { width: 32px; height: 32px; border-radius: 50%; background: var(--green); color: white; display: grid; place-items: center; font-size: 18px; }
  .nav { display: flex; gap: 10px; }
  .nav-button { border: 1px solid transparent; background: transparent; color: var(--muted); border-radius: 999px; padding: 10px 16px; cursor: pointer; font-weight: 700; transition: all 0.2s ease; }
  .nav-button:hover { background: rgba(20,92,79,0.06); transform: translateY(-1px); }
  .nav-button.active { background: var(--green-soft); color: var(--green); border-color: #cfe5d7; }
  .content { max-width: 1200px; margin: 0 auto; padding: 28px 20px 48px; }
  .hero { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 24px; padding: 34px 0 26px; }
  .hero-card, .panel, .catalog-card, .message-box, .audit-card { background: var(--panel); border: 1px solid var(--border); border-radius: 22px; box-shadow: 0 8px 24px rgba(15, 25, 23, 0.04); }
  .hero-card { padding: 28px; background: linear-gradient(135deg, var(--green), #0a3330); color: #eef7f0; }
  .eyebrow { letter-spacing: 0.18em; text-transform: uppercase; font-size: 11px; color: #d4e8dc; font-weight: 700; }
  h1 { font-size: clamp(2.7rem, 6vw, 5rem); margin: 18px 0; line-height: 0.96; letter-spacing: -0.08em; }
  .hero-card p { color: #d9e9e1; margin: 0 0 26px; max-width: 560px; line-height: 1.7; }
  .cta-row { display: flex; gap: 12px; flex-wrap: wrap; }
  .primary-button, .secondary-button, .ghost-button { cursor: pointer; border: none; border-radius: 999px; font-weight: 800; padding: 12px 18px; transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease; }
  .primary-button:hover, .secondary-button:hover, .ghost-button:hover, .ask-button:hover, .send-button:hover { transform: translateY(-1px); }
  .primary-button { background: var(--orange); color: #3c1e17; box-shadow: 0 10px 20px rgba(239, 134, 93, 0.22); }
  .secondary-button { background: var(--green-soft); color: var(--green); }
  .ghost-button { background: transparent; border: 1px solid var(--border); color: var(--ink); }
  .mini-panel { padding: 20px; display: flex; flex-direction: column; gap: 18px; }
  .action-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
  .chip { border: 1px solid var(--border); background: #f9f5ef; color: var(--ink); border-radius: 999px; padding: 8px 12px; cursor: pointer; font-size: 0.8rem; }
  .chip:hover { background: var(--green-soft); border-color: #bfd7cc; }
  .mini-panel .header { display: flex; justify-content: space-between; align-items: center; font-weight: 700; }
  .status-pill { border-radius: 999px; background: rgba(229, 195, 109, 0.18); color: #8d6b19; padding: 6px 10px; font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; }
  .hero-quote { font-size: 1.1rem; line-height: 1.6; font-weight: 600; }
  .section-header { margin: 28px 0 18px; display: flex; justify-content: space-between; align-items: end; gap: 12px; }
  .section-header h2 { margin: 0; font-size: clamp(2rem, 3vw, 3rem); letter-spacing: -0.06em; }
  .section-header p { margin: 0; color: var(--muted); max-width: 540px; }
  .catalog-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; }
  .catalog-card { padding: 14px; transition: transform 0.2s ease, box-shadow 0.2s ease; }
  .catalog-card:hover { transform: translateY(-2px); box-shadow: 0 16px 30px rgba(18, 32, 30, 0.08); }
  .art-card { min-height: 180px; border-radius: 18px; background: linear-gradient(135deg, #e6d6c2, #f6efe7); display: flex; align-items: center; justify-content: center; font-size: 3rem; color: var(--green); }
  .catalog-meta { display: flex; justify-content: space-between; align-items: start; gap: 8px; margin-top: 14px; }
  .category-tag { font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--muted); }
  .price { font-weight: 900; font-size: 1.2rem; }
  .catalog-card h3 { margin: 8px 0 12px; font-size: 1.2rem; }
  .catalog-card p { color: var(--muted); line-height: 1.6; margin: 0 0 16px; }
  .card-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
  .ask-button { background: var(--green-soft); color: var(--green); border: 0; border-radius: 999px; padding: 10px 14px; font-weight: 700; cursor: pointer; transition: transform 0.2s ease, opacity 0.2s ease; }
  .layout-grid { display: grid; grid-template-columns: 1.3fr 0.7fr; gap: 22px; margin-top: 18px; }
  .agent-panel { padding: 22px; }
  .message-list { display: flex; flex-direction: column; gap: 12px; min-height: 260px; }
  .message { max-width: 80%; padding: 12px 14px; border-radius: 16px; line-height: 1.6; }
  .message.you { margin-left: auto; background: var(--green); color: white; }
  .message.agent { background: #f2efe8; border: 1px solid var(--border); }
  .composer { display: flex; gap: 12px; margin-top: 18px; }
  .composer textarea { flex: 1; min-height: 68px; border-radius: 16px; border: 1px solid var(--border); background: #f9f3ea; padding: 12px 14px; resize: vertical; }
  .composer textarea:focus { outline: 2px solid rgba(20,92,79,0.16); border-color: rgba(20,92,79,0.4); }
  .send-button { width: 54px; height: 54px; border: none; border-radius: 50%; background: var(--orange); color: #341a14; font-weight: 900; cursor: pointer; box-shadow: 0 8px 18px rgba(239, 134, 93, 0.22); }
  .side-panel { padding: 22px; }
  .guardrail-box { background: linear-gradient(180deg, #103f37, #0b2d2c); color: white; border-radius: 18px; padding: 18px; }
  .guardrail-row { display: flex; justify-content: space-between; gap: 8px; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.08); }
  .guardrail-row:last-child { border-bottom: 0; }
  .recommendation-card { margin-top: 18px; background: #edf5f1; border: 1px solid #bfd4c9; border-radius: 16px; padding: 18px; }
  .recommendation-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .reasoning-box { background: rgba(255,255,255,0.4); border: 1px solid #c9ddd3; border-radius: 12px; padding: 12px; margin-top: 12px; }
  .checkout-box { margin-top: 18px; padding: 18px; border-radius: 16px; border: 1px solid var(--border); }
  .checkout-box.success { background: #eaf4ee; border-color: #c9ddd2; }
  .checkout-box.fail { background: #fce9e5; border-color: #f0c2b9; }
  .payment-sheet { margin-top: 18px; padding: 18px; border: 1px solid var(--border); border-radius: 18px; background: linear-gradient(180deg, #ffffff, #f8f2ea); }
  .payment-header { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 14px; }
  .payment-methods { display: flex; gap: 8px; margin-bottom: 14px; }
  .payment-mode { flex: 1; border: 1px solid var(--border); background: white; border-radius: 12px; padding: 10px 12px; font-weight: 700; cursor: pointer; }
  .payment-mode.active { background: var(--green-soft); border-color: #cfe4d6; color: var(--green); }
  .payment-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .input-group { display: flex; flex-direction: column; gap: 7px; font-size: 0.8rem; color: var(--muted); }
  .input-group input { width: 100%; border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; background: #fcfaf7; font-size: 0.95rem; }
  .payment-summary { display: flex; justify-content: space-between; align-items: end; margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--border); }
  .summary-meta { font-size: 0.8rem; color: var(--muted); }
  .audit-summary { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 14px; margin: 20px 0 28px; }
  .metric-card { padding: 18px; }
  .metric-card h4 { margin: 10px 0 14px; color: var(--muted); font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; }
  .metric-value { font-size: clamp(1.8rem, 3vw, 2.6rem); font-weight: 900; letter-spacing: -0.06em; }
  .audit-shell { display: grid; gap: 20px; }
  .audit-header { display: flex; align-items: end; justify-content: space-between; gap: 12px; margin-top: 8px; }
  .audit-layout { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(260px, 0.7fr); gap: 18px; }
  .audit-list { display: flex; flex-direction: column; gap: 12px; }
  .audit-item { display: grid; grid-template-columns: 1.2fr 0.9fr 1.4fr 0.7fr; gap: 12px; align-items: start; padding: 14px 16px; border: 1px solid var(--border); border-radius: 14px; background: var(--panel); }
  .audit-item strong { display: block; margin-bottom: 6px; }
  .muted { color: var(--muted); }
  .badge { display: inline-block; border-radius: 999px; padding: 5px 10px; font-size: 11px; font-weight: 800; }
  .badge.pass { background: #dff0e6; color: #145c4f; }
  .badge.fail { background: #f9e5e1; color: #9e403a; }
  .audit-panel { padding: 20px; }
  .audit-filter-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .audit-filter { border: 1px solid var(--border); background: #f5efe8; color: var(--ink); border-radius: 999px; padding: 8px 12px; font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; cursor: pointer; }
  .audit-filter.active { background: var(--green-soft); border-color: #cfe4d6; color: var(--green); }
  .audit-side-box { align-self: start; background: linear-gradient(180deg, #103f37, #0b2d2c); color: white; border-radius: 18px; padding: 18px; }
  .audit-side-box .row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.08); }
  .audit-side-box .row:last-child { border-bottom: 0; }
  @media (max-width: 840px) {
    .hero, .layout-grid, .audit-layout { grid-template-columns: 1fr; }
    .audit-summary { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
    .audit-item { grid-template-columns: 1fr; }
    .topbar { padding: 14px 18px; }
    .nav { display: none; }
  }
`;

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Request failed');
  }

  return response.json() as Promise<T>;
}

function App() {
  const [view, setView] = useState<'store' | 'agent' | 'audit' | 'saved' | 'profile'>('store');
  const [catalog, setCatalog] = useState<Product[]>([]);
  const [savedItems, setSavedItems] = useState<Product[]>([]);
  const [savingProductId, setSavingProductId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [agentResponse, setAgentResponse] = useState<AgentResponse | null>(null);
  const [checkoutResult, setCheckoutResult] = useState<CheckoutResult | null>(null);
  const [order, setOrder] = useState<OrderStatus | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [loadingCatalog, setLoadingCatalog] = useState(true);
  const [loadingAgent, setLoadingAgent] = useState(false);
  const [loadingCheckout, setLoadingCheckout] = useState(false);
  const [loadingAudit, setLoadingAudit] = useState(true);
  const [auditFilter, setAuditFilter] = useState<'all' | 'pass' | 'fail'>('all');
  const [paymentMethod, setPaymentMethod] = useState<'card' | 'upi'>('card');
  const [paymentForm, setPaymentForm] = useState({
    cardName: 'Aarav Sharma',
    cardNumber: '4242 4242 4242 4242',
    expiry: '12/29',
    cvv: '123',
  });

  const loadCatalog = async () => {
    try {
      setLoadingCatalog(true);
      const data = await fetchJson<Product[]>(`${API_BASE}/catalog`);
      setCatalog(data);
    } catch (error) {
      console.error(error);
      setCatalog([]);
    } finally {
      setLoadingCatalog(false);
    }
  };

  const loadSavedItems = async () => {
    try {
      const data = await fetchJson<Product[]>(`${API_BASE}/saved?session_id=${SESSION_ID}`);
      setSavedItems(data);
    } catch (error) {
      console.error(error);
      setSavedItems([]);
    }
  };

  const loadAudit = async () => {
    try {
      setLoadingAudit(true);
      const [events, summaryData] = await Promise.all([
        fetchJson<AuditEvent[]>(`${API_BASE}/audit/log`),
        fetchJson<AuditSummary>(`${API_BASE}/audit/summary`),
      ]);
      setAuditEvents(events);
      setSummary(summaryData);
    } catch (error) {
      console.error(error);
      setAuditEvents([]);
      setSummary({
        actions_today: 0,
        orders_approved: 0,
        total_value: 0,
        session_total_spend: 0,
        session_total_cap: 9000,
        session_remaining: 9000,
        guardrail_pass_rate: 0,
        failed_payments: 0,
      });
    } finally {
      setLoadingAudit(false);
    }
  };

  useEffect(() => { void loadCatalog(); }, []);
  useEffect(() => { void loadSavedItems(); }, []);
  useEffect(() => { void loadAudit(); }, []);

  const sendMessage = async (promptOverride?: string) => {
    const trimmed = (promptOverride ?? input).trim();
    if (!trimmed || loadingAgent) return;

    setMessages((current) => [...current, { from: 'you', text: trimmed }]);
    setInput('');
    setLoadingAgent(true);

    try {
      const response = await fetchJson<AgentResponse>(`${API_BASE}/agent`, {
        method: 'POST',
        body: JSON.stringify({ message: trimmed }),
      });
      setAgentResponse(response);
      setMessages((current) => [...current, { from: 'agent', text: response.message }]);
      setCheckoutResult(null);
      setView('agent');
    } catch (error) {
      console.error(error);
      const fallback = 'I could not complete that recommendation. Please try a simpler request.';
      setMessages((current) => [...current, { from: 'agent', text: fallback }]);
    } finally {
      setLoadingAgent(false);
    }
  };

  const checkout = async (productId: number, amount: number, simulateFailure = false) => {
    setLoadingCheckout(true);
    try {
      const result = await fetchJson<CheckoutResult>(`${API_BASE}/checkout`, {
        method: 'POST',
        body: JSON.stringify({
          product_id: productId,
          amount,
          session_id: 'demo-session',
          simulate_failure: simulateFailure,
        }),
      });
      setCheckoutResult(result);
      if (result.success && recommendedProduct) {
        setOrder({
          id: `AP-${Date.now().toString().slice(-6)}`,
          productName: recommendedProduct.name,
          amount: amount,
          status: 'Confirmed',
          eta: '2-3 days',
        });
      } else {
        setOrder(null);
      }
      await loadAudit();
    } catch (error) {
      console.error(error);
      setCheckoutResult({
        success: false,
        status: 'error',
        message: 'The checkout could not be completed right now.',
        reasoning: 'The backend rejected the request unexpectedly.',
        bounds_passed: false,
        retry_available: false,
      });
    } finally {
      setLoadingCheckout(false);
    }
  };

  const recommendedProduct = useMemo(() => {
    if (!agentResponse?.product_id) return null;
    return catalog.find((product) => product.id === agentResponse.product_id) ?? null;
  }, [agentResponse, catalog]);

  const toggleSavedItem = async (product: Product) => {
    if (savingProductId === product.id) return;

    const exists = savedItems.some((item) => item.id === product.id);
    setSavingProductId(product.id);
    try {
      if (exists) {
        await fetchJson<{ success: boolean }>(`${API_BASE}/saved/${product.id}?session_id=${SESSION_ID}`, {
          method: 'DELETE',
        });
        setSavedItems((current) => current.filter((item) => item.id !== product.id));
      } else {
        const saved = await fetchJson<Product>(`${API_BASE}/saved`, {
          method: 'POST',
          body: JSON.stringify({ product_id: product.id, session_id: SESSION_ID }),
        });
        setSavedItems((current) => current.some((item) => item.id === saved.id) ? current : [...current, saved]);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setSavingProductId(null);
    }
  };

  const amountToPay = agentResponse?.proposed_amount ?? recommendedProduct?.price ?? 0;

  const filteredAuditEvents = useMemo(() => {
    if (auditFilter === 'all') return auditEvents;
    return auditEvents.filter((event) => {
      if (auditFilter === 'pass') return event.bounds_passed;
      return !event.bounds_passed;
    });
  }, [auditEvents, auditFilter]);

  function OrderTrackingCard({ order }: { order: OrderStatus | null }) {
    if (!order) return null;

    const steps = [
      { label: 'Confirmed', done: true },
      { label: 'Packed', done: order.status !== 'Confirmed' },
      { label: 'Dispatched', done: order.status === 'Dispatched' || order.status === 'Delivered' },
      { label: 'Delivered', done: order.status === 'Delivered' },
    ];

    return (
      <div className="recommendation-card" style={{ marginTop: 18, background: '#eef7f4', borderColor: '#bfd7cc' }}>
        <div className="recommendation-top">
          <strong>Order confirmed</strong>
          <span className="badge pass">{order.id}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginTop: 12, flexWrap: 'wrap' }}>
          <div>
            <div className="muted">Item</div>
            <strong>{order.productName}</strong>
          </div>
          <div>
            <div className="muted">Amount</div>
            <strong>₹{order.amount}</strong>
          </div>
          <div>
            <div className="muted">ETA</div>
            <strong>{order.eta}</strong>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 10, marginTop: 18 }}>
          {steps.map((step) => (
            <div key={step.label} style={{ padding: '10px 8px', borderRadius: 12, textAlign: 'center', background: step.done ? '#dff0e6' : '#f5efe8', border: `1px solid ${step.done ? '#bfd7cc' : '#d7cbb7'}` }}>
              <div style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: step.done ? '#145c4f' : '#69746e' }}>{step.label}</div>
              <div style={{ fontSize: 12, marginTop: 6, fontWeight: 800, color: step.done ? '#145c4f' : '#69746e' }}>{step.done ? 'Done' : 'Next'}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  function ExplainabilityPanel({ response, product }: { response: AgentResponse; product: Product | null }) {
    const passed = /pass|allow/i.test(response.guardrail_status || '');
    const checks = [
      { label: 'Use-case fit', value: product ? `Matches ${product.category} intent` : 'Category match found' },
      { label: 'Budget fit', value: response.proposed_amount ? `Within ${new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(response.proposed_amount)}` : 'Inside the session range' },
      { label: 'Stock safety', value: product ? `${product.stock} units available` : 'Inventory checked' },
      { label: 'Guardrail status', value: passed ? 'Allowed to continue' : 'Needs review' },
    ];

    return (
      <div className="recommendation-card" style={{ marginTop: 18, background: '#f8f5ee', borderColor: '#d7cbb7' }}>
        <div className="recommendation-top">
          <strong>Explainability panel</strong>
          <span className={`badge ${passed ? 'pass' : 'fail'}`}>{passed ? 'safe' : 'review'}</span>
        </div>
        <div style={{ display: 'grid', gap: 10 }}>
          {checks.map((check) => (
            <div key={check.label} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, padding: '10px 12px', borderRadius: 12, background: 'rgba(255,255,255,0.5)', border: '1px solid #e1d7c4' }}>
              <span className="muted" style={{ color: '#557067' }}>{check.label}</span>
              <strong>{check.value}</strong>
            </div>
          ))}
        </div>
        <div className="reasoning-box" style={{ marginTop: 16 }}>
          <strong>Checkout conversation:</strong> Nila compared the offer to the requested use case, the spend limit, and current inventory before asking for approval.
        </div>
      </div>
    );
  }

  return (
    <>
      <style>{styles}</style>
      <div className="app-shell">
        <header className="topbar">
          <div className="brand">
            <div className="brand-mark">A</div>
            <span>AuditPay</span>
          </div>
          <nav className="nav">
            <button className={`nav-button ${view === 'store' ? 'active' : ''}`} onClick={() => setView('store')}>Storefront</button>
            <button className={`nav-button ${view === 'agent' ? 'active' : ''}`} onClick={() => setView('agent')}>Agent</button>
            <button className={`nav-button ${view === 'saved' ? 'active' : ''}`} onClick={() => setView('saved')}>Saved</button>
            <button className={`nav-button ${view === 'profile' ? 'active' : ''}`} onClick={() => setView('profile')}>Profile</button>
            <button className={`nav-button ${view === 'audit' ? 'active' : ''}`} onClick={() => setView('audit')}>Audit</button>
          </nav>
        </header>

        <main className="content">
          {view === 'store' && (
            <>
              <section className="hero">
                <div className="hero-card">
                  <div className="eyebrow">AI commerce demo</div>
                  <h1>Buy less. Choose well.</h1>
                  <p>
                    Browse the catalog, ask the AI shopping agent for a recommendation, and review every purchase decision with an explainable audit trail before a single payment is attempted.
                  </p>
                  <div className="cta-row">
                    <button className="primary-button" onClick={() => setView('agent')}>Ask the agent</button>
                    <button className="secondary-button" onClick={() => setView('audit')}>View audit log</button>
                  </div>
                </div>

                <div className="panel mini-panel">
                  <div className="header">
                    <span>Active guardrails</span>
                    <span className="status-pill">On</span>
                  </div>
                  <div className="hero-quote">“Nothing happens silently.”</div>
                  <div className="guardrail-row"><span>Max order value</span><strong>₹8,000</strong></div>
                  <div className="guardrail-row"><span>Max orders/session</span><strong>3</strong></div>
                  <div className="guardrail-row"><span>Approved categories</span><strong>Skincare</strong></div>
                </div>
              </section>

              <div className="section-header">
                <div>
                  <div className="eyebrow" style={{ color: '#a66932' }}>The considered shelf</div>
                  <h2>Skincare essentials</h2>
                </div>
                <p>Recommendations are filtered by explicit category allow-lists, price thresholds, and audited reasoning.</p>
              </div>

              <div className="catalog-grid">
                {loadingCatalog ? (
                  <div className="panel" style={{ padding: 18 }}>Loading catalog…</div>
                ) : (
                  catalog.map((product) => (
                    <article className="catalog-card" key={product.id}>
                      <div className="art-card">{productEmoji[product.category.toLowerCase()] ?? productEmoji.default}</div>
                      <div className="catalog-meta">
                        <div>
                          <div className="category-tag">{product.category}</div>
                          <h3>{product.name}</h3>
                        </div>
                        <div className="price">₹{product.price}</div>
                      </div>
                      <p>{product.description}</p>
                      <div className="card-row">
                        <span className="muted">Stock: {product.stock}</span>
                        <button className="ask-button" onClick={() => {
                          setInput(`Get me a ${product.category} product under ₹${Math.max(product.price + 200, 1000)}.`);
                          setView('agent');
                        }}>Ask agent</button>
                      </div>
                    </article>
                  ))
                )}
              </div>
            </>
          )}

          {view === 'agent' && (
            <div className="layout-grid">
              <section className="panel agent-panel">
                <div className="section-header" style={{ marginTop: 0 }}>
                  <div>
                    <div className="eyebrow" style={{ color: '#a66932' }}>Agent session</div>
                    <h2>What are we looking for?</h2>
                  </div>
                </div>

                <div className="message-list">
                  {messages.length === 0 && (
                    <div className="message agent">
                      Tell me what you need, and I’ll recommend a product with clear reasoning before any checkout is attempted.
                    </div>
                  )}
                  {messages.map((message, index) => (
                    <div key={`${message.from}-${index}`} className={`message ${message.from}`}>
                      {message.text}
                    </div>
                  ))}
                </div>

                {loadingAgent && <div className="muted" style={{ marginTop: 12 }}>Checking the catalog and guardrails…</div>}

                {agentResponse && recommendedProduct && (
                  <div className="recommendation-card">
                    <div className="recommendation-top">
                      <strong>Recommendation ready</strong>
                      <span className="badge pass">{agentResponse.guardrail_status}</span>
                    </div>
                    <div className="muted">{agentResponse.message}</div>
                    <div className="reasoning-box">
                      <strong>Why this choice:</strong><br />
                      {agentResponse.reasoning}
                    </div>
                    {agentResponse.candidates_considered && agentResponse.candidates_considered.length > 0 && (
                      <details style={{ marginTop: 12 }}>
                        <summary style={{ cursor: 'pointer', color: '#145c4f', fontWeight: 700 }}>Other options considered</summary>
                        <ul style={{ margin: '8px 0 0 18px', padding: 0, color: '#425856' }}>
                          {agentResponse.candidates_considered.map((candidate, index) => (
                            <li key={`recommendation-candidate-${index}`}>
                              <strong>{candidate.name}</strong> — {candidate.reason} ({candidate.category}, ₹{candidate.price ?? 0})
                            </li>
                          ))}
                        </ul>
                      </details>
                    )}
                    <div className="card-row" style={{ marginTop: 16 }}>
                      <div className="price">₹{amountToPay}</div>
                      {recommendedProduct && (
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                          <button className="secondary-button" onClick={() => void toggleSavedItem(recommendedProduct)} disabled={loadingCheckout || savingProductId === recommendedProduct.id}>
                            {savingProductId === recommendedProduct.id ? 'Saving…' : savedItems.some((item) => item.id === recommendedProduct.id) ? 'Saved' : 'Save item'}
                          </button>
                          <button className="primary-button" onClick={() => void checkout(recommendedProduct.id, amountToPay, false)} disabled={loadingCheckout}>
                            {loadingCheckout ? 'Processing…' : 'Secure checkout'}
                          </button>
                          <button className="ghost-button" onClick={() => checkout(recommendedProduct.id, amountToPay, true)} disabled={loadingCheckout}>
                            Test decline
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {agentResponse && recommendedProduct && (
                  <ExplainabilityPanel response={agentResponse} product={recommendedProduct} />
                )}

                {recommendedProduct && !checkoutResult && (
                  <div className="payment-sheet">
                    <div className="payment-header">
                      <strong>Secure payment</strong>
                      <span className="badge pass">Protected</span>
                    </div>
                    <div className="payment-methods">
                      <button className={`payment-mode ${paymentMethod === 'card' ? 'active' : ''}`} onClick={() => setPaymentMethod('card')}>Card</button>
                      <button className={`payment-mode ${paymentMethod === 'upi' ? 'active' : ''}`} onClick={() => setPaymentMethod('upi')}>UPI</button>
                    </div>

                    {paymentMethod === 'card' ? (
                      <div className="payment-grid">
                        <div className="input-group" style={{ gridColumn: '1 / -1' }}>
                          <label>Name on card</label>
                          <input value={paymentForm.cardName} onChange={(event) => setPaymentForm((current) => ({ ...current, cardName: event.target.value }))} />
                        </div>
                        <div className="input-group" style={{ gridColumn: '1 / -1' }}>
                          <label>Card number</label>
                          <input value={paymentForm.cardNumber} onChange={(event) => setPaymentForm((current) => ({ ...current, cardNumber: event.target.value }))} />
                        </div>
                        <div className="input-group">
                          <label>Expiry</label>
                          <input value={paymentForm.expiry} onChange={(event) => setPaymentForm((current) => ({ ...current, expiry: event.target.value }))} />
                        </div>
                        <div className="input-group">
                          <label>CVV</label>
                          <input value={paymentForm.cvv} onChange={(event) => setPaymentForm((current) => ({ ...current, cvv: event.target.value }))} />
                        </div>
                      </div>
                    ) : (
                      <div className="input-group" style={{ marginTop: 6 }}>
                        <label>UPI ID</label>
                        <input value="aarav@upi" readOnly />
                      </div>
                    )}

                    <div className="payment-summary">
                      <div>
                        <div className="summary-meta">Order total</div>
                        <div className="price">₹{amountToPay}</div>
                      </div>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <button className="ghost-button" onClick={() => checkout(recommendedProduct.id, amountToPay, true)} disabled={loadingCheckout}>Test decline</button>
                        <button className="primary-button" onClick={() => checkout(recommendedProduct.id, amountToPay, false)} disabled={loadingCheckout}>
                          {loadingCheckout ? 'Processing…' : 'Pay now'}
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {checkoutResult && (
                  <div className={`checkout-box ${checkoutResult.success ? 'success' : 'fail'}`}>
                    <div className="recommendation-top">
                      <strong>{checkoutResult.success ? 'Checkout approved' : 'Checkout held'}</strong>
                      <span className={`badge ${checkoutResult.success ? 'pass' : 'fail'}`}>{checkoutResult.status}</span>
                    </div>
                    <div>{checkoutResult.message}</div>
                    <div className="reasoning-box">{checkoutResult.reasoning}</div>
                    {checkoutResult.retry_available && (
                      <div style={{ marginTop: 14 }}>
                        <button className="secondary-button" onClick={() => {
                          if (recommendedProduct && agentResponse?.proposed_amount) {
                            void checkout(recommendedProduct.id, agentResponse.proposed_amount, false);
                          }
                        }}>
                          Retry safe checkout
                        </button>
                      </div>
                    )}
                  </div>
                )}

                <OrderTrackingCard order={order} />

                <div className="action-chips">
                  {['Need a gentle moisturizer', 'Best sunscreen under ₹900', 'Hydrating serum for dry skin'].map((prompt) => (
                    <button key={prompt} className="chip" onClick={() => void sendMessage(prompt)}>{prompt}</button>
                  ))}
                </div>

                <div className="composer">
                  <textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault();
                      void sendMessage();
                    }
                  }} placeholder="Ask for a moisturizer, sunscreen or serum under a budget…" />
                  <button className="send-button" onClick={() => void sendMessage()}>→</button>
                </div>
              </section>

              <aside className="panel side-panel">
                <div className="eyebrow" style={{ color: '#a66932' }}>How it works</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 18, marginTop: 20 }}>
                  <div><strong>01</strong><div className="muted">You describe the need in plain language.</div></div>
                  <div><strong>02</strong><div className="muted">The agent selects the best-fit product and explains why.</div></div>
                  <div><strong>03</strong><div className="muted">Guardrails check value and category before payment is attempted.</div></div>
                </div>

                <div className="guardrail-box" style={{ marginTop: 24 }}>
                  <div className="header"><span>Guardrails</span><span className="status-pill" style={{ background: 'rgba(229,195,109,0.2)', color: '#f9d98c' }}>Live</span></div>
                  <div className="guardrail-row"><span>Session spend</span><strong>₹8,000</strong></div>
                  <div className="guardrail-row"><span>Category allow-list</span><strong>Enabled</strong></div>
                  <div className="guardrail-row"><span>Audit trail</span><strong>Recording</strong></div>
                </div>
              </aside>
            </div>
          )}

          {view === 'saved' && (
            <div className="audit-shell">
              <div className="audit-header">
                <div>
                  <div className="eyebrow" style={{ color: '#a66932' }}>Saved for later</div>
                  <h2 style={{ margin: 0, fontSize: 'clamp(2rem, 4vw, 3.5rem)', letterSpacing: '-0.06em' }}>Wishlist</h2>
                </div>
              </div>

              {savedItems.length === 0 ? (
                <div className="panel" style={{ padding: 28 }}>
                  <strong>No saved items yet.</strong>
                  <div className="muted" style={{ marginTop: 8 }}>Save a product from the agent flow to keep it in your shortlist.</div>
                </div>
              ) : (
                <div className="catalog-grid">
                  {savedItems.map((product) => (
                    <article className="catalog-card" key={product.id}>
                      <div className="art-card">{productEmoji[product.category.toLowerCase()] ?? productEmoji.default}</div>
                      <div className="catalog-meta">
                        <div>
                          <div className="category-tag">{product.category}</div>
                          <h3>{product.name}</h3>
                        </div>
                        <div className="price">₹{product.price}</div>
                      </div>
                      <p>{product.description}</p>
                      <div className="card-row">
                        <span className="muted">Stock: {product.stock}</span>
                        <button className="ghost-button" onClick={() => void toggleSavedItem(product)} disabled={savingProductId === product.id}>
                          {savingProductId === product.id ? 'Removing…' : 'Remove'}
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>
          )}

          {view === 'profile' && (
            <div className="audit-shell">
              <div className="audit-header">
                <div>
                  <div className="eyebrow" style={{ color: '#a66932' }}>Membership</div>
                  <h2 style={{ margin: 0, fontSize: 'clamp(2rem, 4vw, 3.5rem)', letterSpacing: '-0.06em' }}>Your profile</h2>
                </div>
              </div>

              <div className="audit-summary">
                <div className="panel metric-card">
                  <h4>Saved items</h4>
                  <div className="metric-value">{savedItems.length}</div>
                </div>
                <div className="panel metric-card">
                  <h4>Orders</h4>
                  <div className="metric-value">{order ? 1 : 0}</div>
                </div>
                <div className="panel metric-card">
                  <h4>Member tier</h4>
                  <div className="metric-value">Gold</div>
                </div>
                <div className="panel metric-card">
                  <h4>Alerts</h4>
                  <div className="metric-value">2</div>
                </div>
              </div>

              <div className="audit-layout">
                <section className="panel audit-panel">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                    <strong>Recent activity</strong>
                    <span className="badge pass">Synced</span>
                  </div>
                  <div className="audit-list">
                    <div className="audit-item">
                      <div>
                        <strong>Skin routine review</strong>
                        <div className="muted">Today, 9:42 AM</div>
                      </div>
                      <div>
                        <strong>Category</strong>
                        <div>Moisturizer</div>
                      </div>
                      <div>
                        <strong>Summary</strong>
                        <div className="muted">Nila suggested a lighter hydrator and saved it to your shortlist.</div>
                      </div>
                      <div>
                        <strong>State</strong>
                        <span className="badge pass">Safe</span>
                      </div>
                    </div>
                    <div className="audit-item">
                      <div>
                        <strong>Checkout attempt</strong>
                        <div className="muted">Yesterday, 6:18 PM</div>
                      </div>
                      <div>
                        <strong>Result</strong>
                        <div>{order ? 'Approved' : 'No active order'}</div>
                      </div>
                      <div>
                        <strong>Reason</strong>
                        <div className="muted">Guardrails reviewed and order was validated against the session limit.</div>
                      </div>
                      <div>
                        <strong>State</strong>
                        <span className={`badge ${order ? 'pass' : 'fail'}`}>{order ? 'Live' : 'Idle'}</span>
                      </div>
                    </div>
                  </div>
                </section>

                <aside className="audit-side-box">
                  <div style={{ fontSize: '11px', letterSpacing: '0.14em', textTransform: 'uppercase', opacity: 0.8 }}>Preferences</div>
                  <div style={{ fontSize: '2rem', fontWeight: 800, margin: '12px 0 18px', letterSpacing: '-0.06em' }}>You like gentle, effective essentials.</div>
                  <div className="row"><span>Preferred category</span><strong>Moisturizers</strong></div>
                  <div className="row"><span>Budget comfort</span><strong>₹800</strong></div>
                  <div className="row"><span>Skin type</span><strong>Dry</strong></div>
                  <div className="row"><span>Notifications</span><strong>On</strong></div>
                </aside>
              </div>
            </div>
          )}

          {view === 'audit' && (
            <div className="audit-shell">
              <div className="audit-header">
                <div>
                  <div className="eyebrow" style={{ color: '#a66932' }}>Control room</div>
                  <h2 style={{ margin: 0, fontSize: 'clamp(2rem, 4vw, 3.5rem)', letterSpacing: '-0.06em' }}>Audit trail</h2>
                </div>
                <button className="ghost-button" onClick={() => void loadAudit()}>Refresh</button>
              </div>

              <div className="audit-summary">
                <div className="panel metric-card">
                  <h4>Actions today</h4>
                  <div className="metric-value">{summary?.actions_today ?? 0}</div>
                </div>
                <div className="panel metric-card">
                  <h4>Session total</h4>
                  <div className="metric-value">₹{summary?.session_total_spend ?? 0}</div>
                </div>
                <div className="panel metric-card">
                  <h4>Remaining</h4>
                  <div className="metric-value">₹{summary?.session_remaining ?? 0}</div>
                </div>
                <div className="panel metric-card">
                  <h4>Guardrail pass</h4>
                  <div className="metric-value">{summary?.guardrail_pass_rate ?? 0}%</div>
                </div>
              </div>

              <div className="audit-layout">
                <section className="panel audit-panel">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                    <strong>Action history</strong>
                    <div className="audit-filter-row">
                      {[
                        { label: 'All events', value: 'all' },
                        { label: 'Pass', value: 'pass' },
                        { label: 'Fail', value: 'fail' },
                      ].map((filter) => (
                        <button
                          key={filter.value}
                          className={`audit-filter ${auditFilter === filter.value ? 'active' : ''}`}
                          onClick={() => setAuditFilter(filter.value as 'all' | 'pass' | 'fail')}
                        >
                          {filter.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="audit-list">
                    {loadingAudit ? (
                      <div className="panel" style={{ padding: 18 }}>Loading audit log…</div>
                    ) : filteredAuditEvents.length === 0 ? (
                      <div className="panel" style={{ padding: 18 }}>No audit events in this view.</div>
                    ) : (
                      filteredAuditEvents.map((event) => (
                        <div className="audit-item" key={event.id}>
                          <div>
                            <strong>{event.action_type}</strong>
                            <div className="muted">{new Date(event.timestamp).toLocaleString()}</div>
                          </div>
                          <div>
                            <strong>Amount</strong>
                            <div>₹{event.amount ?? 0}</div>
                          </div>
                          <div>
                            <strong>Reasoning</strong>
                            <div className="muted">{event.reasoning}</div>
                            {event.candidates_considered && event.candidates_considered.length > 0 && (
                              <details style={{ marginTop: 8 }}>
                                <summary style={{ cursor: 'pointer', color: '#145c4f', fontWeight: 700 }}>Other options considered</summary>
                                <ul style={{ margin: '8px 0 0 18px', padding: 0, color: '#425856' }}>
                                  {event.candidates_considered.map((candidate, index) => (
                                    <li key={`${event.id}-candidate-${index}`}>
                                      <strong>{candidate.name}</strong> — {candidate.reason} ({candidate.category}, ₹{candidate.price ?? 0})
                                    </li>
                                  ))}
                                </ul>
                              </details>
                            )}
                          </div>
                          <div>
                            <strong>Result</strong>
                            <span className={`badge ${event.bounds_passed ? 'pass' : 'fail'}`}>{event.bounds_passed ? 'Pass' : 'Fail'}</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </section>

                <aside className="audit-side-box">
                  <div style={{ fontSize: '11px', letterSpacing: '0.14em', textTransform: 'uppercase', opacity: 0.8 }}>Why it matters</div>
                  <div style={{ fontSize: '2rem', fontWeight: 800, margin: '12px 0 18px', letterSpacing: '-0.06em' }}>Every money action explainable.</div>
                  <div className="row"><span>Session total</span><strong>₹{summary?.session_total_spend ?? 0}</strong></div>
                  <div className="row"><span>Session cap</span><strong>₹{summary?.session_total_cap ?? 9000}</strong></div>
                  <div className="row"><span>Remaining</span><strong>₹{summary?.session_remaining ?? 9000}</strong></div>
                  <div className="row"><span>Failure mode</span><strong>Blocked</strong></div>
                </aside>
              </div>
            </div>
          )}
        </main>
      </div>
    </>
  );
}

export default App;
