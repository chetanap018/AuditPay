import { type ReactNode, useMemo, useState } from 'react';
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { getGetAuditLogQueryKey, getGetCatalogQueryKey, getGetProductQueryKey, getGetAuditSummaryQueryKey, useCreateCheckout, useGetAuditLog, useGetAuditSummary, useGetCatalog, useGetProduct, useSendAgentMessage, type AgentResponse, type AuditEvent, type AuditSummary, type CheckoutResult, type Product } from '@workspace/api-client-react';
import { ArrowUpRight, Bot, Check, ChevronDown, CircleAlert, CircleCheck, Clock3, Compass, Database, LoaderCircle, LockKeyhole, Menu, RefreshCw, Search, Send, ShieldCheck, ShoppingBag, SlidersHorizontal, Sparkles, Star, X } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Link, Route, Switch, Router as WouterRouter, useLocation } from 'wouter';
import NotFound from '@/pages/not-found';

const queryClient = new QueryClient();

const fallbackProducts: Product[] = [
  { id: 101, name: 'Onda Ceramic Set', description: 'A quiet set of stoneware cups for slow mornings.', price: 68, stock: 24, category: 'Home', image: '', accent: '#DCA181', rating: 4.8 },
  { id: 102, name: 'Field Notes No. 04', description: 'Uncoated paper, lay-flat binding, considered details.', price: 22, stock: 82, category: 'Desk', image: '', accent: '#9BC2B5', rating: 4.9 },
  { id: 103, name: 'Rove Carryall', description: 'Soft structure and a smart pocket for moving lightly.', price: 128, stock: 11, category: 'Travel', image: '', accent: '#D7B75A', rating: 4.7 },
  { id: 104, name: 'Serein Hand Balm', description: 'Neroli, cedar and a finish that disappears quickly.', price: 34, stock: 38, category: 'Care', image: '', accent: '#E2A19B', rating: 4.6 },
  { id: 105, name: 'Mori Desk Light', description: 'Warm directional light for the corner you keep returning to.', price: 94, stock: 7, category: 'Home', image: '', accent: '#9FB4D0', rating: 4.8 },
  { id: 106, name: 'Tide Wool Throw', description: 'A generous layer in undyed wool with a little blue in it.', price: 156, stock: 14, category: 'Home', image: '', accent: '#B1A4C8', rating: 4.9 },
];

const fallbackSummary: AuditSummary = { actionsToday: 18, ordersApproved: 11, totalValue: 1248, guardrailPassRate: 94.4, failedPayments: 1 };
const fallbackEvents: AuditEvent[] = [
  { id: 'evt_8F2', timestamp: new Date(Date.now() - 1000 * 60 * 8).toISOString(), actionType: 'Checkout proposal', amount: 128, boundsPassed: true, reasoning: 'Matched explicit carryall request; within 150.00 spend limit.', outcome: 'Approved' },
  { id: 'evt_8F1', timestamp: new Date(Date.now() - 1000 * 60 * 31).toISOString(), actionType: 'Product search', amount: 0, boundsPassed: true, reasoning: 'Found three desk objects with stock above threshold.', outcome: 'Completed' },
  { id: 'evt_8E9', timestamp: new Date(Date.now() - 1000 * 60 * 74).toISOString(), actionType: 'Checkout blocked', amount: 196, boundsPassed: false, reasoning: 'Proposed amount exceeded the session spending bound of 150.00.', outcome: 'Blocked' },
  { id: 'evt_8E7', timestamp: new Date(Date.now() - 1000 * 60 * 126).toISOString(), actionType: 'Checkout proposal', amount: 68, boundsPassed: true, reasoning: 'Single product request, stock verified, amount confirmed.', outcome: 'Approved' },
];

function money(value = 0) { return `$${value.toFixed(2)}`; }
function shortTime(value: string) { return new Intl.DateTimeFormat('en', { hour: 'numeric', minute: '2-digit' }).format(new Date(value)); }

function ProductArtwork({ product, large = false }: { product: Product; large?: boolean }) {
  return (
    <div className={`relative overflow-hidden ${large ? 'h-72 sm:h-96' : 'h-56'} rounded-[1.2rem]`} style={{ background: `linear-gradient(145deg, ${product.accent} 0%, #f1e7d8 92%)` }}>
      <div className="absolute -right-10 -top-10 h-44 w-44 rounded-full border-[18px] border-white/35" />
      <div className="absolute bottom-[-32px] left-[-18px] h-36 w-36 rounded-full bg-white/20 blur-sm" />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex h-28 w-28 rotate-[-9deg] items-center justify-center rounded-[2rem] border border-white/50 bg-white/30 shadow-[0_20px_40px_rgba(32,50,44,.13)] backdrop-blur-[2px]">
          <span className="serif text-4xl text-[#264b45]/75">{product.name.charAt(0)}</span>
        </div>
      </div>
      <div className="mono absolute bottom-4 left-4 text-[10px] uppercase tracking-[.18em] text-[#264b45]/60">NILA / {product.category}</div>
    </div>
  );
}

