import { Navigate, Outlet, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";
import { useMe } from "../../lib/useMe";

export default function PanelLayout() {
  const { data: me, isLoading, isError } = useMe();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  if (isLoading) return null;
  if (isError || !me) return <Navigate to="/panel/login" replace />;

  async function logout() {
    await apiFetch("/auth/logout", { method: "POST" });
    queryClient.setQueryData(["me"], undefined);
    navigate("/panel/login");
  }

  const displayName = me.acting_as_shop_name ?? me.shop_name ?? me.username;

  return (
    <div>
      {me.role === "operator" && me.acting_as_shop_name && (
        <div
          style={{
            background: "var(--color-amber-bg)",
            borderBottom: "1px solid var(--color-amber-border)",
            color: "var(--color-amber-text)",
            padding: "10px 20px",
            fontSize: 13.5,
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <span>داری به‌جای «{me.acting_as_shop_name}» کار می‌کنی</span>
          <a href="/admin/shops" style={{ color: "var(--color-amber-text)" }}>
            بازگشت
          </a>
        </div>
      )}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "16px 20px",
          borderBottom: "1px solid var(--color-border-soft)",
        }}
      >
        <b style={{ fontSize: 16 }}>{displayName}</b>
        <button
          onClick={logout}
          style={{ background: "none", border: "none", fontSize: 14, color: "var(--color-text-secondary)" }}
        >
          خروج
        </button>
      </div>
      <Outlet />
    </div>
  );
}
