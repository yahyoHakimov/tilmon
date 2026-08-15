/**
 * Marshrutlash va kirish himoyasi.
 *
 * Himoya ikki qatlamda: backend har so'rovda tekshiradi (asosiy),
 * frontend esa foydalanuvchini to'g'ri sahifaga olib boradi (qulaylik).
 * Frontend himoyasi xavfsizlik chorasi EMAS — u faqat buzuq, bo'sh
 * ekran ko'rsatmaslik uchun.
 */

import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { BrowserRouter } from "react-router-dom";
import type { ReactNode } from "react";

import { AuthProvider, useAuth } from "./auth";
import { Admin } from "./pages/Admin";
import { Classify } from "./pages/Classify";
import { Landing } from "./pages/Landing";
import { Login, Register } from "./pages/AuthForms";

function Yuklanmoqda() {
  return <div className="app splash">Yuklanmoqda…</div>;
}

function Himoyalangan({
  children,
  adminKerak = false,
}: {
  children: ReactNode;
  adminKerak?: boolean;
}) {
  const { user, yuklandi } = useAuth();

  // Tekshiruv tugamaguncha hech narsa ko'rsatilmaydi: aks holda
  // kirgan foydalanuvchi bir lahza kirish sahifasini ko'radi.
  if (!yuklandi) return <Yuklanmoqda />;
  if (!user) return <Navigate to="/kirish" replace />;

  if (adminKerak && user.role !== "admin") {
    return (
      <div className="app" data-testid="forbidden">
        <div className="notice notice-error">
          Bu sahifa uchun administrator huquqi kerak.
        </div>
        <p>
          <Link to="/app">Tasnif sahifasiga qaytish</Link>
        </p>
      </div>
    );
  }
  return <>{children}</>;
}

function Sarlavha() {
  const { user, chiq } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;

  return (
    <header className="topbar">
      <Link to="/app" className="topbar-brand">
        Tilmon
      </Link>
      <div className="topbar-right">
        {user.role === "admin" && (
          <Link to="/admin" className="topbar-link">
            Boshqaruv
          </Link>
        )}
        <span className="topbar-email">{user.email}</span>
        <button
          type="button"
          className="topbar-link"
          data-testid="logout"
          onClick={async () => {
            await chiq();
            navigate("/");
          }}
        >
          Chiqish
        </button>
      </div>
    </header>
  );
}

function LandingYokiIlova() {
  const { user, yuklandi, registrationOpen } = useAuth();
  const navigate = useNavigate();

  if (!yuklandi) return <Yuklanmoqda />;
  // Kirgan foydalanuvchi uchun landing ma'nosiz — to'g'ridan ilovaga.
  if (user) return <Navigate to="/app" replace />;

  return (
    <Landing
      onLogin={() => navigate("/kirish")}
      onRegister={() => navigate("/royxat")}
      registrationOpen={registrationOpen}
    />
  );
}

function Marshrutlar() {
  return (
    <>
      <Sarlavha />
      <Routes>
        <Route path="/" element={<LandingYokiIlova />} />
        <Route path="/kirish" element={<Login />} />
        <Route path="/royxat" element={<Register />} />
        <Route
          path="/app"
          element={
            <Himoyalangan>
              <Classify />
            </Himoyalangan>
          }
        />
        <Route
          path="/admin"
          element={
            <Himoyalangan adminKerak>
              <Admin />
            </Himoyalangan>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

/** Testlar uchun: o'z routerini beradigan variant. */
export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Marshrutlar />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
