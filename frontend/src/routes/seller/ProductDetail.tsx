import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";

interface GarmentType {
  id: number;
  name: string;
}

interface Product {
  id: number;
  name: string;
  garment_type_id: number;
  numbers_kind: "circumference" | "width";
  shop_url: string | null;
  is_active: boolean;
}

export default function ProductDetail() {
  const { id } = useParams();
  const isNew = id === "new" || id === undefined;
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: garmentTypes } = useQuery<GarmentType[]>({
    queryKey: ["garment-types"],
    queryFn: () => apiFetch<GarmentType[]>("/garment-types"),
  });

  const { data: product } = useQuery<Product>({
    queryKey: ["product", id],
    queryFn: () => apiFetch<Product>(`/products/${id}`),
    enabled: !isNew,
  });

  const [name, setName] = useState("");
  const [garmentTypeId, setGarmentTypeId] = useState<number | null>(null);
  const [numbersKind, setNumbersKind] = useState<"circumference" | "width">("circumference");
  const [shopUrl, setShopUrl] = useState("");
  const [switchConfirm, setSwitchConfirm] = useState(false);

  const effectiveName = product?.name ?? name;
  const effectiveGarmentTypeId = product?.garment_type_id ?? garmentTypeId;
  const effectiveNumbersKind = product?.numbers_kind ?? numbersKind;
  const effectiveShopUrl = product?.shop_url ?? shopUrl;

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch<Product>("/products", {
        method: "POST",
        body: JSON.stringify({
          name,
          garment_type_id: garmentTypeId,
          numbers_kind: numbersKind,
        }),
      }),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      navigate(`/panel/products/${created.id}/sizes`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: () =>
      apiFetch(`/products/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ shop_url: effectiveShopUrl || null }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["product", id] }),
  });

  const switchMutation = useMutation({
    mutationFn: (confirm: boolean) =>
      apiFetch(`/products/${id}/numbers-kind`, {
        method: "POST",
        body: JSON.stringify({
          numbers_kind: effectiveNumbersKind === "circumference" ? "width" : "circumference",
          confirm,
        }),
      }),
    onSuccess: () => {
      setSwitchConfirm(false);
      queryClient.invalidateQueries({ queryKey: ["product", id] });
    },
    onError: () => setSwitchConfirm(true),
  });

  const deactivateMutation = useMutation({
    mutationFn: () => apiFetch(`/products/${id}/deactivate`, { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      navigate("/panel");
    },
  });

  if (isNew) {
    return (
      <div style={{ maxWidth: 480, margin: "0 auto", padding: 20 }}>
        <h1 style={{ fontSize: 18 }}>محصولِ تازه</h1>
        <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 16 }}>
          <input placeholder="نامِ محصول" value={name} onChange={(e) => setName(e.target.value)} style={inputStyle} />
          <select
            value={garmentTypeId ?? ""}
            onChange={(e) => setGarmentTypeId(Number(e.target.value))}
            style={inputStyle}
          >
            <option value="">نوعِ پوشاک را انتخاب کن</option>
            {garmentTypes?.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>

          <div>
            <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
              اعدادِ جدولِ سایز از جنسِ دور است یا عرض؟
            </div>
            <div style={{ fontSize: 12.5, color: "var(--color-amber-text)", marginBottom: 8 }}>
              اشتباه‌گرفتنِ این دو، جوابِ محصول را دو برابر غلط می‌کند.
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <ChoiceButton active={numbersKind === "circumference"} onClick={() => setNumbersKind("circumference")}>
                دور
              </ChoiceButton>
              <ChoiceButton active={numbersKind === "width"} onClick={() => setNumbersKind("width")}>
                عرض (نصفِ دور)
              </ChoiceButton>
            </div>
          </div>

          <button
            disabled={!name || !garmentTypeId || createMutation.isPending}
            onClick={() => createMutation.mutate()}
            style={primaryButtonStyle}
          >
            ذخیره
          </button>
        </div>
      </div>
    );
  }

  if (!product) return null;

  return (
    <div style={{ maxWidth: 480, margin: "0 auto", padding: 20 }}>
      <h1 style={{ fontSize: 18 }}>{effectiveName}</h1>
      <div style={{ display: "flex", gap: 14, margin: "16px 0" }}>
        <Link to={`/panel/products/${id}/sizes`} style={tabLink}>
          جدولِ سایز
        </Link>
        <Link to={`/panel/products/${id}/link`} style={tabLink}>
          لینک و نصب
        </Link>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <div style={{ fontSize: 13, color: "var(--color-text-muted)", marginBottom: 6 }}>آدرسِ صفحهٔ محصول در سایتِ فروشگاه (اختیاری)</div>
          <input
            value={effectiveShopUrl ?? ""}
            onChange={(e) => setShopUrl(e.target.value)}
            onBlur={() => updateMutation.mutate()}
            placeholder="https://..."
            style={inputStyle}
          />
        </div>

        <div>
          <div style={{ fontSize: 13, color: "var(--color-text-muted)", marginBottom: 6 }}>
            اعدادِ جدولِ سایز: {effectiveNumbersKind === "circumference" ? "دور" : "عرض"}
          </div>
          {!switchConfirm ? (
            <button onClick={() => switchMutation.mutate(false)} style={secondaryButtonStyle}>
              عوض کردن
            </button>
          ) : (
            <div style={{ background: "var(--color-amber-bg)", border: "1px solid var(--color-amber-border)", borderRadius: 12, padding: 14 }}>
              <div style={{ fontSize: 13.5, marginBottom: 10, color: "var(--color-amber-text)" }}>
                این کار همهٔ اندازه‌های ثبت‌شده را خالی می‌کند. مطمئنی؟
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button onClick={() => switchMutation.mutate(true)} style={primaryButtonStyle}>
                  بله، عوض کن
                </button>
                <button onClick={() => setSwitchConfirm(false)} style={secondaryButtonStyle}>
                  بی‌خیال
                </button>
              </div>
            </div>
          )}
        </div>

        <div style={{ marginTop: 30, borderTop: "1px solid var(--color-border-soft)", paddingTop: 20 }}>
          {!product.is_active ? null : (
            <button
              onClick={() => {
                if (confirm("لینک می‌خوابد ولی دیتای گذشته می‌ماند. مطمئنی؟")) deactivateMutation.mutate();
              }}
              style={{ ...secondaryButtonStyle, color: "#B9772E" }}
            >
              غیرفعال کردنِ این محصول
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function ChoiceButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1,
        height: 56,
        borderRadius: 12,
        border: active ? "2px solid var(--color-accent)" : "1px solid var(--color-border)",
        background: active ? "var(--color-accent-bg)" : "#fff",
        color: active ? "var(--color-accent-hover)" : "var(--color-text)",
        fontSize: 15,
        fontWeight: 600,
      }}
    >
      {children}
    </button>
  );
}

const inputStyle: React.CSSProperties = {
  height: 48,
  borderRadius: 12,
  border: "1px solid var(--color-border)",
  padding: "0 14px",
  fontSize: 15,
  fontFamily: "inherit",
};

const primaryButtonStyle: React.CSSProperties = {
  height: 50,
  borderRadius: 12,
  border: "none",
  background: "var(--color-accent)",
  color: "#fff",
  fontSize: 15,
  fontWeight: 700,
};

const secondaryButtonStyle: React.CSSProperties = {
  height: 44,
  borderRadius: 12,
  border: "1px solid var(--color-border)",
  background: "#fff",
  fontSize: 14,
  fontWeight: 600,
  padding: "0 16px",
};

const tabLink: React.CSSProperties = {
  fontSize: 14,
  color: "var(--color-accent)",
  textDecoration: "none",
};
