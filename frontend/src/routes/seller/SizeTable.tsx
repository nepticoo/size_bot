import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";
import { parseNumber, toPersianDigits } from "../../lib/digits";

interface Product {
  id: number;
  garment_type_id: number;
}

interface Criterion {
  id: number;
  garment_type_id: number;
  name: string;
  is_main: boolean;
  kind: string;
  where_text: string;
}

interface SizeRow {
  id: number;
  name: string;
  sort_order: number;
  is_complete: boolean;
  measurements: Record<number, number>;
}

export default function SizeTable() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [newSizeName, setNewSizeName] = useState("");

  const { data: product } = useQuery<Product>({
    queryKey: ["product", id],
    queryFn: () => apiFetch<Product>(`/products/${id}`),
  });
  const { data: criteria } = useQuery<Criterion[]>({
    queryKey: ["criteria"],
    queryFn: () => apiFetch<Criterion[]>("/criteria"),
  });
  const { data: sizes, refetch } = useQuery<SizeRow[]>({
    queryKey: ["sizes", id],
    queryFn: () => apiFetch<SizeRow[]>(`/products/${id}/sizes`),
  });
  const { data: link } = useQuery<{ is_active: boolean; complete_count: number; total_count: number }>({
    queryKey: ["link", id],
    queryFn: () => apiFetch(`/products/${id}/link`),
  });

  const relevantCriteria = (criteria ?? [])
    .filter((c) => c.garment_type_id === product?.garment_type_id)
    .sort((a, b) => (a.is_main === b.is_main ? 0 : a.is_main ? -1 : 1));

  const addSizeMutation = useMutation({
    mutationFn: (name: string) => apiFetch(`/products/${id}/sizes`, { method: "POST", body: JSON.stringify({ name }) }),
    onSuccess: () => {
      setNewSizeName("");
      queryClient.invalidateQueries({ queryKey: ["sizes", id] });
      queryClient.invalidateQueries({ queryKey: ["link", id] });
    },
  });

  const saveMeasurement = useMutation({
    mutationFn: ({ sizeId, criterionId, value }: { sizeId: number; criterionId: number; value: number }) =>
      apiFetch(`/sizes/${sizeId}/measurements`, {
        method: "PUT",
        body: JSON.stringify({ criterion_id: criterionId, value_cm: value }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sizes", id] });
      queryClient.invalidateQueries({ queryKey: ["link", id] });
    },
  });

  const deleteSize = useMutation({
    mutationFn: (sizeId: number) => apiFetch(`/sizes/${sizeId}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sizes", id] });
      queryClient.invalidateQueries({ queryKey: ["link", id] });
    },
    onError: async (_err, sizeId) => {
      if (confirm("این سایز درخواستِ گذشته دارد. حذف شود؟")) {
        await apiFetch(`/sizes/${sizeId}/force`, { method: "DELETE" });
        queryClient.invalidateQueries({ queryKey: ["sizes", id] });
      }
    },
  });

  if (!product || !sizes) return null;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: 20 }}>
      <h1 style={{ fontSize: 18 }}>جدولِ سایز</h1>

      {link && !link.is_active && (
        <div
          style={{
            background: "var(--color-accent-bg)",
            border: "1px solid var(--color-accent-bg-border)",
            borderRadius: 13,
            padding: "13px 14px",
            fontSize: 13.5,
            lineHeight: 1.8,
            color: "#3B4A63",
            marginBottom: 16,
          }}
        >
          لینکِ این محصول هنوز فعال نشده — دو اندازهٔ اصلی برای همهٔ سایزها لازم است. الان {link.complete_count} سایز از {link.total_count} کامل است.
        </div>
      )}

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
          <thead>
            <tr>
              <th style={thStyle}>سایز</th>
              {relevantCriteria.map((c) => (
                <th key={c.id} style={thStyle} title={c.where_text}>
                  {c.name}
                  {c.is_main && <span style={{ color: "var(--color-accent)" }}> ★</span>}
                </th>
              ))}
              <th style={thStyle} />
            </tr>
          </thead>
          <tbody>
            {sizes.map((size) => (
              <tr key={size.id} style={{ background: size.is_complete ? "transparent" : "var(--color-amber-bg)" }}>
                <td style={{ ...tdStyle, fontWeight: 700 }}>
                  {size.name}
                  {!size.is_complete && (
                    <div style={{ fontSize: 11.5, color: "var(--color-amber-text)" }}>ناقص</div>
                  )}
                </td>
                {relevantCriteria.map((c) => (
                  <td key={c.id} style={tdStyle}>
                    <MeasurementInput
                      value={size.measurements[c.id]}
                      onSave={(value) => saveMeasurement.mutate({ sizeId: size.id, criterionId: c.id, value })}
                    />
                  </td>
                ))}
                <td style={tdStyle}>
                  <button onClick={() => deleteSize.mutate(size.id)} style={{ background: "none", border: "none", color: "var(--color-text-muted)", cursor: "pointer" }}>
                    حذف
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 20, display: "flex", gap: 10 }}>
        <input
          placeholder="نامِ سایزِ تازه"
          value={newSizeName}
          onChange={(e) => setNewSizeName(e.target.value)}
          style={{ height: 44, borderRadius: 10, border: "1px solid var(--color-border)", padding: "0 12px", flex: 1 }}
        />
        <button
          disabled={!newSizeName}
          onClick={() => addSizeMutation.mutate(newSizeName)}
          style={{ height: 44, borderRadius: 10, border: "none", background: "var(--color-accent)", color: "#fff", padding: "0 18px", fontWeight: 700 }}
        >
          افزودنِ سایز
        </button>
      </div>
    </div>
  );
}

function MeasurementInput({ value, onSave }: { value: number | undefined; onSave: (v: number) => void }) {
  const [text, setText] = useState(value !== undefined ? toPersianDigits(value) : "");

  function commit() {
    const parsed = parseNumber(text);
    if (!isNaN(parsed) && parsed > 0) {
      onSave(parsed);
    }
  }

  return (
    <input
      value={text}
      onChange={(e) => setText(e.target.value)}
      onBlur={commit}
      placeholder="—"
      style={{ width: 70, height: 36, borderRadius: 8, border: "1px solid var(--color-border)", textAlign: "center" }}
    />
  );
}

const thStyle: React.CSSProperties = {
  textAlign: "center",
  padding: "10px 8px",
  fontSize: 13,
  color: "var(--color-text-muted)",
  borderBottom: "1px solid var(--color-border)",
};

const tdStyle: React.CSSProperties = {
  textAlign: "center",
  padding: "10px 8px",
  borderBottom: "1px solid var(--color-border-soft)",
};
