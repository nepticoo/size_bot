import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";

interface SizeAnswer {
  id: number;
  name: string;
  fit_word: string;
  is_recommended: boolean;
}

interface Answer {
  status: "answered" | "no_fit";
  shop_name: string;
  product_name: string;
  shop_url: string | null;
  recommended_size?: { id: number; name: string };
  nearest_size?: { id: number; name: string };
  nearest_direction?: "tight" | "loose";
  sizes: SizeAnswer[];
  length_note: string | null;
  secondary_notes: string[];
}

export default function AnswerPage() {
  const { viewCode } = useParams();
  const [copied, setCopied] = useState(false);

  const { data, isLoading, error } = useQuery<Answer>({
    queryKey: ["answer", viewCode],
    queryFn: () => apiFetch<Answer>(`/r/${viewCode}`),
    retry: false,
  });

  if (isLoading) return null;

  if (error) {
    const message = (error as Error).message || "";
    const expired = message.includes("پاک شده") || message.includes("410");
    return (
      <div style={{ maxWidth: 420, margin: "0 auto", padding: "60px 26px", textAlign: "center" }}>
        <div style={{ fontSize: 17, lineHeight: 1.8, marginBottom: 24 }}>
          {expired ? "این جواب پاک شده — عکس‌ها را بیشتر از نیم‌ساعت نگه نمی‌داریم." : "پیدا نشد"}
        </div>
        <a href="/" style={{ color: "var(--color-accent)" }}>
          از اول شروع کن
        </a>
      </div>
    );
  }

  if (!data) return null;

  function copyLink() {
    navigator.clipboard?.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div style={{ maxWidth: 420, margin: "0 auto", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "18px 26px", borderBottom: "1px solid var(--color-border-soft)", fontSize: 13, color: "var(--color-text-muted)" }}>
        {data.shop_name} · {data.product_name}
      </div>

      <div style={{ padding: 22 }}>
        {data.status === "answered" && data.recommended_size ? (
          <div
            style={{
              background: "var(--color-accent-bg)",
              border: "1px solid var(--color-accent-bg-border)",
              borderRadius: 18,
              padding: "22px 22px 24px",
              display: "flex",
              flexDirection: "column",
              gap: 12,
            }}
          >
            <div
              style={{
                alignSelf: "flex-start",
                background: "var(--color-accent)",
                color: "#fff",
                fontSize: 12.5,
                fontWeight: 700,
                padding: "5px 11px",
                borderRadius: 999,
              }}
            >
              پیشنهادِ ما
            </div>
            <div style={{ fontSize: 34, fontWeight: 800, color: "var(--color-accent-hover)" }}>
              {data.recommended_size.name}
            </div>
          </div>
        ) : (
          <div style={{ background: "var(--color-amber-bg)", border: `1px solid var(--color-amber-border)`, borderRadius: 18, padding: 20 }}>
            <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 8 }}>این محصول در اندازهٔ تو موجود نیست.</div>
            {data.nearest_size && (
              <div style={{ fontSize: 14.5, color: "var(--color-amber-text)" }}>
                نزدیک‌ترین سایز {data.nearest_size.name} است، ولی برایت{" "}
                {data.nearest_direction === "tight" ? "تنگ" : "گشاد"} می‌شود.
              </div>
            )}
          </div>
        )}

        {(data.length_note || data.secondary_notes.length > 0) && (
          <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 8 }}>
            {data.length_note && (
              <div style={{ fontSize: 14.5, lineHeight: 1.8, color: "var(--color-text)", fontWeight: 600 }}>
                {data.length_note}
              </div>
            )}
            {data.secondary_notes.map((n, i) => (
              <div key={i} style={{ fontSize: 14.5, lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                {n}
              </div>
            ))}
          </div>
        )}

        <div style={{ marginTop: 24 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: "var(--color-text-muted)", marginBottom: 10 }}>
            همهٔ سایزهای این محصول
          </div>
          <div style={{ border: "1px solid var(--color-border)", borderRadius: 16, overflow: "hidden" }}>
            {data.sizes.map((s) => (
              <div
                key={s.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "16px 18px",
                  borderBottom: "1px solid var(--color-border-soft)",
                  background: s.is_recommended ? "var(--color-accent-bg)" : "transparent",
                  borderRight: s.is_recommended ? "4px solid var(--color-accent)" : "none",
                }}
              >
                <div style={{ fontSize: 17, fontWeight: 700, color: s.is_recommended ? "var(--color-accent-hover)" : "var(--color-text)" }}>
                  {s.name}
                </div>
                <div style={{ fontSize: 15.5, color: s.is_recommended ? "var(--color-accent)" : "var(--color-text-secondary)", fontWeight: s.is_recommended ? 600 : 400 }}>
                  {s.fit_word}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 12 }}>
          {data.shop_url && (
            <a
              href={data.shop_url}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: 58,
                borderRadius: 15,
                background: "var(--color-accent)",
                color: "#fff",
                fontSize: 18.5,
                fontWeight: 700,
                textDecoration: "none",
              }}
            >
              برگرد و خرید کن
            </a>
          )}
          <button
            onClick={copyLink}
            style={{
              height: 50,
              borderRadius: 15,
              border: "1px solid var(--color-border)",
              background: "#fff",
              fontSize: 15,
              color: "var(--color-text)",
            }}
          >
            {copied ? "کپی شد" : "کپیِ لینکِ این جواب"}
          </button>
          <div style={{ textAlign: "center", fontSize: 12.5, color: "var(--color-text-muted)" }}>
            تا نیم‌ساعت با این لینک برمی‌گردی
          </div>
          <div style={{ textAlign: "center", fontSize: 12.5, color: "var(--color-text-faint)" }}>قدرت‌گرفته از سایز</div>
        </div>
      </div>
    </div>
  );
}
