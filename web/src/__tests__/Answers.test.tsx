/**
 * 8-bosqich: Savol-javob sikli (UI).
 *
 * Tizim savol berishi yetarli emas — foydalanuvchi javob berib davom
 * eta olishi kerak. Aks holda "nima yetishmayapti" degan javob boshi
 * berk ko'chaga aylanadi va foydalanuvchi baribir taxmin qiladi.
 *
 * Tugmalarda `koylak_bluzka` emas, odam o'qiydigan yorliq bo'lishi shart:
 * bojxona atamalari bilan ishlaydigan odam ham dastur slug'ini o'qishi
 * shart emas.
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Classify } from "../pages/Classify";
import { Result } from "../components/Result";
import fixtures from "./fixtures.json";
import type { InsufficientResponse, ResolvedResponse } from "../types";

const resolved = fixtures.resolved as unknown as ResolvedResponse;
const insufficient = fixtures.insufficient as unknown as InsufficientResponse;

// --- Javob variantlari -----------------------------------------------------

describe("javob variantlari", () => {
  it("to'liqmas javobda variant tugmalari ko'rinadi", () => {
    render(<Result data={insufficient} onAnswer={() => {}} />);
    const tugmalar = screen.getAllByTestId("answer-option");
    expect(tugmalar).toHaveLength(insufficient.candidates.length);
  });

  it("tugmada o'zbekcha yorliq ko'rinadi, slug emas", () => {
    render(<Result data={insufficient} onAnswer={() => {}} />);
    const tugmalar = screen.getAllByTestId("answer-option");
    for (const c of insufficient.candidates) {
      expect(tugmalar.some((t) => t.textContent?.includes(c.label_uz))).toBe(true);
    }
    // Slug hech qaysi tugmada ko'rinmasligi kerak.
    for (const t of tugmalar) {
      expect(t.textContent).not.toContain("koylak_bluzka");
    }
  });

  it("tugma bosilganda yetishmayotgan xususiyat va qiymat uzatiladi", async () => {
    const onAnswer = vi.fn();
    render(<Result data={insufficient} onAnswer={onAnswer} />);
    await userEvent.click(screen.getAllByTestId("answer-option")[0]);
    expect(onAnswer).toHaveBeenCalledWith(
      insufficient.missing_attribute,
      insufficient.candidates[0].branch_value,
    );
  });

  it("aniqlangan javobda variant tugmalari yo'q", () => {
    render(<Result data={resolved} onAnswer={() => {}} />);
    expect(screen.queryByTestId("answer-option")).toBeNull();
  });

  it("onAnswer berilmasa tugmalar chiqmaydi", () => {
    render(<Result data={insufficient} />);
    expect(screen.queryByTestId("answer-option")).toBeNull();
  });
});

// --- Ziddiyat --------------------------------------------------------------

describe("ziddiyat", () => {
  it("foydalanuvchi o'z matnini bekor qilganini ko'rsatadi", () => {
    render(
      <Result
        data={{
          ...resolved,
          conflicts: [
            {
              attribute: "mato_turi",
              extracted_value: "trikotaj",
              answered_value: "toqima",
            },
          ],
        }}
      />,
    );
    const z = screen.getByTestId("conflict");
    expect(z).toHaveTextContent("trikotaj");
    expect(z).toHaveTextContent("toqima");
  });

  it("ziddiyat bo'lmasa hech narsa ko'rsatilmaydi", () => {
    render(<Result data={resolved} />);
    expect(screen.queryByTestId("conflict")).toBeNull();
  });
});

// --- ⭐ To'liq sikl (App darajasida) ---------------------------------------

describe("to'liq sikl", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("javob berilgach so'rov javoblar bilan qayta yuboriladi", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => insufficient })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => resolved });
    vi.stubGlobal("fetch", fetchMock);

    render(<Classify />);
    await userEvent.type(
      screen.getByRole("textbox"),
      "ayollar bluzkasi, 100% paxta",
    );
    await userEvent.click(screen.getByRole("button", { name: /Kodni aniqlash/ }));

    // 1-javob: savol
    await waitFor(() => expect(screen.getAllByTestId("answer-option").length).toBe(2));
    expect(screen.queryByTestId("final-code")).toBeNull();

    // Variantni tanlaymiz
    await userEvent.click(screen.getAllByTestId("answer-option")[0]);

    // 2-javob: kod
    await waitFor(() => expect(screen.getByTestId("final-code")).toBeInTheDocument());

    // Ikkinchi so'rovda javob yuborilgani tekshiriladi
    const ikkinchi = JSON.parse(fetchMock.mock.calls[1][1].body);
    expect(ikkinchi.answers).toEqual({
      [insufficient.missing_attribute]: insufficient.candidates[0].branch_value,
    });
    expect(ikkinchi.text).toBe("ayollar bluzkasi, 100% paxta");
  });

  it("⭐ matn o'zgartirilsa avvalgi javoblar bekor qilinadi", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, status: 200, json: async () => insufficient });
    vi.stubGlobal("fetch", fetchMock);

    render(<Classify />);
    const maydon = screen.getByRole("textbox");
    await userEvent.type(maydon, "ayollar bluzkasi");
    await userEvent.click(screen.getByRole("button", { name: /Kodni aniqlash/ }));
    await waitFor(() => expect(screen.getAllByTestId("answer-option").length).toBe(2));
    await userEvent.click(screen.getAllByTestId("answer-option")[0]);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));

    // Yangi tovar — eski javoblar unga tegishli emas.
    await userEvent.clear(maydon);
    await userEvent.type(maydon, "erkaklar shimi");
    await userEvent.click(screen.getByRole("button", { name: /Kodni aniqlash/ }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    const uchinchi = JSON.parse(fetchMock.mock.calls[2][1].body);
    expect(uchinchi.answers).toEqual({});
  });

  it("berilgan javoblar ro'yxati ko'rinadi va tozalash mumkin", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, status: 200, json: async () => insufficient });
    vi.stubGlobal("fetch", fetchMock);

    render(<Classify />);
    await userEvent.type(screen.getByRole("textbox"), "ayollar bluzkasi");
    await userEvent.click(screen.getByRole("button", { name: /Kodni aniqlash/ }));
    await waitFor(() => expect(screen.getAllByTestId("answer-option").length).toBe(2));
    await userEvent.click(screen.getAllByTestId("answer-option")[0]);

    const panel = await screen.findByTestId("given-answers");
    expect(within(panel).getByText(/mato_turi/)).toBeInTheDocument();

    await userEvent.click(within(panel).getByTestId("clear-answers"));
    await waitFor(() => {
      const oxirgi = JSON.parse(
        fetchMock.mock.calls[fetchMock.mock.calls.length - 1][1].body,
      );
      expect(oxirgi.answers).toEqual({});
    });
  });
});
