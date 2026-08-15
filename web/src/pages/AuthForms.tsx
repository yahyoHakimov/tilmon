/**
 * Kirish va ro'yxatdan o'tish shakllari.
 *
 * Xato matni HAR DOIM serverdan olinadi. Frontend o'zidan "bunday email
 * topilmadi" kabi aniqroq xabar yozsa, backend ataylab yashirgan
 * ma'lumotni oshkor qilgan bo'lardi.
 */

import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth";

function Qobiq({
  sarlavha,
  tavsif,
  children,
}: {
  sarlavha: string;
  tavsif?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="auth-page">
      <Link to="/" className="auth-brand">
        Tilmon
      </Link>
      <div className="auth-card">
        <h1>{sarlavha}</h1>
        {tavsif && <p className="auth-sub">{tavsif}</p>}
        {children}
      </div>
    </div>
  );
}

function Xato({ matn }: { matn: string | null }) {
  if (!matn) return null;
  return (
    <div className="notice notice-error" data-testid="auth-error">
      {matn}
    </div>
  );
}

export function Login() {
  const { kir } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [parol, setParol] = useState("");
  const [xato, setXato] = useState<string | null>(null);
  const [yuborilmoqda, setYuborilmoqda] = useState(false);

  async function yubor(e: FormEvent) {
    e.preventDefault();
    setXato(null);
    setYuborilmoqda(true);
    try {
      await kir(email, parol);
      navigate("/app");
    } catch (err) {
      setXato(err instanceof Error ? err.message : "Xatolik yuz berdi.");
    } finally {
      setYuborilmoqda(false);
    }
  }

  return (
    <Qobiq sarlavha="Kirish">
      <form onSubmit={yubor} data-testid="login-form" className="auth-form">
        <Xato matn={xato} />

        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label htmlFor="parol">Parol</label>
        <input
          id="parol"
          type="password"
          autoComplete="current-password"
          value={parol}
          onChange={(e) => setParol(e.target.value)}
          required
        />

        <button type="submit" disabled={yuborilmoqda}>
          {yuborilmoqda ? "Tekshirilmoqda…" : "Kirish"}
        </button>
      </form>

      <p className="auth-alt">
        Akkauntingiz yo'qmi? <Link to="/royxat">Ro'yxatdan o'tish</Link>
      </p>
    </Qobiq>
  );
}

export function Register() {
  const { royxat, registrationOpen } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [parol, setParol] = useState("");
  const [kod, setKod] = useState("");
  const [xato, setXato] = useState<string | null>(null);
  const [yuborilmoqda, setYuborilmoqda] = useState(false);

  async function yubor(e: FormEvent) {
    e.preventDefault();
    setXato(null);
    setYuborilmoqda(true);
    try {
      await royxat(email, parol, kod);
      navigate("/app");
    } catch (err) {
      setXato(err instanceof Error ? err.message : "Xatolik yuz berdi.");
    } finally {
      setYuborilmoqda(false);
    }
  }

  return (
    <Qobiq
      sarlavha="Ro'yxatdan o'tish"
      tavsif={
        registrationOpen
          ? "Tilmon beta bosqichida. Javoblar tavsiya xarakteriga ega."
          : "Tilmon hozircha yopiq betada. Ro'yxatdan o'tish uchun taklif kodi kerak."
      }
    >
      <form onSubmit={yubor} data-testid="register-form" className="auth-form">
        <Xato matn={xato} />

        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label htmlFor="parol">Parol</label>
        <input
          id="parol"
          type="password"
          autoComplete="new-password"
          value={parol}
          onChange={(e) => setParol(e.target.value)}
          required
        />
        <div className="auth-hint">
          Kamida 10 ta belgi, ikki xil belgi turi (harf va raqam).
        </div>

        {!registrationOpen && (
          <>
            <label htmlFor="kod">Taklif kodi</label>
            <input
              id="kod"
              type="text"
              placeholder="TILMON-XXXX-XXXX"
              value={kod}
              onChange={(e) => setKod(e.target.value.toUpperCase())}
              required
            />
          </>
        )}

        <button type="submit" disabled={yuborilmoqda}>
          {yuborilmoqda ? "Yuborilmoqda…" : "Ro'yxatdan o'tish"}
        </button>
      </form>

      <p className="auth-alt">
        Akkauntingiz bormi? <Link to="/kirish">Kirish</Link>
      </p>
    </Qobiq>
  );
}
