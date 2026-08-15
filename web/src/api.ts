import type { ClassifyResponse } from "./types";

export async function classify(
  text: string,
  answers: Record<string, string> = {},
): Promise<ClassifyResponse> {
  const r = await fetch("/api/classify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, answers }),
  });

  if (r.status === 422) {
    throw new Error(
      "So'rov qabul qilinmadi: matn bo'sh, juda uzun (2000 belgigacha) " +
        "yoki javob qiymati noto'g'ri.",
    );
  }
  if (!r.ok) {
    throw new Error(`Server xatosi (${r.status}). Qayta urinib ko'ring.`);
  }
  return r.json();
}
