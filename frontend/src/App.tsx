import { Route, Routes } from "react-router-dom";

function Placeholder({ label }: { label: string }) {
  return <div style={{ padding: 24 }}>{label}</div>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Placeholder label="سایز" />} />
    </Routes>
  );
}
