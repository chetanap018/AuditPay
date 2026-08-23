export const MAX_ORDER_VALUE = 1500;
export const MAX_ORDERS_PER_SESSION = 3;
export const ALLOWED_CATEGORIES = ["moisturizer", "sunscreen", "serum", "cleanser", "face oil", "sets", "makeup"];

export type GuardrailResult = { passed: boolean; reason: string };

export function checkOrderBounds(amount: number, category: string): GuardrailResult {
  if (!Number.isFinite(amount) || amount <= 0) return { passed: false, reason: "Order amount must be a positive number." };
  if (amount > MAX_ORDER_VALUE) return { passed: false, reason: `Order value ₹${amount} exceeds the configured maximum of ₹${MAX_ORDER_VALUE}.` };
  if (!ALLOWED_CATEGORIES.includes(category.toLowerCase())) return { passed: false, reason: `Category "${category}" is not on the approved purchase allow-list.` };
  return { passed: true, reason: `Amount ₹${amount} is within the ₹${MAX_ORDER_VALUE} limit and category "${category}" is approved.` };
}

export function checkSessionOrderLimit(orderCount: number): GuardrailResult {
  return orderCount >= MAX_ORDERS_PER_SESSION
    ? { passed: false, reason: `Session has reached the maximum of ${MAX_ORDERS_PER_SESSION} orders.` }
    : { passed: true, reason: `Session has ${MAX_ORDERS_PER_SESSION - orderCount} bounded order slot(s) remaining.` };
}