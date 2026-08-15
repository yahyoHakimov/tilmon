/**
 * 6-bosqich: UI kafolatlari.
 *
 * Backend to'g'ri ishlashi yetarli emas. Agar UI to'liqmas javobdagi
 * nomzod kodni javob kabi ko'rsatsa, foydalanuvchi uni deklaratsiyaga
 * yozadi va tizimning butun ehtiyotkorligi behuda ketadi.
 *
 * Shuning uchun bu yerdagi asosiy test — "kod ko'rinmaydi" emas,
 * "kod JAVOB SIFATIDA ko'rinmaydi". Nomzodlar ko'rinishi kerak, lekin
 * ular ehtimol ekani aniq belgilangan bo'lishi shart.
 *
 * Fixture backend'dan generatsiya qilinadi (scripts/gen_fixtures.py),
 * shuning uchun bu testlar API kontraktidan ajralib keta olmaydi.
 */

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { Result } from "../components/Result";
import fixtures from "./fixtures.json";
import type { ClassifyResponse, InsufficientResponse, ResolvedResponse } from "../types";

const resolved = fixtures.resolved as unknown as ResolvedResponse;
const insufficient = fixtures.insufficient as unknown as InsufficientResponse;
const empty = fixtures.empty as unknown as InsufficientResponse;

const chiqar = (javob: ClassifyResponse) => render(<Result data={javob} />);

// --- Fixture haqiqiyligi ---------------------------------------------------

describe("fixture", () => {
  it("backend to'liqmas javobda kod maydonini umuman bermaydi", () => {
    expect("code" in insufficient).toBe(false);
    expect("code" in empty).toBe(false);
    expect("code" in resolved).toBe(true);
  });
});

// --- Aniqlangan kod --------------------------------------------------------

