import { Router, type IRouter } from "express";
import { products } from "../data/store";

const router: IRouter = Router();

router.get("/catalog", (_req, res) => res.json(products));
router.get("/catalog/:id", (req, res) => {
  const product = products.find((item) => item.id === Number(req.params.id));
  if (!product) return res.status(404).json({ error: "Product not found" });
  return res.json(product);
});

export default router;