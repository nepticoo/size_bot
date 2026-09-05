import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";

interface Shop {
  id: number;
  name: string;
  instagram: string | null;
  phone: string | null;
  is_active: boolean;
  username: string;
}

export default function ShopsList() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [instagram, setInstagram] = useState("");
  const [phone, setPhone] = useState("");
  const [created, setCreated] = useState<{ username: string; password: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: shops } = useQuery<Shop[]>({
    queryKey: ["admin-shops"],
    queryFn: () => apiFetch<Shop[]>("/admin/shops"),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch<{ username: string; password: string }>("/admin/shops", {
        method: "POST",
        body: JSON.stringify({ name, username, instagram: instagram || null, phone: phone || null }),
      }),
    onSuccess: (result) => {
      setCreated(result);
      setError(null);
      setName("");
      setUsername("");
      setInstagram("");
      setPhone("");
      queryClient.invalidateQueries({ queryKey: ["admin-shops"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  async function impersonate(shopId: number) {
    await fetch(`/api/admin/shops/${shopId}/impersonate`, { method: "POST" });
    window.location.href = "/panel";
  }

  return (
    <div style={{ maxWidth: 640, margin: "0 auto", padding: 20, display: "flex", flexDirection: "column", gap: 24 }}>
      <h1 style={{ fontSize: 18 }}>فهرستِ فروشگاه‌ها</h1>

      <div style={{ border: "1px solid var(--color-border)", borderRadius: 14, padding: 16, display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ fontWeight: 700, fontSize: 15 }}>فروشگاهِ تازه</div>
        <input placeholder="نامِ فروشگاه" value={name} onChange={(e) => setName(e.target.value)} style={inputStyle} />
        <input placeholder="نامِ کاربری" value={username} onChange={(e) => setUsername(e.target.value)} style={inputStyle} />
        <input placeholder="اینستاگرام (اختیاری)" value={instagram} onChange={(e) => setInstagram(e.target.value)} style={inputStyle} />
        <input placeholder="شماره (اختیاری)" value={phone} onChange={(e) => setPhone(e.target.value)} style={inputStyle} />
        {error && <div style={{ color: "#B9772E", fontSize: 13.5 }}>{error}</div>}
        <button disabled={!name || !username} onClick={() => createMutation.mutate()} style={primaryButtonStyle}>
          ذخیره
        </button>

        {created && (
          <div style={{ background: "var(--color-amber-bg)", border: "1px solid var(--color-amber-border)", borderRadius: 10, padding: 12, fontSize: 13.5 }}>
            <div>نام کاربری: {created.username}</div>
            <div>رمز: {created.password}</div>
            <div style={{ color: "var(--color-amber-text)", marginTop: 6 }}>این رمز فقط همین حالا خوانا است — یادداشتش کن.</div>
          </div>
        )}
      </div>

      <div style={{ border: "1px solid var(--color-border)", borderRadius: 14, overflow: "hidden" }}>
        {shops?.map((s) => (
          <div key={s.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 16px", borderBottom: "1px solid var(--color-border-soft)" }}>
            <div>
              <div style={{ fontWeight: 600 }}>{s.name}</div>
              <div style={{ fontSize: 12.5, color: "var(--color-text-muted)" }}>{s.username}</div>
            </div>
            <button onClick={() => impersonate(s.id)} style={secondaryButtonStyle}>
              ورود به پنلِ این فروشگاه
            </button>
          </div>
        ))}
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

const secondaryButtonStyle: React.CSSProperties = {
  height: 38,
  borderRadius: 10,
  border: "1px solid var(--color-border)",
  background: "#fff",
  fontSize: 13,
  padding: "0 12px",
};