describe("aniqlangan kod", () => {
  it("yakuniy kodni ko'rsatadi", () => {
    chiqar(resolved);
    expect(screen.getByTestId("final-code")).toHaveTextContent("6106 10 000 0");
  });

  it("tovar nomi va boj stavkasini ko'rsatadi", () => {
    chiqar(resolved);
    // Aynan javob blokidagi nom — bir xil matn iqtiboslar orasida ham uchraydi.
    expect(screen.getByTestId("final-title")).toHaveTextContent(resolved.title_uz);
    expect(screen.getByTestId("duty-rate")).toHaveTextContent("10");
  });

  it("ishonch darajasini ko'rsatadi", () => {
    chiqar(resolved);
    expect(screen.getByTestId("confidence")).toHaveTextContent(/yuqori|o'rta/);
  });

  it("asos zanjirining har bir qadamini ko'rsatadi", () => {
    chiqar(resolved);
    const qadamlar = screen.getAllByTestId("evidence-step");
    expect(qadamlar).toHaveLength(resolved.evidence.steps.length);
  });

  it("har bir iqtibosni manba ishorasi bilan ko'rsatadi", () => {
    chiqar(resolved);
    const birinchi = resolved.evidence.steps[0].citations[0];
    expect(screen.getAllByText(birinchi.ref)[0]).toBeInTheDocument();
    expect(screen.getAllByText(birinchi.text)[0]).toBeInTheDocument();
  });
});

// --- ⭐ Ma'lumot yetarli emas ----------------------------------------------

describe("ma'lumot yetarli emas", () => {
  it("YAKUNIY KOD BLOKINI UMUMAN CHIQARMAYDI", () => {
    chiqar(insufficient);
    expect(screen.queryByTestId("final-code")).toBeNull();
    expect(screen.queryByTestId("duty-rate")).toBeNull();
    expect(screen.queryByTestId("confidence")).toBeNull();
  });

  it("yetishmayotgan ma'lumot haqidagi savolni ko'rsatadi", () => {
    chiqar(insufficient);
    expect(screen.getByTestId("question")).toHaveTextContent(
      insufficient.question_uz.trim().slice(0, 30),
    );
  });

  it("nega bu savol muhimligini tushuntiradi", () => {
    chiqar(insufficient);
    expect(screen.getByTestId("why")).toHaveTextContent("boj stavkasi");
  });

  it("nomzod kodlarni ko'rsatadi, lekin EHTIMOL sifatida belgilaydi", () => {
    chiqar(insufficient);
    const blok = screen.getByTestId("candidates");
    expect(within(blok).getByText(/6106 10 000 0/)).toBeInTheDocument();
    expect(within(blok).getByText(/6206 30 000 0/)).toBeInTheDocument();
    // Blok sarlavhasi bu kodlar javob EMASLIGINI aytishi shart.
    expect(blok).toHaveTextContent(/mumkin|ehtimol|variant/i);
  });

  it("nomzod kodni javob kabi ko'rsatmaydi", () => {
    chiqar(insufficient);
    const blok = screen.getByTestId("candidates");
    expect(within(blok).queryByTestId("final-code")).toBeNull();
  });

  it("hech narsa aniqlanmaganda ham tushunarli javob beradi", () => {
    chiqar(empty);
    expect(screen.queryByTestId("final-code")).toBeNull();
    expect(screen.getByTestId("question")).toBeInTheDocument();
  });
});

// --- ⭐ Halollik: har doim ko'rinadigan ogohlantirishlar -------------------

describe("ogohlantirishlar", () => {
  it.each([
    ["aniqlangan", resolved],
    ["to'liqmas", insufficient],
    ["bo'sh", empty],
  ])("%s javobda disclaimer ko'rinadi", (_nom, javob) => {
    chiqar(javob as ClassifyResponse);
    expect(screen.getByTestId("disclaimer")).toHaveTextContent(
      "yuridik kuchga ega emas",
    );
  });

  it.each([
    ["aniqlangan", resolved],
    ["to'liqmas", insufficient],
    ["bo'sh", empty],
  ])("%s javobda tasdiqlanmagan ma'lumot ogohlantirishi ko'rinadi", (_nom, javob) => {
    chiqar(javob as ClassifyResponse);
    expect(screen.getByTestId("data-warning")).toBeInTheDocument();
  });

  it("tasdiqlanmagan iqtiboslarni belgilaydi", () => {
    chiqar(resolved);
    const bayroqlar = screen.getAllByTestId("unverified-badge");
    expect(bayroqlar.length).toBeGreaterThan(0);
  });

  it("model ishlamaganini yashirmaydi", () => {
    chiqar({ ...empty, model_ok: false });
    expect(screen.getByTestId("model-error")).toBeInTheDocument();
  });

  it("model joyida bo'lsa xato ko'rsatilmaydi", () => {
    chiqar(resolved);
    expect(screen.queryByTestId("model-error")).toBeNull();
  });
});

// --- Rad etilgan variantlar ------------------------------------------------

describe("rad etilgan variantlar", () => {
  it("boshida yopiq turadi", () => {
    chiqar(resolved);
    expect(screen.queryByTestId("rejection")).toBeNull();
  });

  it("bosilganda sabablari bilan ochiladi", async () => {
    chiqar(resolved);
    await userEvent.click(screen.getByTestId("rejections-toggle"));
    const radlar = screen.getAllByTestId("rejection");
    expect(radlar.length).toBeGreaterThan(0);
    expect(radlar[0]).toHaveTextContent(/talab qilinardi|kiritmada/);
  });
});

// --- Tizim kiritmani qanday tushundi ---------------------------------------

describe("ajratilgan ma'lumot", () => {
  it("tizim nimani tushunganini ko'rsatadi", () => {
    chiqar(resolved);
    const blok = screen.getByTestId("attributes");
    // Har bir ajratilgan atribut ro'yxatda bo'lishi kerak.
    for (const a of resolved.attributes) {
      expect(within(blok).getByText(a.name)).toBeInTheDocument();
    }
    expect(within(blok).getAllByText("trikotaj").length).toBeGreaterThan(0);
  });

  it("xulosa qilingan qiymatni aytilganidan ajratadi", () => {
    chiqar(resolved);
    const xulosa = screen.getAllByTestId("attr-inferred");
    expect(xulosa.length).toBeGreaterThan(0);
  });
});
