import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";

interface RequestRow {
  id: number;
  product_name: string;
  created_at: string;
  status: "answered" | "rejected";
  recommended_size_name: string | null;
  reject_reason: string | null;
}

interface RequestsResponse {
  requests: RequestRow[];
  answered_count: number;
  rejected_count: number;
}

const REJECT_LABEL: Record<string, string> = {
  blurry: "عکس تار است",
  card_not_found: "کارت پیدا نشد",
  garment_cropped: "قسمتی از لباس بیرونِ قاب بود",
};

export default function RequestsList() {
  const { data } = useQuery<RequestsResponse>({
    queryKey: ["requests"],
    queryFn: () => apiFetch<RequestsResponse>("/requests"),
  });

  if (!data) return null;

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: 20 }}>
      <h1 style={{ fontSize: 18 }}>فهرستِ درخواست‌ها</h1>
      <div style={{ display: "flex", gap: 20, margin: "12px 0 20px", fontSize: 14, color: "var(--color-text-secondary)" }}>
        <div>{data.answered_count} جواب داده‌شده</div>
        <div>{data.rejected_count} عکسِ ردشده</div>
      </div>

      {data.requests.length === 0 ? (
        <div style={{ color: "var(--color-text-muted)", fontSize: 15, textAlign: "center", padding: 40 }}>
          هنوز درخواستی نیامده.
        </div>
      ) : (
        <div style={{ border: "1px solid var(--color-border)", borderRadius: 14, overflow: "hidden" }}>
          {data.requests.map((r) => (
            <div
              key={r.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "14px 18px",
                borderBottom: "1px solid var(--color-border-soft)",
                fontSize: 14,
              }}
            >
              <div>{r.product_name}</div>
              <div style={{ color: "var(--color-text-muted)" }}>
                {new Date(r.created_at).toLocaleTimeString("fa-IR", { hour: "2-digit", minute: "2-digit" })}
              </div>
              <div style={{ fontWeight: 600, color: r.status === "answered" ? "var(--color-accent)" : "var(--color-amber-text)" }}>
                {r.status === "answered" ? r.recommended_size_name : REJECT_LABEL[r.reject_reason ?? ""] ?? "عکس رد شد"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
