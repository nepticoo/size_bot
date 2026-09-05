import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      navigate("/panel");
    } catch (err) {
      setError("نام کاربری یا رمز درست نیست.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 360, margin: "60px auto", padding: "0 20px" }}>
      <h1 style={{ fontSize: 20, marginBottom: 24 }}>ورود</h1>
      <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <input
          placeholder="نام کاربری"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={inputStyle}
        />
        <input
          placeholder="رمز"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={inputStyle}
        />
        {error && <div style={{ color: "#B9772E", fontSize: 13.5 }}>{error}</div>}
        <button type="submit" disabled={busy} style={buttonStyle}>
          ورود
        </button>
        <div style={{ fontSize: 12.5, color: "var(--color-text-muted)", textAlign: "center" }}>
          رمزت را فراموش کردی؟ به ما پیام بده.
        </div>
      </form>
    </div>
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

const buttonStyle: React.CSSProperties = {
  height: 52,
  borderRadius: 15,
  border: "none",
  background: "var(--color-accent)",
  color: "#fff",
  fontSize: 17,
  fontWeight: 700,
};
