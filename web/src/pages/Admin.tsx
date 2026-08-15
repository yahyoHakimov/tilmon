/**
 * Administrator paneli.
 *
 * MVP doirasi ataylab tor: foydalanuvchilarni ko'rish/bloklash va
 * taklif kodlari yaratish. Ontologiyani tahrirlash bu yerda YO'Q —
 * u audit jurnali va tahrir tarixi talab qiladi, va o'sha ishlar
 * qilinmaguncha huquqiy matnni brauzerdan o'zgartirish xavfli.
 */

import { useCallback, useEffect, useState } from "react";

interface AdminUser {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

interface Invite {
  code: string;
  note: string | null;
  created_at: string;
  expires_at: string | null;
  used_at: string | null;
  used_by: string | null;
}

const sana = (s: string | null) =>
  s ? new Date(s).toLocaleDateString("uz-UZ") : "—";

export function Admin() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [izoh, setIzoh] = useState("");
  const [xato, setXato] = useState<string | null>(null);

  const yukla = useCallback(async () => {
    try {
      const [u, i] = await Promise.all([
        fetch("/api/admin/users"),
        fetch("/api/admin/invites"),
      ]);
      if (u.ok) setUsers((await u.json()).users);
      if (i.ok) setInvites((await i.json()).invites);
    } catch {
      setXato("Ma'lumotni yuklab bo'lmadi.");
    }
  }, []);

  useEffect(() => {
    void yukla();
  }, [yukla]);

  async function kodYarat() {
    setXato(null);
    const r = await fetch("/api/admin/invites", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note: izoh || null }),
    });
    if (!r.ok) {
      setXato("Kod yaratib bo'lmadi.");
      return;
    }
    setIzoh("");
    await yukla();
  }

  async function holatOzgartir(u: AdminUser) {
    const amal = u.is_active ? "block" : "unblock";
    const r = await fetch(`/api/admin/users/${u.id}/${amal}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    if (!r.ok) {
      const b = await r.json().catch(() => ({}));
      setXato(b.detail ?? "Amalni bajarib bo'lmadi.");
      return;
    }
    await yukla();
  }

  return (
    <div className="app" data-testid="admin-page">
      <h2 className="admin-h">Taklif kodlari</h2>

      {xato && <div className="notice notice-error">{xato}</div>}

      <div className="admin-new">
        <input
          type="text"
          placeholder="Kim uchun (ixtiyoriy eslatma)"
          value={izoh}
          onChange={(e) => setIzoh(e.target.value)}
        />
        <button type="button" onClick={kodYarat} data-testid="new-invite">
          Yangi kod
        </button>
      </div>

      <table className="admin-table">
        <thead>
          <tr>
            <th>Kod</th>
            <th>Izoh</th>
            <th>Holat</th>
            <th>Kim ishlatdi</th>
          </tr>
        </thead>
        <tbody>
          {invites.map((k) => (
            <tr key={k.code}>
              <td>
                <code>{k.code}</code>
              </td>
              <td>{k.note ?? "—"}</td>
              <td>{k.used_at ? "ishlatilgan" : "bo'sh"}</td>
              <td>{k.used_by ?? "—"}</td>
            </tr>
          ))}
          {invites.length === 0 && (
            <tr>
              <td colSpan={4} className="admin-empty">
                Hali kod yaratilmagan.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <h2 className="admin-h">Foydalanuvchilar</h2>
      <table className="admin-table">
        <thead>
          <tr>
            <th>Email</th>
            <th>Rol</th>
            <th>Holat</th>
            <th>Oxirgi kirish</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.email}</td>
              <td>{u.role}</td>
              <td>{u.is_active ? "faol" : "bloklangan"}</td>
              <td>{sana(u.last_login_at)}</td>
              <td>
                <button
                  type="button"
                  className="admin-act"
                  onClick={() => holatOzgartir(u)}
                >
                  {u.is_active ? "bloklash" : "blokni yechish"}
                </button>
              </td>
            </tr>
          ))}
          {users.length === 0 && (
            <tr>
              <td colSpan={5} className="admin-empty">
                Foydalanuvchilar yo'q.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
