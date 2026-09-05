import { useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";

interface ProductPublic {
  shop_name: string;
  product_name: string;
  photo_url: string | null;
  is_active: boolean;
}

type Stage = "start" | "guide" | "processing" | "rejected" | "too-long";

const REJECT_GUIDANCE: Record<string, string> = {
  blurry: "عکس تار است",
  card_not_found: "کارت را در عکس پیدا نکردیم",
  garment_cropped: "قسمتی از لباس بیرونِ قاب است",
};

export default function BuyerFlow() {
  const { linkCode } = useParams();
  const navigate = useNavigate();
  const [stage, setStage] = useState<Stage>("start");
  const [rejectReason, setRejectReason] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: product, isLoading, error } = useQuery<ProductPublic>({
    queryKey: ["public-product", linkCode],
    queryFn: () => apiFetch<ProductPublic>(`/p/${linkCode}`),
    retry: false,
  });

  if (isLoading) return null;

  if (error) {
    return (
      <Screen>
        <Center>
          <div style={{ fontSize: 17, color: "var(--color-text-secondary)", textAlign: "center" }}>
            {(error as Error).message || "پیدا نشد"}
          </div>
        </Center>
      </Screen>
    );
  }

  if (!product) return null;

  async function handleFile(file: File) {
    setStage("processing");
    const form = new FormData();
    form.append("photo", file);
    const timeout = setTimeout(() => setStage("too-long"), 15000);
    try {
      const res = await fetch(`/api/p/${linkCode}/measure`, { method: "POST", body: form });
      clearTimeout(timeout);
      const body = await res.json();
      if (body.status === "rejected") {
        setRejectReason(body.reason);
        setStage("rejected");
      } else if (body.status === "answered") {
        navigate(`/r/${body.view_code}`);
      } else {
        setRejectReason(null);
        setStage("rejected");
      }
    } catch {
      clearTimeout(timeout);
      setStage("too-long");
    }
  }

  if (stage === "start") {
    return (
      <Screen>
        <div style={{ textAlign: "center", fontSize: 15, fontWeight: 600, color: "var(--color-text-secondary)" }}>
          {product.shop_name}
        </div>
        <Center>
          {product.photo_url ? (
            <img src={product.photo_url} alt="" style={{ width: 150, height: 150, borderRadius: 20, objectFit: "cover" }} />
          ) : (
            <div style={{ width: 150, height: 150, borderRadius: 20, background: "var(--color-border-soft)" }} />
          )}
          <div style={{ fontSize: 18.5, lineHeight: 1.85, color: "var(--color-text)", maxWidth: 300, textAlign: "center" }}>
            عکسِ یکی از لباس‌های خودت را بفرست تا بگوییم کدام سایزِ «{product.product_name}» اندازه‌ات است.
          </div>
        </Center>
        <BigButton onClick={() => setStage("guide")}>شروع</BigButton>
        <Footer note="عکست نیم‌ساعت بعد پاک می‌شود" />
      </Screen>
    );
  }

  if (stage === "guide") {
    return (
      <Screen>
        <StepList
          steps={[
            "لباس را روی سطحِ صاف پهن کن",
            "کارتِ ملی، کارتِ مترو یا حتی پشتِ کارتِ بانکی را رویش بگذار — شمارهٔ کارت لازم نیست.",
            "از درست بالای سرش عکس بگیر",
          ]}
        />
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          style={{ display: "none" }}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
        <BigButton onClick={() => fileInputRef.current?.click()}>عکس بگیر یا انتخاب کن</BigButton>
      </Screen>
    );
  }

  if (stage === "processing") {
    return (
      <Screen>
        <Center>
          <Spinner />
          <div style={{ fontSize: 19, color: "var(--color-text)", textAlign: "center" }}>
            داریم لباست را اندازه می‌گیریم…
          </div>
        </Center>
      </Screen>
    );
  }

  if (stage === "too-long") {
    return (
      <Screen>
        <Center>
          <div style={{ fontSize: 17, textAlign: "center", color: "var(--color-text-secondary)" }}>
            کمی طول کشید.
          </div>
          <BigButton onClick={() => setStage("guide")}>دوباره امتحان کن</BigButton>
        </Center>
      </Screen>
    );
  }

  // rejected
  return (
    <Screen>
      <Center>
        <div style={{ fontSize: 18, fontWeight: 700, textAlign: "center" }}>
          {rejectReason ? REJECT_GUIDANCE[rejectReason] ?? "عکس پذیرفته نشد" : "عکس پذیرفته نشد"}
        </div>
        <div style={{ fontSize: 14, color: "var(--color-text-muted)", textAlign: "center" }}>
          دوباره امتحان کن — لباس روی سطحِ صاف، کارت رویش، عکس از بالا.
        </div>
        <BigButton onClick={() => setStage("guide")}>دوباره عکس بگیر</BigButton>
      </Center>
    </Screen>
  );
}

function Screen({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        maxWidth: 420,
        minHeight: "100vh",
        margin: "0 auto",
        display: "flex",
        flexDirection: "column",
        padding: "34px 26px 30px",
        gap: 20,
      }}
    >
      {children}
    </div>
  );
}

function Center({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 18 }}>
      {children}
    </div>
  );
}

function BigButton({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      style={{
        height: 60,
        borderRadius: 15,
        border: "none",
        background: "var(--color-accent)",
        color: "#fff",
        fontSize: 19,
        fontWeight: 700,
      }}
    >
      {children}
    </button>
  );
}

function Footer({ note }: { note: string }) {
  return (
    <div style={{ textAlign: "center", display: "flex", flexDirection: "column", gap: 4 }}>
      <div style={{ fontSize: 13.5, color: "var(--color-text-muted)" }}>{note}</div>
      <div style={{ fontSize: 12.5, color: "var(--color-text-faint)" }}>قدرت‌گرفته از سایز</div>
    </div>
  );
}

function StepList({ steps }: { steps: string[] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, flex: 1, justifyContent: "center" }}>
      {steps.map((s, i) => (
        <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
          <div
            style={{
              width: 30,
              height: 30,
              flex: "none",
              borderRadius: "50%",
              background: "var(--color-accent-bg)",
              color: "var(--color-accent)",
              fontSize: 15,
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {i + 1}
          </div>
          <div style={{ fontSize: 15, lineHeight: 1.75, color: "var(--color-text)" }}>{s}</div>
        </div>
      ))}
    </div>
  );
}

function Spinner() {
  return (
    <div
      style={{
        width: 46,
        height: 46,
        borderRadius: "50%",
        border: "3px solid var(--color-accent-bg-border)",
        borderTopColor: "var(--color-accent)",
        animation: "spin 1.1s linear infinite",
      }}
    >
      <style>{"@keyframes spin { to { transform: rotate(360deg); } }"}</style>
    </div>
  );
}
