import { Route, Routes } from "react-router-dom";
import Login from "./routes/seller/Login";
import PanelLayout from "./routes/seller/PanelLayout";
import ProductList from "./routes/seller/ProductList";

function Placeholder({ label }: { label: string }) {
  return <div style={{ padding: 24 }}>{label}</div>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Placeholder label="سایز" />} />
      <Route path="/panel/login" element={<Login />} />
      <Route path="/panel" element={<PanelLayout />}>
        <Route index element={<ProductList />} />
      </Route>
    </Routes>
  );
}
