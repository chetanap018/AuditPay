import { Router, type IRouter } from "express";
import { CreateCheckoutBody } from "@workspace/api-zod";
import { products, addAudit } from "../data/store";
import { checkOrderBounds, checkSessionOrderLimit } from "../core/guardrails";

const router: IRouter = Router();

router.post("/checkout", (req, res) => {
  const parsed = CreateCheckoutBody.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: "Invalid checkout request." });
  const input = parsed.data;
  const product = products.find((item) => item.id === input.productId);
  if (!product) return res.status(404).json({ error: "Product not found." });
  const bounds = checkOrderBounds(input.amount, product.category);
  const session = checkSessionOrderLimit(0);
  if (!bounds.passed || !session.passed) {
    const reasoning = !bounds.passed ? bounds.reason : session.reason;
    addAudit({ actionType: "BOUNDS_REJECTED", amount: input.amount, boundsPassed: false, reasoning, outcome: "Blocked before payment" });
    return res.json({ success: false, status: "blocked", message: "I stopped this checkout before it reached Razorpay.", reasoning, boundsPassed: false, retryAvailable: false });
  }
  if (input.simulateFailure) {
    const reasoning = "Razorpay test payment was intentionally declined. No funds were captured and the order remains safe to retry.";
    addAudit({ actionType: "PAYMENT_DECLINED", amount: input.amount, boundsPassed: true, reasoning, outcome: "Retry offered" });
    return res.json({ success: false, status: "payment_declined", message: "The test payment was declined — your money is safe. You can retry with a different test payment method.", reasoning, boundsPassed: true, retryAvailable: true });
  }
  const reasoning = `Guardrails passed: ₹${input.amount} is under the maximum and ${product.category} is approved. Created a Razorpay test checkout for ${product.name}.`;
  addAudit({ actionType: "CHECKOUT_APPROVED", amount: input.amount, boundsPassed: true, reasoning, outcome: "Awaiting payment" });
  return res.json({ success: true, status: "checkout_created", message: "Checkout is ready. This is a Razorpay test-mode payment link.", reasoning, boundsPassed: true, paymentUrl: "https://rzp.io/i/nila-test", retryAvailable: false });
});

export default router;