/**
 * Kirish holati.
 *
 * Sessiya cookie'da (HttpOnly) — JavaScript uni o'qiy olmaydi va bu
 * ataylab: XSS hujumida token o'g'irlanmasligi uchun. Frontend faqat
 * `/api/auth/me` orqali "kirganmanmi?" degan savolga javob oladi.
 *
 * Ya'ni bu yerda token saqlanmaydi, `localStorage` ishlatilmaydi.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

export interface Foydalanuvchi {
  id: string;
  email: string;
  role: "user" | "admin";
  created_at: string;
}

interface AuthHolati {
  user: Foydalanuvchi | null;
  /** Ro'yxatdan o'tish taklif kodisiz mumkinmi (serverdan). */
  registrationOpen: boolean;
  /** Boshlang'ich tekshiruv tugadimi. Tugamaguncha hech narsa ko'rsatilmaydi. */
  yuklandi: boolean;
  kir: (email: string, parol: string) => Promise<void>;
  royxat: (email: string, parol: string, kod: string) => Promise<void>;
  chiq: () => Promise<void>;
}

const Kontekst = createContext<AuthHolati | null>(null);

/** Serverdagi xato matnini oladi. Frontend o'zidan xabar TO'QIMAYDI. */
async function xatoMatni(r: Response, zaxira: string): Promise<string> {
  try {
    const b = await r.json();
    if (typeof b?.detail === "string") return b.detail;
    // Pydantic validatsiya xatolari ro'yxat ko'rinishida keladi.
    if (Array.isArray(b?.detail) && b.detail[0]?.msg) {
      return String(b.detail[0].msg).replace(/^Value error,\s*/, "");
    }
  } catch {
    /* JSON emas — zaxira matn ishlatiladi */
  }
  return zaxira;
}

async function post(yol: string, tana: unknown): Promise<Response> {
  return fetch(yol, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(tana),
  });
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Foydalanuvchi | null>(null);
  const [yuklandi, setYuklandi] = useState(false);
  // Sukut bo'yicha YOPIQ: server javob bermaguncha taklif kodi
  // so'raladi. Aks holda maydon bir lahza yo'qolib, keyin paydo bo'ladi.
  const [registrationOpen, setRegistrationOpen] = useState(false);

  const yangila = useCallback(async () => {
    try {
      const r = await fetch("/api/auth/me");
      setUser(r.ok ? await r.json() : null);
    } catch {
      setUser(null);
    } finally {
      setYuklandi(true);
    }
  }, []);

  useEffect(() => {
    void yangila();
  }, [yangila]);

  useEffect(() => {
    fetch("/api/auth/config")
      .then((r) => (r.ok ? r.json() : null))
      .then((b) => setRegistrationOpen(Boolean(b?.registration_open)))
      .catch(() => setRegistrationOpen(false));
  }, []);

  const kir = useCallback(
    async (email: string, parol: string) => {
      const r = await post("/api/auth/login", { email, password: parol });
      if (!r.ok) {
        throw new Error(await xatoMatni(r, "Kirishda xatolik yuz berdi."));
      }
      await yangila();
    },
    [yangila],
  );

  const royxat = useCallback(
    async (email: string, parol: string, kod: string) => {
      const r = await post("/api/auth/register", {
        email,
        password: parol,
        // Bo'sh kod yuborilmaydi: ochiq rejimda u ixtiyoriy, yopiq
        // rejimda esa server aniq xato beradi.
        ...(kod.trim() ? { invite_code: kod.trim() } : {}),
      });
      if (!r.ok) {
        throw new Error(
          await xatoMatni(r, "Ro'yxatdan o'tishda xatolik yuz berdi."),
        );
      }
      await yangila();
    },
    [yangila],
  );

  const chiq = useCallback(async () => {
    await post("/api/auth/logout", {});
    await yangila();
  }, [yangila]);

  return (
    <Kontekst.Provider
      value={{ user, yuklandi, registrationOpen, kir, royxat, chiq }}
    >
      {children}
    </Kontekst.Provider>
  );
}

export function useAuth(): AuthHolati {
  const k = useContext(Kontekst);
  if (!k) throw new Error("useAuth faqat <AuthProvider> ichida ishlaydi");
  return k;
}
