/**
 * Landing sahifasidagi interaktiv demo.
 *
 * Demo mahsulotni TUSHUNTIRMAYDI — KO'RSATADI. Tashrif buyuruvchi
 * ro'yxatdan o'tmasdan turib tizimning eng muhim xususiyatini o'z
 * ko'zi bilan ko'radi: ma'lumot yetarli bo'lmaganda kod berilmaydi,
 * savol beriladi.
 *
 * Shu sababli bu yerdagi asosiy test — demo'ning O'ZI ham jim
 * turishi. Agar marketing uchun "chiroyliroq" qilib, demo darhol
 * kod ko'rsatadigan qilinsa, sahifa mahsulot haqida yolg'on
 * gapirgan bo'ladi.
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { Landing } from "../pages/Landing";

const chiqar = () =>
  render(<Landing onLogin={() => {}} onRegister={() => {}} />);

const demo = () => screen.getByTestId("demo");

// --- ⭐ Demo ham jim turadi -------------------------------------------------

describe("demo — jim turish", () => {
  it("boshlang'ich holatda KOD KO'RSATMAYDI", () => {
    chiqar();
    expect(within(demo()).queryByTestId("demo-code")).toBeNull();
  });

  it("boshlang'ich holatda savol ko'rsatadi", () => {
    chiqar();
    expect(within(demo()).getByTestId("demo-question")).toBeInTheDocument();
  });

  it("savol bilan birga nima xavf ostidaligini ko'rsatadi", () => {
    chiqar();
    const d = demo();
    expect(within(d).getByText(/6106/)).toBeInTheDocument();
    expect(within(d).getByText(/6206/)).toBeInTheDocument();
  });

  it("javob variantlari tugma sifatida beriladi", () => {
    chiqar();
    expect(within(demo()).getAllByTestId("demo-option").length).toBeGreaterThan(1);
  });
});

// --- Sikl -------------------------------------------------------------------

describe("demo — savol-javob sikli", () => {
  it("javob berilgach keyingi savolga o'tadi", async () => {
    chiqar();
    const birinchi = within(demo()).getByTestId("demo-question").textContent;

    await userEvent.click(within(demo()).getAllByTestId("demo-option")[0]);

    await waitFor(() =>
      expect(within(demo()).getByTestId("demo-question").textContent).not.toBe(
        birinchi,
      ),
    );
    expect(within(demo()).queryByTestId("demo-code")).toBeNull();
  });

  it("⭐ barcha savollarga javob berilgach kod chiqadi", async () => {
    chiqar();
    await userEvent.click(within(demo()).getAllByTestId("demo-option")[0]);
    await waitFor(() => within(demo()).getByTestId("demo-question"));
    await userEvent.click(within(demo()).getAllByTestId("demo-option")[0]);

    await waitFor(() =>
      expect(within(demo()).getByTestId("demo-code")).toHaveTextContent(
        "6106 10 000 0",
      ),
    );
  });

  it("kod bilan birga huquqiy asos ko'rsatiladi", async () => {
    chiqar();
    await userEvent.click(within(demo()).getAllByTestId("demo-option")[0]);
    await waitFor(() => within(demo()).getByTestId("demo-question"));
    await userEvent.click(within(demo()).getAllByTestId("demo-option")[0]);

    await waitFor(() => within(demo()).getByTestId("demo-code"));
    expect(within(demo()).getAllByTestId("demo-citation").length).toBeGreaterThan(0);
  });

  it("demoda ham tasdiqlanmagan bayrog'i ko'rinadi", async () => {
    chiqar();
    await userEvent.click(within(demo()).getAllByTestId("demo-option")[0]);
    await waitFor(() => within(demo()).getByTestId("demo-question"));
    await userEvent.click(within(demo()).getAllByTestId("demo-option")[0]);

    await waitFor(() => within(demo()).getByTestId("demo-code"));
    expect(
      within(demo()).getAllByTestId("demo-unverified").length,
    ).toBeGreaterThan(0);
  });

  it("boshqa tarmoq boshqa kodga olib boradi", async () => {
    /** «to'qima» tanlansa 6206 chiqishi kerak — demoning butun mazmuni shu. */
    chiqar();
    const variantlar = within(demo()).getAllByTestId("demo-option");
    await userEvent.click(variantlar[1]); // to'qima

    await waitFor(() => within(demo()).getByTestId("demo-question"));
    await userEvent.click(within(demo()).getAllByTestId("demo-option")[0]);

    await waitFor(() =>
      expect(within(demo()).getByTestId("demo-code")).toHaveTextContent("6206"),
    );
  });
});

// --- Boshqarish -------------------------------------------------------------

describe("demo — boshqarish", () => {
  it("qayta boshlash boshlang'ich holatga qaytaradi", async () => {
    chiqar();
    await userEvent.click(within(demo()).getAllByTestId("demo-option")[0]);
    await waitFor(() => within(demo()).getByTestId("demo-question"));
    await userEvent.click(within(demo()).getAllByTestId("demo-option")[0]);
    await waitFor(() => within(demo()).getByTestId("demo-code"));

    await userEvent.click(within(demo()).getByTestId("demo-reset"));

    await waitFor(() =>
      expect(within(demo()).queryByTestId("demo-code")).toBeNull(),
    );
    expect(within(demo()).getByTestId("demo-question")).toBeInTheDocument();
  });

  it("bosilgan javoblar ko'rinib turadi", async () => {
    chiqar();
    await userEvent.click(within(demo()).getAllByTestId("demo-option")[0]);
    await waitFor(() =>
      expect(within(demo()).getAllByTestId("demo-answered").length).toBe(1),
    );
  });

  it("boshqa misolga o'tish mumkin", async () => {
    chiqar();
    const misollar = within(demo()).getAllByTestId("demo-preset");
    expect(misollar.length).toBeGreaterThan(1);

    await userEvent.click(misollar[1]);
    await waitFor(() =>
      expect(within(demo()).getByTestId("demo-input")).toHaveTextContent(
        /paxta|trikotaj|smartfon/i,
      ),
    );
  });

  it("to'liq tavsifli misol darhol kod beradi", async () => {
    chiqar();
    const misollar = within(demo()).getAllByTestId("demo-preset");
    await userEvent.click(misollar[1]);
    await waitFor(() =>
      expect(within(demo()).getByTestId("demo-code")).toBeInTheDocument(),
    );
  });
});
