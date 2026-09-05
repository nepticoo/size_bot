import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";

interface Criterion {
  id: number;
  garment_type_id: number;
  name: string;
  is_main: boolean;
  kind: string;
  where_text: string;
  measure_rule: string | null;
}

interface GarmentType {
  id: number;
  name: string;
}

export default function CriteriaPage() {
  const queryClient = useQueryClient();
  const [garmentTypeId, setGarmentTypeId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [kind, setKind] = useState<"circumference" | "length">("circumference");
  const [whereText, setWhereText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: criteria } = useQuery<Criterion[]>({
    queryKey: ["admin-criteria"],
    queryFn: () => apiFetch<Criterion[]>("/admin/criteria"),
  });
  const { data: garmentTypes } = useQuery<GarmentType[]>({
    queryKey: ["garment-types"],
    queryFn: () => apiFetch<GarmentType[]>("/garment-types"),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch("/admin/criteria", {
        method: "POST",
        body: JSON.stringify({
          garment_type_id: garmentTypeId,
          name,
          is_main: false,
          kind,
          where_text: whereText,
          measure_rule: null,
        }),
      }),
    onSuccess: () => {
      setName("");
      setWhereText("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["admin-criteria"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const byType = new Map<number, Criterion[]>();
  for (const c of criteria ?? []) {
    if (!byType.has(c.garment_type_id)) byType.set(c.garment_type_id, []);
    byType.get(c.garment_type_id)!.push(c);
  }

  return (
    <div style={{ maxWidth: 640, margin: "0 auto", padding: 20, display: "flex", flexDirection: "column", gap: 24 }}>
      <h1 style={{ fontSize: 18 }}>معیارهای اندازه</h1>

      {garmentTypes?.map((g) => (
        <div key={g.id}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>{g.name}</div>
          <div style={{ border: "1px solid var(--color-border)", borderRadius: 12, overflow: "hidden" }}>
            {(byType.get(g.id) ?? []).map((c) => (
              <div key={c.id} style={{ display: "flex", justifyContent: "space-between", padding: "10px 14px", borderBottom: "1px solid var(--color-border-soft)", fontSize: 13.5 }}>
                <span>
                  {c.name} {c.is_main && <span style={{ color: "var(--color-accent)" }}>★</span>}
                </span>
                <span style={{ color: "var(--color-text-muted)" }}>{c.kind === "circumference" ? "دور" : "طول"}</span>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div style={{ border: "1px solid var(--color-border)", borderRadius: 14, padding: 16, display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ fontWeight: 700 }}>معیارِ تازه</div>
        <select value={garmentTypeId ?? ""} onChange={(e) => setGarmentTypeId(Number(e.target.value))} style={inputStyle}>
          <option value="">نوعِ پوشاک</option>
          {garmentTypes?.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}
            </option>
          ))}
        </select>
        <input placeholder="نامِ معیار" value={name} onChange={(e) => setName(e.target.value)} style={inputStyle} />
        <select value={kind} onChange={(e) => setKind(e.target.value as "circumference" | "length")} style={inputStyle}>
          <option value="circumference">دور</option>
          <option value="length">طول</option>
        </select>
        <input placeholder="توضیحِ محلِ اندازه‌گیری" value={whereText} onChange={(e) => setWhereText(e.target.value)} style={inputStyle} />
        {error && <div style={{ color: "#B9772E", fontSize: 13.5 }}>{error}</div>}
        <button disabled={!garmentTypeId || !name || !whereText} onClick={() => createMutation.mutate()} style={primaryButtonStyle}>
          افزودن
        </button>
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  height: 44,
  borderRadius: 10,
  border: "1px solid var(--color-border)",
  padding: "0 12px",
  fontSize: 14,
};

const primaryButtonStyle: React.CSSProperties = {
  height: 46,
  borderRadius: 10,
  border: "none",
  background: "var(--color-accent)",
  color: "#fff",
  fontWeight: 700,
};
