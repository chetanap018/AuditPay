import { Router, type IRouter } from "express";
import healthRouter from "./health";
import catalogRouter from "./catalog";
import agentRouter from "./agent";
import checkoutRouter from "./checkout";
import auditRouter from "./audit";

const router: IRouter = Router();

router.use(healthRouter);
router.use(catalogRouter);
router.use(agentRouter);
router.use(checkoutRouter);
router.use(auditRouter);

export default router;
