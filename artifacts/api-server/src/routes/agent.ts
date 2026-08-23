import { Router, type IRouter } from "express";
import { SendAgentMessageBody } from "@workspace/api-zod";
import { products, addAudit } from "../data/store";

const router: IRouter = Router();

router.post("/agent/chat", (req, res) => {
  const parsed = SendAgentMessageBody.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: "Please tell the agent what you are looking for." });
  const text = parsed.data.message.toLowerCase();
  const budgetMatch = text.match(/(?:under|below|less than|₹)\s?([\d,]+)/);
  const budget = budgetMatch ? Number(budgetMatch[1].replace(",", "")) : 1000;
  const category = ["moisturizer", "sunscreen", "serum", "cleanser", "face oil", "makeup", "sets"].find((value) => text.includes(value)) ?? (text.includes("dry") ? "moisturizer" : "");
  const matches = products.filter((product) => product.price <= budget && (!category || product.category === category) && product.stock > 0).slice(0, 3);
  const selected = matches[0];
  const reasoning = selected
    ? `Selected ${selected.name} because it matches ${category || "your request"}, is in stock, and ₹${selected.price} is under your ₹${budget} budget.`
    : `I couldn't find an in-stock match within ₹${budget}. I kept the search bounded and did not create an order.`;
  addAudit({ actionType: "CATALOG_SEARCH", amount: 0, boundsPassed: true, reasoning: `Parsed request into ${category || "open search"} with a maximum price of ₹${budget}.`, outcome: matches.length ? `${matches.length} matches found` : "No safe match" });
  return res.json({
    message: selected ? `I found a strong match: ${selected.name}. Want me to prepare the ₹${selected.price} checkout?` : "I couldn't find a safe match yet. Try widening your budget or asking for another category.",
    status: selected ? "recommendation_ready" : "no_match",
    reasoning,
    products: matches,
    guardrailStatus: selected ? "Ready for confirmation" : "No order proposed",
    proposedAmount: selected?.price ?? null,
    checkoutId: null,
  });
});

export default router;