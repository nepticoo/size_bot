import { Route, Routes } from "react-router-dom";
import BuyerFlow from "./routes/buyer/BuyerFlow";
import AnswerPage from "./routes/buyer/AnswerPage";
import Login from "./routes/seller/Login";
import PanelLayout from "./routes/seller/PanelLayout";
import ProductList from "./routes/seller/ProductList";
import ProductDetail from "./routes/seller/ProductDetail";
import SizeTable from "./routes/seller/SizeTable";
import LinkPage from "./routes/seller/LinkPage";
import RequestsList from "./routes/seller/RequestsList";
import ShopsList from "./routes/operator/ShopsList";
import CriteriaPage from "./routes/operator/CriteriaPage";

function Home() {
  return (
    <div style={{ padding: 40, textAlign: "center", color: "var(--color-text-muted)" }}>
      سایز — لینکِ محصول را از فروشنده بگیر.
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/p/:linkCode" element={<BuyerFlow />} />
      <Route path="/r/:viewCode" element={<AnswerPage />} />

      <Route path="/panel/login" element={<Login />} />
      <Route path="/panel" element={<PanelLayout />}>
        <Route index element={<ProductList />} />
        <Route path="products/new" element={<ProductDetail />} />
        <Route path="products/:id" element={<ProductDetail />} />
        <Route path="products/:id/sizes" element={<SizeTable />} />
        <Route path="products/:id/link" element={<LinkPage />} />
        <Route path="requests" element={<RequestsList />} />
      </Route>

      <Route path="/admin/shops" element={<PanelLayout />}>
        <Route index element={<ShopsList />} />
      </Route>
      <Route path="/admin/criteria" element={<PanelLayout />}>
        <Route index element={<CriteriaPage />} />
      </Route>
    </Routes>
  );
}
