export type Product = {
  id: number;
  name: string;
  description: string;
  price: number;
  stock: number;
  category: string;
  image: string;
  accent: string;
  rating: number;
};

export type AuditEvent = {
  id: string;
  timestamp: string;
  actionType: string;
  amount: number;
  boundsPassed: boolean;
  reasoning: string;
  outcome: string;
};

export const products: Product[] = [
  { id: 1, name: "Cloudmilk Barrier Cream", description: "A cushiony daily moisturizer for dry, stressed skin.", price: 649, stock: 18, category: "moisturizer", image: "cloudmilk", accent: "#DDEBDD", rating: 4.9 },
  { id: 2, name: "Solar Veil SPF 50", description: "Weightless broad-spectrum protection with a dewy finish.", price: 599, stock: 32, category: "sunscreen", image: "solar", accent: "#F7E5B8", rating: 4.8 },
  { id: 3, name: "Dewdrop Hydration Serum", description: "Multi-weight hyaluronic acid for an instant drink of water.", price: 799, stock: 11, category: "serum", image: "dewdrop", accent: "#CFE6EE", rating: 4.7 },
  { id: 4, name: "Quiet Reset Cleanser", description: "A low-foam oat cleanser that leaves skin calm, never tight.", price: 449, stock: 26, category: "cleanser", image: "reset", accent: "#E7DED5", rating: 4.9 },
  { id: 5, name: "Night Orchard Oil", description: "A featherlight botanical blend for your evening ritual.", price: 899, stock: 7, category: "face oil", image: "orchard", accent: "#D8D8C2", rating: 4.6 },
  { id: 6, name: "Cloudmilk Mini Duo", description: "Two travel-sized barrier creams for skin on the move.", price: 399, stock: 41, category: "sets", image: "duo", accent: "#EBD9DF", rating: 4.8 },
  { id: 7, name: "Soft Focus Lip Veil", description: "A sheer, conditioning tint with a soft-focus finish.", price: 349, stock: 29, category: "makeup", image: "lip", accent: "#E8C9C0", rating: 4.5 },
  { id: 8, name: "Sunday Ritual Set", description: "The complete calm-skin routine: cleanse, hydrate, protect.", price: 1890, stock: 5, category: "sets", image: "ritual", accent: "#D6D1E5", rating: 5 },
];

export const auditEvents: AuditEvent[] = [
  { id: "evt_1042", timestamp: new Date(Date.now() - 2 * 60_000).toISOString(), actionType: "CHECKOUT_APPROVED", amount: 649, boundsPassed: true, reasoning: "Selected Cloudmilk Barrier Cream because it matches the moisturizer category, is in stock, and ₹649 is under the ₹800 budget.", outcome: "Awaiting payment" },
  { id: "evt_1041", timestamp: new Date(Date.now() - 8 * 60_000).toISOString(), actionType: "PAYMENT_DECLINED", amount: 799, boundsPassed: true, reasoning: "Razorpay test payment was intentionally declined. The order stayed bounded and no funds were captured.", outcome: "Retry offered" },
  { id: "evt_1040", timestamp: new Date(Date.now() - 15 * 60_000).toISOString(), actionType: "CATALOG_SEARCH", amount: 0, boundsPassed: true, reasoning: "Parsed request into category: moisturizer, concern: dry skin, maximum price: ₹800.", outcome: "3 matches found" },
  { id: "evt_1039", timestamp: new Date(Date.now() - 31 * 60_000).toISOString(), actionType: "BOUNDS_REJECTED", amount: 1890, boundsPassed: false, reasoning: "Rejected Sunday Ritual Set because ₹1,890 exceeds the configured maximum order value of ₹1,500.", outcome: "Blocked before payment" },
];

export function addAudit(event: Omit<AuditEvent, "id" | "timestamp">) {
  auditEvents.unshift({ ...event, id: `evt_${1043 + auditEvents.length}`, timestamp: new Date().toISOString() });
}