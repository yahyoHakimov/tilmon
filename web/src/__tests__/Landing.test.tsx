/**
 * 13-bosqich: Landing page.
 *
 * Bu sahifa marketing matni emas, ishonch hujjati. Uch narsa majburiy:
 *
 * 1. Cheklov BIRINCHI aytiladi. Foydalanuvchi javobning yuridik kuchga
 *    ega emasligini pastdagi mayda shrifтdan emas, yuqoridan bilishi kerak.
 * 2. Ma'lumot hali tasdiqlanmagani ochiq yoziladi.
 * 3. Foyda davlat tomonidan tushuntiriladi — "tadbirkor jarima to'lamaydi"
 *    emas, "noto'g'ri deklaratsiyalar kamayadi".
 *
 * Testlar shu uchtasini himoya qiladi: kimdir keyinchalik sahifani
 * "sotuvchiroq" qilmoqchi bo'lganda, ular yiqiladi.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Landing } from "../pages/Landing";

const chiqar = (props = {}) =>
  render(<Landing onLogin={() => {}} onRegister={() => {}} {...props} />);

// --- ⭐ Halollik majburiyatlari --------------------------------------------

describe("halollik", () => {
  it("javob yuridik kuchga ega emasligini aytadi", () => {
    chiqar();
    expect(screen.getByTestId("disclaimer")).toHaveTextContent(
      /yuridik kuchga ega emas/i,
    );
  });

  it("cheklov sahifaning yuqori qismida turadi", () => {
    /**
     * Pastda, mayda shrifтda turgan ogohlantirish — yashirilgan
     * ogohlantirish. U asosiy mazmundan OLDIN kelishi kerak.
     */
    chiqar();
    const disclaimer = screen.getByTestId("disclaimer");
    const misol = screen.getByTestId("example");
    expect(
      disclaimer.compareDocumentPosition(misol) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("ma'lumot hali tasdiqlanmaganini yashirmaydi", () => {
    chiqar();
    expect(screen.getByTestId("data-status")).toHaveTextContent(
      /tasdiqlanmagan/i,
    );
  });

  it("yopiq beta ekanini aytadi", () => {
    chiqar();
    expect(screen.getByTestId("beta-notice")).toBeInTheDocument();
  });
});

// --- Muammo va yechim ------------------------------------------------------

describe("mazmun", () => {
  it("aniq misolni ko'rsatadi: 6106 va 6206", () => {
    chiqar();
    const misol = screen.getByTestId("example");
    expect(misol).toHaveTextContent("6106");
    expect(misol).toHaveTextContent("6206");
  });

  it("farq matoning ishlab chiqarilishida ekanini tushuntiradi", () => {
    chiqar();
    expect(screen.getByTestId("example")).toHaveTextContent(/trikotaj/i);
    expect(screen.getByTestId("example")).toHaveTextContent(/to'qima/i);
  });

  it("davlat uchun foydani alohida ko'rsatadi", () => {
    chiqar();
    const foyda = screen.getByTestId("state-benefit");
    expect(foyda).toHaveTextContent(/deklaratsiya/i);
  });

  it("uchta tamoyilni sanaydi", () => {
    chiqar();
    expect(screen.getAllByTestId("principle")).toHaveLength(3);
  });

  it("jim turish tamoyilini ko'rsatadi", () => {
    chiqar();
    const tamoyillar = screen
      .getAllByTestId("principle")
      .map((el) => el.textContent ?? "");
    expect(tamoyillar.some((t) => /jim tur/i.test(t))).toBe(true);
  });
});

// --- Harakatlar ------------------------------------------------------------

describe("kirish va ro'yxat", () => {
  it("kirish tugmasi ishlaydi", async () => {
    const onLogin = vi.fn();
    chiqar({ onLogin });
    await userEvent.click(screen.getByTestId("cta-login"));
    expect(onLogin).toHaveBeenCalledOnce();
  });

  it("ro'yxatdan o'tish tugmasi ishlaydi", async () => {
    const onRegister = vi.fn();
    chiqar({ onRegister });
    await userEvent.click(screen.getByTestId("cta-register"));
    expect(onRegister).toHaveBeenCalledOnce();
  });

  it("ro'yxatdan o'tish taklif kodi talab qilishini aytadi", () => {
    chiqar();
    expect(screen.getByTestId("beta-notice")).toHaveTextContent(/taklif kodi/i);
  });
});
