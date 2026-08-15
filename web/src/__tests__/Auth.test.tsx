/**
 * 14-bosqich: Frontend auth va marshrutlash.
 *
 * Eng muhim test — himoyalangan sahifaga kirishsiz tushib bo'lmasligi.
 * Backend baribir 401 qaytaradi, lekin UI darajasidagi himoya ham kerak:
 * aks holda foydalanuvchi bo'sh, buzuq ekranni ko'radi va nima
 * qilishini bilmaydi.
 *
 * Ikkinchi muhim narsa — 401 javobiga munosabat. Sessiya muddati
 * tugaganda ilova jimgina "xato" ko'rsatmasligi, kirish sahifasiga
 * olib borishi kerak.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../App";

const FOYDALANUVCHI = {
  id: "u-1",
  email: "tadbirkor@example.uz",
  role: "user",
  created_at: "2026-08-15T00:00:00Z",
};

function javob(status: number, tana: unknown = {}) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => tana,
  };
}

/** `/api/auth/me` javobini belgilaydi, qolganini yo'lga qarab. */
function fetchni_soxtalashtir(marshrutlar: Record<string, () => unknown>) {
  const mock = vi.fn(async (url: string, init?: RequestInit) => {
    const kalit = `${init?.method ?? "GET"} ${url}`;
    const h = marshrutlar[kalit] ?? marshrutlar[url];
    if (!h) throw new Error(`kutilmagan so'rov: ${kalit}`);
    return h();
  });
  vi.stubGlobal("fetch", mock);
  return mock;
}

const chiqar = (yol = "/") => {
  window.history.pushState({}, "", yol);
  return render(<App />);
};

beforeEach(() => {
  vi.restoreAllMocks();
  window.history.pushState({}, "", "/");
});

// --- ⭐ Himoyalangan marshrutlar --------------------------------------------

describe("himoyalangan marshrutlar", () => {
  it("kirishsiz /app kirish sahifasiga yo'naltiradi", async () => {
    fetchni_soxtalashtir({ "GET /api/auth/me": () => javob(401) });
    chiqar("/app");
    await waitFor(() =>
      expect(screen.getByTestId("login-form")).toBeInTheDocument(),
    );
    expect(screen.queryByRole("textbox", { name: /tovar/i })).toBeNull();
  });

  it("kirishsiz /admin kirish sahifasiga yo'naltiradi", async () => {
    fetchni_soxtalashtir({ "GET /api/auth/me": () => javob(401) });
    chiqar("/admin");
    await waitFor(() =>
      expect(screen.getByTestId("login-form")).toBeInTheDocument(),
    );
  });

  it("kirgan foydalanuvchi /app ni ko'radi", async () => {
    fetchni_soxtalashtir({
      "GET /api/auth/me": () => javob(200, FOYDALANUVCHI),
    });
    chiqar("/app");
    await waitFor(() =>
      expect(screen.getByTestId("classify-form")).toBeInTheDocument(),
    );
  });

  it("⭐ oddiy foydalanuvchi /admin ni KO'RA OLMAYDI", async () => {
    fetchni_soxtalashtir({
      "GET /api/auth/me": () => javob(200, FOYDALANUVCHI),
    });
    chiqar("/admin");
    await waitFor(() =>
      expect(screen.getByTestId("forbidden")).toBeInTheDocument(),
    );
  });

  it("admin /admin ni ko'radi", async () => {
    fetchni_soxtalashtir({
      "GET /api/auth/me": () => javob(200, { ...FOYDALANUVCHI, role: "admin" }),
      "GET /api/admin/users": () => javob(200, { users: [] }),
      "GET /api/admin/invites": () => javob(200, { invites: [] }),
    });
    chiqar("/admin");
    await waitFor(() =>
      expect(screen.getByTestId("admin-page")).toBeInTheDocument(),
    );
  });
});

// --- Landing ----------------------------------------------------------------

describe("landing", () => {
  it("ildiz sahifasi ochiq", async () => {
    fetchni_soxtalashtir({ "GET /api/auth/me": () => javob(401) });
    chiqar("/");
    await waitFor(() =>
      expect(screen.getByTestId("disclaimer")).toBeInTheDocument(),
    );
  });

  it("kirgan foydalanuvchi ildizdan ilovaga o'tadi", async () => {
    fetchni_soxtalashtir({
      "GET /api/auth/me": () => javob(200, FOYDALANUVCHI),
    });
    chiqar("/");
    await waitFor(() =>
      expect(screen.getByTestId("classify-form")).toBeInTheDocument(),
    );
  });
});

// --- Kirish -----------------------------------------------------------------

