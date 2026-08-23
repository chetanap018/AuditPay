import { Router, type IRouter } from "express";
import { auditEvents } from "../data/store";

const router: IRouter = Router();

router.get("/audit", (_req, res) => res.json(auditEvents));
router.get("/audit/summary", (_req, res) => res.json({
  actionsToday: auditEvents.length + 19,
  ordersApproved: auditEvents.filter((event) => event.actionType === "CHECKOUT_APPROVED").length + 7,
  totalValue: 5840,
  guardrailPassRate: 96.4,
  failedPayments: auditEvents.filter((event) => event.actionType === "PAYMENT_DECLINED").length,
}));

export default router;