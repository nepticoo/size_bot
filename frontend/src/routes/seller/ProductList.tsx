import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";

interface ProductRow {
  id: number;
  name: string;
  garment_type_id: number;
  is_active: boolean;
  size_count: number;
}

export default function ProductList() {
  const { data: products, isLoading } = useQuery<ProductRow[]>({
    queryKey: ["products"],
    queryFn: () => apiFetch<ProductRow[]>("/products"),
  });

  if (isLoading) return null;

  return (
    <div style={{ padding: 20, maxWidth: 720, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: 18, margin: 0 }}>فهرستِ محصول‌ها</h1>
        <Link
          to="/panel/products/new"
          style={{
            background: "var(--color-accent)",
            color: "#fff",
            padding: "10px 16px",
            borderRadius: 12,
            fontSize: 14,
            fontWeight: 700,
            textDecoration: "none",
          }}
        >
          محصولِ تازه
        </Link>
      </div>

      {!products || products.length === 0 ? (
        <div style={{ color: "var(--color-text-muted)", fontSize: 15, textAlign: "center", padding: 40 }}>
          هنوز محصولی نساخته‌ای.
        </div>
      ) : (
        <div style={{ border: "1px solid var(--color-border)", borderRadius: 14, overflow: "hidden" }}>
          {products.map((p) => (
            <Link
              key={p.id}
              to={`/panel/products/${p.id}`}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "16px 18px",
                borderBottom: "1px solid var(--color-border-soft)",
                textDecoration: "none",
                color: "var(--color-text)",
              }}
            >
              <div style={{ fontWeight: 600 }}>{p.name}</div>
              <div style={{ display: "flex", gap: 14, alignItems: "center", fontSize: 13.5, color: "var(--color-text-muted)" }}>
                <span>{p.size_count} سایز</span>
                <span style={{ color: p.is_active ? "var(--color-accent)" : "var(--color-text-faint)" }}>
                  {p.is_active ? "لینک فعال" : "لینک خاموش"}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