describe("kirish", () => {
  it("to'g'ri ma'lumot bilan ilovaga o'tadi", async () => {
    let kirgan = false;
    fetchni_soxtalashtir({
      "GET /api/auth/me": () => (kirgan ? javob(200, FOYDALANUVCHI) : javob(401)),
      "POST /api/auth/login": () => {
        kirgan = true;
        return javob(200, FOYDALANUVCHI);
      },
    });
    chiqar("/kirish");

    await userEvent.type(screen.getByLabelText(/email/i), "a@b.uz");
    await userEvent.type(screen.getByLabelText(/parol/i), "Bluzka-6106-trikotaj");
    await userEvent.click(screen.getByRole("button", { name: /^Kirish$/ }));

    await waitFor(() =>
      expect(screen.getByTestId("classify-form")).toBeInTheDocument(),
    );
  });

  it("xato ma'lumotda xabar ko'rsatadi va sahifada qoladi", async () => {
    fetchni_soxtalashtir({
      "GET /api/auth/me": () => javob(401),
      "POST /api/auth/login": () =>
        javob(401, { detail: "Email yoki parol noto'g'ri." }),
    });
    chiqar("/kirish");

    await userEvent.type(screen.getByLabelText(/email/i), "a@b.uz");
    await userEvent.type(screen.getByLabelText(/parol/i), "notogri-parol");
    await userEvent.click(screen.getByRole("button", { name: /^Kirish$/ }));

    await waitFor(() =>
      expect(screen.getByTestId("auth-error")).toHaveTextContent(/noto'g'ri/i),
    );
    expect(screen.getByTestId("login-form")).toBeInTheDocument();
  });

  it("⭐ server xabarini o'zi o'ylab topmaydi", async () => {
    /**
     * Xato matni serverdan keladi. Frontend o'zidan "email topilmadi"
     * kabi aniqroq xabar yozsa, backend ataylab yashirgan ma'lumotni
     * oshkor qilgan bo'lardi.
     */
    fetchni_soxtalashtir({
      "GET /api/auth/me": () => javob(401),
      "POST /api/auth/login": () =>
        javob(401, { detail: "Email yoki parol noto'g'ri." }),
    });
    chiqar("/kirish");
    await userEvent.type(screen.getByLabelText(/email/i), "a@b.uz");
    await userEvent.type(screen.getByLabelText(/parol/i), "x");
    await userEvent.click(screen.getByRole("button", { name: /^Kirish$/ }));

    await waitFor(() => screen.getByTestId("auth-error"));
    const matn = screen.getByTestId("auth-error").textContent ?? "";
    expect(matn).not.toMatch(/topilmadi|mavjud emas|ro'yxatdan o'tmagan/i);
  });
});

// --- Ro'yxatdan o'tish ------------------------------------------------------

describe("ro'yxatdan o'tish", () => {
  it("taklif kodi maydonini so'raydi", async () => {
    fetchni_soxtalashtir({ "GET /api/auth/me": () => javob(401) });
    chiqar("/royxat");
    await waitFor(() => screen.getByTestId("register-form"));
    expect(screen.getByLabelText(/taklif kodi/i)).toBeInTheDocument();
  });

  it("muvaffaqiyatli ro'yxatdan keyin ilovaga o'tadi", async () => {
    let kirgan = false;
    fetchni_soxtalashtir({
      "GET /api/auth/me": () => (kirgan ? javob(200, FOYDALANUVCHI) : javob(401)),
      "POST /api/auth/register": () => {
        kirgan = true;
        return javob(201, FOYDALANUVCHI);
      },
    });
    chiqar("/royxat");

    await userEvent.type(screen.getByLabelText(/email/i), "a@b.uz");
    await userEvent.type(screen.getByLabelText(/^parol/i), "Bluzka-6106-trikotaj");
    await userEvent.type(screen.getByLabelText(/taklif kodi/i), "TILMON-ABCD-2345");
    await userEvent.click(
      screen.getByRole("button", { name: /Ro'yxatdan o'tish/ }),
    );

    await waitFor(() =>
      expect(screen.getByTestId("classify-form")).toBeInTheDocument(),
    );
  });

  it("noto'g'ri kod xabari ko'rsatiladi", async () => {
    fetchni_soxtalashtir({
      "GET /api/auth/me": () => javob(401),
      "POST /api/auth/register": () =>
        javob(400, { detail: "Taklif kodi noto'g'ri yoki muddati o'tgan." }),
    });
    chiqar("/royxat");

    await userEvent.type(screen.getByLabelText(/email/i), "a@b.uz");
    await userEvent.type(screen.getByLabelText(/^parol/i), "Bluzka-6106-trikotaj");
    await userEvent.type(screen.getByLabelText(/taklif kodi/i), "TILMON-YOQ-KOD");
    await userEvent.click(
      screen.getByRole("button", { name: /Ro'yxatdan o'tish/ }),
    );

    await waitFor(() =>
      expect(screen.getByTestId("auth-error")).toHaveTextContent(/taklif kodi/i),
    );
  });
});

// --- Chiqish ----------------------------------------------------------------

describe("chiqish", () => {
  it("chiqishdan keyin landing ko'rinadi", async () => {
    let kirgan = true;
    fetchni_soxtalashtir({
      "GET /api/auth/me": () => (kirgan ? javob(200, FOYDALANUVCHI) : javob(401)),
      "POST /api/auth/logout": () => {
        kirgan = false;
        return javob(204);
      },
    });
    chiqar("/app");
    await waitFor(() => screen.getByTestId("classify-form"));

    await userEvent.click(screen.getByTestId("logout"));
    await waitFor(() =>
      expect(screen.getByTestId("disclaimer")).toBeInTheDocument(),
    );
  });
});