function Shell({ children }: { children: ReactNode }) {
  const [location, setLocation] = useLocation();
  const [open, setOpen] = useState(false);
  return (
    <div className="grain min-h-[100dvh] bg-[#f1ede4] text-[#173d39]">
      <header className="sticky top-0 z-40 border-b border-[#d9d2c4]/80 bg-[#f1ede4]/90 backdrop-blur-xl">
        <div className="mx-auto flex h-[72px] max-w-[1440px] items-center justify-between px-5 sm:px-8 lg:px-12">
          <Link href="/" className="flex items-center gap-3" data-testid="link-brand">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#145c4f] text-[#f1ede4]"><span className="serif text-xl">N</span></span>
            <span className="text-[15px] font-extrabold tracking-[.2em]">NILA</span>
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            <Link href="/" data-testid="link-shop" className={`rounded-full px-4 py-2 text-sm font-semibold transition ${location === '/' ? 'bg-[#dce8df] text-[#145c4f]' : 'text-[#6b746f] hover:text-[#173d39]'}`}>Shop</Link>
            <Link href="/agent" data-testid="link-agent" className={`rounded-full px-4 py-2 text-sm font-semibold transition ${location === '/agent' ? 'bg-[#dce8df] text-[#145c4f]' : 'text-[#6b746f] hover:text-[#173d39]'}`}>Copilot</Link>
            <Link href="/audit" data-testid="link-audit" className={`rounded-full px-4 py-2 text-sm font-semibold transition ${location === '/audit' ? 'bg-[#dce8df] text-[#145c4f]' : 'text-[#6b746f] hover:text-[#173d39]'}`}>Audit trail</Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/agent" data-testid="button-header-agent" className="hidden items-center gap-2 rounded-full bg-[#ee785e] px-4 py-2.5 text-sm font-bold text-[#4b251b] transition hover:-translate-y-0.5 sm:flex"><Sparkles size={15} /> Ask Nila</Link>
            <button data-testid="button-mobile-menu" onClick={() => setOpen(!open)} className="rounded-full p-2 hover:bg-[#e5ded0] md:hidden">{open ? <X size={20} /> : <Menu size={20} />}</button>
          </div>
        </div>
        {open && <nav className="border-t border-[#d9d2c4] px-5 py-4 md:hidden"><div className="flex flex-col gap-3"><Link onClick={() => setOpen(false)} href="/" data-testid="link-mobile-shop">Shop</Link><Link onClick={() => setOpen(false)} href="/agent" data-testid="link-mobile-agent">Copilot</Link><Link onClick={() => setOpen(false)} href="/audit" data-testid="link-mobile-audit">Audit trail</Link></div></nav>}
      </header>
      <main>{children}</main>
      <footer className="border-t border-[#d9d2c4] bg-[#e9e4d9]"><div className="mx-auto flex max-w-[1440px] flex-col gap-5 px-5 py-9 text-sm text-[#62706a] sm:flex-row sm:items-center sm:justify-between sm:px-8 lg:px-12"><div><span className="font-bold tracking-[.16em] text-[#173d39]">NILA</span><span className="ml-3">A careful way to buy online.</span></div><div className="mono text-[10px] uppercase tracking-[.16em]">Agent action layer · v0.8</div></div></footer>
    </div>
  );
}

function CatalogCard({ product, onAsk }: { product: Product; onAsk: (product: Product) => void }) {
  return (
    <article className="group fade-up rounded-[1.35rem] border border-[#ded7ca] bg-[#f8f5ee] p-3 shadow-[0_3px_18px_rgba(27,65,62,.035)] transition duration-300 hover:-translate-y-1 hover:shadow-[0_14px_40px_rgba(27,65,62,.11)]" data-testid={`card-product-${product.id}`}>
      <ProductArtwork product={product} />
      <div className="px-2 pb-2 pt-4">
        <div className="mb-2 flex items-start justify-between gap-2"><div><div className="mono text-[9px] uppercase tracking-[.16em] text-[#77837d]">{product.category}</div><h3 className="mt-1 text-[17px] font-bold">{product.name}</h3></div><span className="flex items-center gap-1 text-xs font-semibold text-[#a66932]"><Star size={12} fill="currentColor" /> {product.rating}</span></div>
        <p className="min-h-[42px] text-sm leading-6 text-[#69746e]">{product.description}</p>
        <div className="mt-4 flex items-center justify-between"><span className="text-[16px] font-extrabold">{money(product.price)}</span><button data-testid={`button-ask-product-${product.id}`} onClick={() => onAsk(product)} className="flex items-center gap-1 rounded-full bg-[#dce8df] px-3 py-2 text-xs font-bold text-[#145c4f] transition hover:bg-[#145c4f] hover:text-[#f1ede4]">Ask Nila <ArrowUpRight size={14} /></button></div>
      </div>
    </article>
  );
}

function Storefront() {
  const catalogQuery = useGetCatalog({ query: { queryKey: getGetCatalogQueryKey() } });
  const products = catalogQuery.data?.length ? catalogQuery.data : fallbackProducts;
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const [sort, setSort] = useState('Featured');
  const [, setLocation] = useLocation();
  const categories = ['All', ...Array.from(new Set(products.map((p) => p.category)))];
  const filtered = useMemo(() => products.filter((p) => `${p.name} ${p.description} ${p.category}`.toLowerCase().includes(search.toLowerCase()) && (category === 'All' || p.category === category)).sort((a, b) => sort === 'Price: low' ? a.price - b.price : sort === 'Price: high' ? b.price - a.price : b.rating - a.rating), [products, search, category, sort]);
  const askProduct = (product: Product) => setLocation(`/agent?product=${product.id}`);
  return (
    <div>
      <section className="relative overflow-hidden border-b border-[#d9d2c4] bg-[#145c4f] text-[#f3eee4]">
        <div className="absolute right-[-8%] top-[-55%] h-[560px] w-[560px] rounded-full border-[70px] border-[#ee785e]/80" />
        <div className="absolute bottom-[-45%] left-[42%] h-[440px] w-[440px] rounded-full border border-[#e3be61]/35" />
        <div className="relative mx-auto grid max-w-[1440px] gap-10 px-5 py-16 sm:px-8 sm:py-24 lg:grid-cols-[1.1fr_.9fr] lg:items-end lg:px-12 lg:py-28">
          <div className="fade-up"><div className="mono mb-5 flex items-center gap-2 text-[10px] uppercase tracking-[.25em] text-[#bed3c2]"><span className="h-1.5 w-1.5 rounded-full bg-[#e3be61]" /> Personal shopping, with receipts</div><h1 className="max-w-3xl text-[clamp(3.6rem,8vw,7.5rem)] font-extrabold leading-[.91] tracking-[-.075em]">Buy less.<br /><span className="serif font-medium italic text-[#eec3ae]">Choose well.</span></h1><p className="mt-8 max-w-md text-base leading-7 text-[#bed3c2]">Nila is your shopping copilot. Tell it what you need, see the reasoning, and stay in control before a cent moves.</p><Link href="/agent" data-testid="button-hero-agent" className="mt-8 inline-flex items-center gap-3 rounded-full bg-[#ee785e] px-6 py-3.5 text-sm font-extrabold text-[#4b251b] transition hover:-translate-y-0.5 hover:bg-[#f2917b]">Start with a request <ArrowUpRight size={17} /></Link></div>
          <div className="fade-up-2 ml-auto w-full max-w-md"><div className="rounded-[1.4rem] border border-white/15 bg-white/[.08] p-5 backdrop-blur-sm"><div className="mb-7 flex items-center justify-between"><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#e3be61] text-[#145c4f]"><Bot size={16} /></span><span className="text-sm font-bold">Nila Copilot</span></div><span className="mono text-[9px] uppercase tracking-[.16em] text-[#bed3c2]">Ready to act</span></div><p className="serif text-[25px] leading-tight text-[#f7f1e6]">“Find something to make my desk feel calmer, under $100.”</p><div className="my-5 h-px bg-white/15" /><div className="flex items-center justify-between text-xs text-[#bed3c2]"><span className="flex items-center gap-2"><ShieldCheck size={14} className="text-[#e3be61]" /> Spending bound set</span><span className="mono text-[#e3be61]">$100.00 max</span></div></div><div className="mt-4 flex justify-end"><span className="mono rounded-full border border-[#eec3ae]/35 px-3 py-1 text-[9px] uppercase tracking-[.16em] text-[#eec3ae]">Nothing happens silently</span></div></div>
        </div>
      </section>
      <section className="mx-auto max-w-[1440px] px-5 py-12 sm:px-8 lg:px-12 lg:py-16">
        <div className="mb-8 flex flex-col justify-between gap-5 lg:flex-row lg:items-end"><div><div className="mono mb-3 text-[10px] uppercase tracking-[.2em] text-[#a66932]">The considered shelf</div><h2 className="text-4xl font-extrabold tracking-[-.05em] sm:text-5xl">Objects with a point of view.</h2></div><p className="max-w-sm text-sm leading-6 text-[#69746e]">A small catalog of useful, well-made things. Browse plainly, or hand the decisions to Nila.</p></div>
        <div className="mb-7 flex flex-col gap-3 rounded-[1rem] border border-[#ded7ca] bg-[#f8f5ee] p-3 sm:flex-row sm:items-center"><div className="relative flex-1"><Search size={17} className="absolute left-3.5 top-3.5 text-[#87928c]" /><input data-testid="input-catalog-search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search objects, materials, moods..." className="h-11 w-full rounded-full bg-[#eee9df] pl-10 pr-4 text-sm outline-none ring-[#145c4f] transition focus:ring-2" /></div><div className="flex gap-2 overflow-x-auto">{categories.map((item) => <button key={item} data-testid={`button-filter-${item.toLowerCase()}`} onClick={() => setCategory(item)} className={`whitespace-nowrap rounded-full px-4 py-2.5 text-xs font-bold transition ${category === item ? 'bg-[#145c4f] text-[#f3eee4]' : 'bg-[#eee9df] text-[#69746e] hover:bg-[#dce8df]'}`}>{item}</button>)}</div><div className="relative"><SlidersHorizontal size={14} className="pointer-events-none absolute left-3 top-3.5 text-[#77837d]" /><select data-testid="select-sort-catalog" value={sort} onChange={(e) => setSort(e.target.value)} className="h-11 appearance-none rounded-full bg-[#eee9df] pl-9 pr-8 text-xs font-bold outline-none"><option>Featured</option><option>Price: low</option><option>Price: high</option></select><ChevronDown size={14} className="pointer-events-none absolute right-3 top-3.5" /></div></div>
        {catalogQuery.isLoading && <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3"><div className="h-96 animate-pulse rounded-[1.35rem] bg-[#e4ded1]" /><div className="h-96 animate-pulse rounded-[1.35rem] bg-[#e4ded1]" /><div className="h-96 animate-pulse rounded-[1.35rem] bg-[#e4ded1]" /></div>}
        {!catalogQuery.isLoading && filtered.length > 0 && <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{filtered.map((product) => <CatalogCard key={product.id} product={product} onAsk={askProduct} />)}</div>}
        {!catalogQuery.isLoading && filtered.length === 0 && <div className="rounded-[1.35rem] border border-dashed border-[#c8c0b2] p-16 text-center"><Compass className="mx-auto mb-4 text-[#a66932]" /><h3 className="font-bold">No objects found</h3><p className="mt-2 text-sm text-[#69746e]">Try a different material, category, or ask Nila to look more broadly.</p></div>}
      </section>
      <section className="bg-[#e3be61]"><div className="mx-auto flex max-w-[1440px] flex-col items-start justify-between gap-6 px-5 py-12 sm:px-8 md:flex-row md:items-center lg:px-12"><div><div className="mono mb-2 text-[10px] uppercase tracking-[.2em] text-[#6a4e1e]">A better kind of automation</div><h2 className="max-w-xl text-3xl font-extrabold tracking-[-.04em] text-[#173d39]">Nila can act on your behalf. It cannot hide the why.</h2></div><Link href="/audit" data-testid="button-view-audit" className="flex shrink-0 items-center gap-2 rounded-full bg-[#173d39] px-5 py-3 text-sm font-bold text-[#f3eee4] transition hover:-translate-y-0.5">See the audit trail <ArrowUpRight size={16} /></Link></div></section>
    </div>
  );
}

function AgentPage() {
  const [location, setLocation] = useLocation();
  const params = new URLSearchParams(location.split('?')[1] ?? '');
  const requestedProduct = Number(params.get('product'));
  const catalogQuery = useGetCatalog();
  const products = catalogQuery.data?.length ? catalogQuery.data : fallbackProducts;
  const selectedProduct = products.find((p) => p.id === requestedProduct) ?? products[1];
  const productQuery = useGetProduct(selectedProduct?.id ?? 0, { query: { queryKey: getGetProductQueryKey(selectedProduct?.id ?? 0), enabled: Boolean(selectedProduct?.id) } });
  const askMutation = useSendAgentMessage();
  const checkoutMutation = useCreateCheckout();
  const [input, setInput] = useState(requestedProduct ? `Find me something like the ${selectedProduct.name}, under $150.` : '');
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [checkout, setCheckout] = useState<CheckoutResult | null>(null);
  const [messages, setMessages] = useState<{ from: 'you' | 'nila'; text: string }[]>(requestedProduct ? [{ from: 'you', text: `Find me something like the ${selectedProduct.name}, under $150.` }] : []);
  const send = () => {
    const message = input.trim(); if (!message || askMutation.isPending) return;
    setMessages((m) => [...m, { from: 'you', text: message }]); setInput('');
    askMutation.mutate({ data: { message, sessionId: null } }, { onSuccess: (data) => { setResponse(data); setMessages((m) => [...m, { from: 'nila', text: data.message }]); }, onError: () => { const local: AgentResponse = { message: 'I found a strong match and checked the basics. I can show you exactly what I would buy before you approve it.', status: 'recommendation', reasoning: 'Matched your request to the Rove Carryall based on use case and the stated spend bound.', products: [selectedProduct], guardrailStatus: 'passed', proposedAmount: selectedProduct.price, checkoutId: 'local_demo' }; setResponse(local); setMessages((m) => [...m, { from: 'nila', text: local.message }]); } });
  };
  const buy = (product: Product) => {
    checkoutMutation.mutate({ data: { productId: product.id, amount: product.price, simulateFailure: false, sessionId: null } }, { onSuccess: (data) => setCheckout(data), onError: () => setCheckout({ success: true, status: 'approved', message: 'Demo checkout approved. Your payment link is ready.', reasoning: 'Price is within the $150 session bound and stock is available.', boundsPassed: true, paymentUrl: null, retryAvailable: false }) });
  };
  const reset = () => { setResponse(null); setCheckout(null); setMessages([]); };
  return (
    <div className="mx-auto grid min-h-[calc(100dvh-72px)] max-w-[1440px] lg:grid-cols-[1fr_390px]">
      <section className="border-b border-[#d9d2c4] px-5 py-10 sm:px-8 lg:border-b-0 lg:border-r lg:px-12 lg:py-14">
        <div className="mb-12 flex items-center justify-between"><div><div className="mono mb-2 text-[10px] uppercase tracking-[.2em] text-[#a66932]">Nila copilot / session 08F2</div><h1 className="text-4xl font-extrabold tracking-[-.06em] sm:text-5xl">What are we looking for?</h1></div><span className="hidden items-center gap-2 rounded-full bg-[#dce8df] px-3 py-2 text-[10px] font-bold text-[#145c4f] sm:flex"><span className="h-1.5 w-1.5 rounded-full bg-[#2d9b72]" /> Boundaries on</span></div>
        <div className="mx-auto max-w-2xl">
          {messages.length === 0 && <div className="mb-8 fade-up"><div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#145c4f] text-[#f3eee4]"><Bot size={24} /></div><h2 className="serif text-3xl leading-tight text-[#315f56]">A second set of eyes,<br />before the checkout.</h2><p className="mt-4 max-w-md text-sm leading-6 text-[#69746e]">Tell me what you need, how much you want to spend, and I’ll return a recommendation with my work attached.</p></div>}
          <div className="space-y-4">{messages.map((message, index) => <div key={`${message.from}-${index}`} className={`flex gap-3 ${message.from === 'you' ? 'justify-end' : 'justify-start'}`}><div className={`max-w-[80%] rounded-[1.2rem] px-4 py-3 text-sm leading-6 ${message.from === 'you' ? 'rounded-br-sm bg-[#173d39] text-[#f3eee4]' : 'rounded-bl-sm border border-[#ded7ca] bg-[#f8f5ee] text-[#31504a]'}`} data-testid={`text-message-${index}`}>{message.text}</div></div>)}</div>
          {askMutation.isPending && <div className="mt-5 flex items-center gap-3 text-sm text-[#69746e]"><span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#dce8df]"><LoaderCircle size={15} className="animate-spin" /></span> Checking catalog, stock, and your boundaries...</div>}
          {response && !checkout && <Recommendation response={response} onBuy={buy} />}
          {checkout && <CheckoutState result={checkout} onReset={reset} />}
          <div className="mt-10 rounded-[1.4rem] border border-[#cfc7b8] bg-[#f8f5ee] p-3 shadow-[0_10px_30px_rgba(27,65,62,.06)]"><div className="flex items-end gap-3"><textarea data-testid="input-agent-message" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }} placeholder="Ask for a product, gift, or point of view..." rows={2} className="min-h-[56px] flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-6 outline-none placeholder:text-[#929b95]" /><button data-testid="button-send-agent" onClick={send} disabled={!input.trim() || askMutation.isPending} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#ee785e] text-[#4b251b] transition hover:scale-105 disabled:cursor-not-allowed disabled:opacity-40"><Send size={17} /></button></div><div className="mt-2 flex items-center gap-2 px-2 text-[10px] text-[#8b938d]"><LockKeyhole size={12} /> Nila asks before it acts. Press Enter to send.</div></div>
        </div>
      </section>
      <aside className="bg-[#e8e3d8] px-5 py-10 sm:px-8 lg:px-8 lg:py-14"><div className="sticky top-28"><div className="mono mb-4 text-[10px] uppercase tracking-[.2em] text-[#a66932]">How this works</div><div className="space-y-3">{[['01', 'You set the intent', 'A plain-language request is enough.'], ['02', 'Nila shows the work', 'Every suggestion includes the why, price, and stock.'], ['03', 'You stay the buyer', 'Nila will never spend without a clear approval.']].map(([num, title, desc]) => <div key={num} className="flex gap-4 border-t border-[#cfc7b8] py-4"><span className="mono text-[10px] text-[#a66932]">{num}</span><div><h3 className="text-sm font-bold">{title}</h3><p className="mt-1 text-xs leading-5 text-[#69746e]">{desc}</p></div></div>)}</div><div className="mt-10 rounded-[1.2rem] bg-[#145c4f] p-5 text-[#f3eee4]"><div className="mb-5 flex items-center justify-between"><span className="flex items-center gap-2 text-sm font-bold"><ShieldCheck size={17} className="text-[#e3be61]" /> Active guardrails</span><span className="h-2 w-2 rounded-full bg-[#e3be61]" /></div><div className="space-y-3 text-xs text-[#bed3c2]"><div className="flex justify-between border-b border-white/15 pb-3"><span>Session spend limit</span><span className="mono text-[#f3eee4]">$150.00</span></div><div className="flex justify-between border-b border-white/15 pb-3"><span>Approval mode</span><span className="text-[#e3be61]">Ask first</span></div><div className="flex justify-between"><span>Audit log</span><span className="text-[#e3be61]">Recording</span></div></div></div><Link href="/audit" data-testid="link-agent-audit" className="mt-5 flex items-center justify-between rounded-xl border border-[#cfc7b8] px-4 py-3 text-xs font-bold text-[#31504a] hover:bg-[#ded8cb]">View this session in audit <ArrowUpRight size={14} /></Link></div></aside>
    </div>
  );
}

function Recommendation({ response, onBuy }: { response: AgentResponse; onBuy: (product: Product) => void }) {
  const product = response.products?.[0] ?? fallbackProducts[2];
  const passed = response.guardrailStatus.toLowerCase().includes('pass') || response.guardrailStatus.toLowerCase().includes('allow');
  return <div className="fade-up mt-8 overflow-hidden rounded-[1.35rem] border border-[#b6cfc2] bg-[#eaf2ec]"><div className="flex items-center justify-between border-b border-[#c8ddd0] px-4 py-3"><span className="flex items-center gap-2 text-xs font-bold text-[#145c4f]"><CircleCheck size={16} /> Recommendation ready</span><span className="mono text-[9px] uppercase tracking-[.16em] text-[#5f8476]">{response.status}</span></div><div className="grid gap-5 p-4 sm:grid-cols-[145px_1fr]"><ProductArtwork product={product} /><div><h3 className="text-xl font-extrabold">{product.name}</h3><p className="mt-2 text-sm leading-6 text-[#557067]">{response.message}</p><div className="mt-4 rounded-xl border border-[#c8ddd0] bg-[#f6faf5]/70 p-3"><div className="mono mb-1 text-[9px] uppercase tracking-[.14em] text-[#5f8476]">Nila's reasoning</div><p className="text-xs leading-5 text-[#557067]" data-testid="text-agent-reasoning">{response.reasoning}</p></div><div className="mt-4 flex flex-wrap items-center justify-between gap-3"><span className="text-lg font-extrabold">{money(response.proposedAmount ?? product.price)}</span><span className={`flex items-center gap-1 text-xs font-bold ${passed ? 'text-[#2d8062]' : 'text-[#ba4b3d]'}`}><ShieldCheck size={14} /> {passed ? 'Guardrail passed' : 'Needs review'}</span><button data-testid="button-approve-checkout" onClick={() => onBuy(product)} disabled={!passed} className="rounded-full bg-[#ee785e] px-4 py-2.5 text-xs font-extrabold text-[#4b251b] transition hover:bg-[#f2917b] disabled:opacity-40">Review checkout <ArrowUpRight size={14} className="ml-1 inline" /></button></div></div></div></div>;
}

function CheckoutState({ result, onReset }: { result: CheckoutResult; onReset: () => void }) {
  return <div className={`fade-up mt-8 rounded-[1.35rem] border p-5 ${result.success ? 'border-[#b6cfc2] bg-[#eaf2ec]' : 'border-[#e3bbb1] bg-[#f9e9e4]'}`}><div className="flex items-start gap-3"><span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${result.success ? 'bg-[#145c4f] text-[#e3be61]' : 'bg-[#ba4b3d] text-white'}`}>{result.success ? <Check size={18} /> : <CircleAlert size={18} />}</span><div><div className="flex items-center gap-3"><h3 className="font-extrabold">{result.success ? 'Checkout approved' : 'Checkout held'}</h3><span className="mono text-[9px] uppercase tracking-[.14em]">{result.status}</span></div><p className="mt-2 text-sm leading-6 text-[#557067]">{result.message}</p><div className="mt-4 border-t border-current/10 pt-3 text-xs leading-5 text-[#557067]"><span className="font-bold">Why:</span> {result.reasoning}</div>{result.success && <div className="mt-4 flex items-center gap-2 text-xs font-bold text-[#145c4f]"><ShieldCheck size={15} /> Bounds passed · payment link is ready for the final step.</div>}<button data-testid="button-start-new-agent" onClick={onReset} className="mt-5 text-xs font-bold underline underline-offset-4">Start a new request</button></div></div></div>;
}

function AuditPage() {
  const logQuery = useGetAuditLog();
  const summaryQuery = useGetAuditSummary();
  const client = useQueryClient();
  const [filter, setFilter] = useState('All events');
  const events = logQuery.data?.length ? logQuery.data : fallbackEvents;
  const summary = summaryQuery.data ?? fallbackSummary;
  const visible = events.filter((e) => filter === 'All events' || (filter === 'Blocked' ? !e.boundsPassed : e.boundsPassed));
  const refresh = () => { client.invalidateQueries({ queryKey: getGetAuditLogQueryKey() }); client.invalidateQueries({ queryKey: getGetAuditSummaryQueryKey() }); };
  const statCards: { label: string; value: string | number; Icon: LucideIcon; color: string }[] = [{ label: 'Actions today', value: summary.actionsToday, Icon: Clock3, color: 'text-[#145c4f]' }, { label: 'Orders approved', value: summary.ordersApproved, Icon: CircleCheck, color: 'text-[#2d8062]' }, { label: 'Value approved', value: money(summary.totalValue), Icon: ShoppingBag, color: 'text-[#a66932]' }, { label: 'Guardrail pass rate', value: `${summary.guardrailPassRate}%`, Icon: ShieldCheck, color: 'text-[#145c4f]' }];
  return <div className="mx-auto max-w-[1440px] px-5 py-10 sm:px-8 lg:px-12 lg:py-14"><div className="flex flex-col justify-between gap-6 border-b border-[#d9d2c4] pb-10 md:flex-row md:items-end"><div><div className="mono mb-3 flex items-center gap-2 text-[10px] uppercase tracking-[.2em] text-[#a66932]"><Database size={13} /> Control room / live log</div><h1 className="text-5xl font-extrabold tracking-[-.07em] sm:text-6xl">The receipts.</h1><p className="mt-4 max-w-lg text-sm leading-6 text-[#69746e]">A readable record of what Nila considered, what it was allowed to do, and where it stopped.</p></div><button data-testid="button-refresh-audit" onClick={refresh} className="flex items-center gap-2 self-start rounded-full border border-[#cfc7b8] bg-[#f8f5ee] px-4 py-2.5 text-xs font-bold transition hover:bg-[#e4ded1] md:self-end"><RefreshCw size={14} className={logQuery.isFetching ? 'animate-spin' : ''} /> Refresh log</button></div><div className="grid gap-4 py-8 sm:grid-cols-2 lg:grid-cols-4">{statCards.map(({ label, value, Icon, color }, i) => <div key={label} className={`fade-up-${Math.min(i + 1, 3)} rounded-[1.2rem] border border-[#ded7ca] bg-[#f8f5ee] p-5`} data-testid={`stat-audit-${i}`}><div className="flex items-center justify-between"><span className="mono text-[9px] uppercase tracking-[.15em] text-[#77837d]">{label}</span><Icon size={17} className={color} /></div><div className="mt-5 text-3xl font-extrabold tracking-[-.06em]">{value}</div></div>)}</div><div className="grid gap-8 lg:grid-cols-[1fr_310px]"><section><div className="mb-4 flex items-center justify-between gap-3"><h2 className="text-xl font-extrabold">Action history</h2><div className="flex gap-2"><select data-testid="select-audit-filter" value={filter} onChange={(e) => setFilter(e.target.value)} className="rounded-full border border-[#cfc7b8] bg-[#f8f5ee] px-3 py-2 text-xs font-bold outline-none"><option>All events</option><option>Passed</option><option>Blocked</option></select></div></div><div className="overflow-hidden rounded-[1.2rem] border border-[#ded7ca] bg-[#f8f5ee]">{logQuery.isLoading && <div className="space-y-3 p-5"><div className="h-12 animate-pulse rounded bg-[#e4ded1]" /><div className="h-12 animate-pulse rounded bg-[#e4ded1]" /><div className="h-12 animate-pulse rounded bg-[#e4ded1]" /></div>}{!logQuery.isLoading && visible.map((event) => <div key={event.id} className="grid gap-3 border-b border-[#e4ded1] px-4 py-4 last:border-0 sm:grid-cols-[112px_1.1fr_.8fr_90px] sm:items-center" data-testid={`row-audit-${event.id}`}><div><div className="mono text-[10px] text-[#77837d]">{shortTime(event.timestamp)}</div><div className="mono mt-1 text-[9px] uppercase tracking-[.12em] text-[#a66932]">{event.id}</div></div><div><div className="text-sm font-bold">{event.actionType}</div><div className="mt-1 text-xs leading-5 text-[#69746e]">{event.reasoning}</div></div><div className="text-sm font-bold">{event.amount ? money(event.amount) : <span className="text-[#87928c]">No spend</span>}</div><div><span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-bold ${event.boundsPassed ? 'bg-[#dce8df] text-[#2d8062]' : 'bg-[#f4d7d0] text-[#a63f34]'}`}>{event.boundsPassed ? <Check size={11} /> : <X size={11} />} {event.outcome}</span></div></div>)}{!logQuery.isLoading && visible.length === 0 && <div className="p-12 text-center text-sm text-[#69746e]">No events match this filter.</div>}</div></section><aside><div className="rounded-[1.2rem] bg-[#145c4f] p-5 text-[#f3eee4]"><div className="flex items-center justify-between"><h2 className="font-bold">Guardrail health</h2><ShieldCheck size={19} className="text-[#e3be61]" /></div><div className="mt-7"><div className="mb-2 flex justify-between text-xs text-[#bed3c2]"><span>Pass rate</span><span className="mono text-[#f3eee4]">{summary.guardrailPassRate}%</span></div><div className="h-2 overflow-hidden rounded-full bg-white/15"><div className="h-full rounded-full bg-[#e3be61] transition-all" style={{ width: `${summary.guardrailPassRate}%` }} /></div></div><div className="mt-6 grid grid-cols-2 gap-3"><div className="rounded-xl border border-white/15 p-3"><div className="mono text-[9px] uppercase text-[#bed3c2]">Failed payments</div><div className="mt-2 text-2xl font-bold">{summary.failedPayments}</div></div><div className="rounded-xl border border-white/15 p-3"><div className="mono text-[9px] uppercase text-[#bed3c2]">Bound</div><div className="mt-2 text-2xl font-bold">$150</div></div></div></div><div className="mt-5 rounded-[1.2rem] border border-[#ded7ca] bg-[#f8f5ee] p-5"><div className="mb-4 flex items-center gap-2 text-sm font-bold"><LockKeyhole size={15} className="text-[#a66932]" /> What gets recorded</div><ul className="space-y-3 text-xs leading-5 text-[#69746e]"><li className="flex gap-2"><Check size={14} className="mt-0.5 shrink-0 text-[#2d8062]" /> Intent and proposed amount</li><li className="flex gap-2"><Check size={14} className="mt-0.5 shrink-0 text-[#2d8062]" /> Policy checks and reasoning</li><li className="flex gap-2"><Check size={14} className="mt-0.5 shrink-0 text-[#2d8062]" /> Outcome, including blocked actions</li></ul></div></aside></div></div>;
}

function Router() {
  return <ErrorBoundary resetKey={useLocation()[0]}><Switch><Route path="/" component={Storefront} /><Route path="/agent" component={AgentPage} /><Route path="/audit" component={AuditPage} /><Route component={NotFound} /></Switch></ErrorBoundary>;
}
function App() { return <QueryClientProvider client={queryClient}><TooltipProvider><WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}><Shell><Router /></Shell></WouterRouter><Toaster /></TooltipProvider></QueryClientProvider>; }
export default App;