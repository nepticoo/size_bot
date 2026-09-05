import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";

interface LinkInfo {
  link_code: string;
  is_active: boolean;
  complete_count: number;
  total_count: number;
}

export default function LinkPage() {
  const { id } = useParams();
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedSnippet, setCopiedSnippet] = useState(false);

  const { data: link } = useQuery<LinkInfo>({
    queryKey: ["link", id],
    queryFn: () => apiFetch<LinkInfo>(`/products/${id}/link`),
  });

  if (!link) return null;

  const url = `${window.location.origin}/p/${link.link_code}`;
  const snippet = `<a href="${url}">سایزم را پیدا کن</a>`;

  function copy(text: string, setFlag: (v: boolean) => void) {
    navigator.clipboard?.writeText(text).then(() => {
      setFlag(true);
      setTimeout(() => setFlag(false), 2000);
    });
  }

  if (!link.is_active) {
    const missing = link.total_count - link.complete_count;
    return (
      <div style={{ maxWidth: 480, margin: "0 auto", padding: 20 }}>
        <h1 style={{ fontSize: 18 }}>لینک و نصب</h1>
        <div
          style={{
            background: "var(--color-accent-bg)",
            border: "1px solid var(--color-accent-bg-border)",
            borderRadius: 12,
            padding: "12px 15px",
            fontSize: 13.5,
            color: "#3B4A63",
            marginTop: 16,
          }}
        >
          اول جدولِ سایز را کامل کن — دورِ کمر و قد (یا دورِ سینه و طولِ لباس) برای همهٔ سایزها لازم است. الان {missing} سایز از {link.total_count} ناقص است.
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 480, margin: "0 auto", padding: 20, display: "flex", flexDirection: "column", gap: 20 }}>
      <h1 style={{ fontSize: 18 }}>لینک و نصب</h1>

      <div>
        <div style={{ fontSize: 13, color: "var(--color-text-muted)", marginBottom: 6 }}>لینکِ محصول</div>
        <div style={{ display: "flex", gap: 8 }}>
          <input readOnly value={url} style={{ flex: 1, height: 44, borderRadius: 10, border: "1px solid var(--color-border)", padding: "0 12px", fontSize: 13 }} />
          <button onClick={() => copy(url, setCopiedLink)} style={buttonStyle}>
            {copiedLink ? "کپی شد" : "کپیِ لینک"}
          </button>
        </div>
      </div>

      <div>
        <div style={{ fontSize: 13, color: "var(--color-text-muted)", marginBottom: 6 }}>قطعهٔ سایت</div>
        <textarea readOnly value={snippet} rows={3} style={{ width: "100%", borderRadius: 10, border: "1px solid var(--color-border)", padding: 12, fontSize: 13, fontFamily: "monospace" }} />
        <button onClick={() => copy(snippet, setCopiedSnippet)} style={{ ...buttonStyle, marginTop: 8 }}>
          {copiedSnippet ? "کپی شد" : "کپیِ قطعه"}
        </button>
      </div>

      <div>
        <div style={{ fontSize: 13, color: "var(--color-text-muted)", marginBottom: 6 }}>پیش‌نمایشِ صفحهٔ خریدار</div>
        <a href={`/p/${link.link_code}`} target="_blank" rel="noreferrer" style={{ color: "var(--color-accent)", fontSize: 14 }}>
          بازکردنِ صفحهٔ خریدار ↗
        </a>
      </div>
    </div>
  );
}

const buttonStyle: React.CSSProperties = {
  height: 44,
  borderRadius: 10,
  border: "1px solid var(--color-border)",
  background: "#fff",
  padding: "0 16px",
  fontSize: 13.5,
  fontWeight: 600,
};
