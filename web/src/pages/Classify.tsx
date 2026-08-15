import { useState } from "react";

import { classify } from "../api";
import { Result } from "../components/Result";
import type { ClassifyResponse } from "../types";

const MISOLLAR = [
  "ayollar bluzkasi, 100% paxta, trikotaj, uzun yeng",
  "ayollar bluzkasi",
  "erkaklar ko'ylagi, 100% paxta",
  "telefon uchun zaryadlovchi qurilma, 20W",
];

export function Classify() {
  const [matn, setMatn] = useState("");
  const [javoblar, setJavoblar] = useState<Record<string, string>>({});
  const [natija, setNatija] = useState<ClassifyResponse | null>(null);
  const [yuklanmoqda, setYuklanmoqda] = useState(false);
  const [xato, setXato] = useState<string | null>(null);

  /**
   * Server holat saqlamaydi: har safar matn + to'liq javoblar to'plami
   * yuboriladi. Shuning uchun natija har doim joriy kiritmadan to'liq
   * qayta hisoblanadi va "eskirgan javob" muammosi yuzaga kelmaydi.
   */
  async function yubor(qiymat: string, javoblarToplami: Record<string, string>) {
    if (!qiymat.trim()) return;
    setYuklanmoqda(true);
    setXato(null);
    try {
      setNatija(await classify(qiymat, javoblarToplami));
    } catch (e) {
      setXato(e instanceof Error ? e.message : "Noma'lum xato");
      setNatija(null);
    } finally {
      setYuklanmoqda(false);
    }
  }

  function matnOzgardi(yangi: string) {
    setMatn(yangi);
    // Javoblar avvalgi tovarga tegishli edi — yangi matn bilan ular
    // noto'g'ri bo'lib qolishi mumkin, shuning uchun bekor qilinadi.
    if (Object.keys(javoblar).length > 0) setJavoblar({});
  }

  function javobBerildi(xususiyat: string, qiymat: string) {
    const yangi = { ...javoblar, [xususiyat]: qiymat };
    setJavoblar(yangi);
    void yubor(matn, yangi);
  }

  function javoblarniTozala() {
    setJavoblar({});
    void yubor(matn, {});
  }

  return (
    <div className="app">
      <header className="header">
        <p className="lead">
          Tovarni tavsiflang — tizim TN VED kodini rasmiy tasnif qoidalari
          asosida aniqlaydi va har bir qadamning asosini ko'rsatadi.{" "}
          <b>Ma'lumot yetarli bo'lmasa, kod bermaydi</b> — nima yetishmayotganini
          so'raydi.
        </p>
      </header>

      <form
        className="form"
        data-testid="classify-form"
        onSubmit={(e) => {
          e.preventDefault();
          void yubor(matn, javoblar);
        }}
      >
        <textarea
          value={matn}
          onChange={(e) => matnOzgardi(e.target.value)}
          placeholder="Masalan: ayollar bluzkasi, 100% paxta, trikotaj, uzun yeng"
          rows={3}
          maxLength={2000}
        />
        <button type="submit" disabled={yuklanmoqda || !matn.trim()}>
          {yuklanmoqda ? "Tahlil qilinmoqda…" : "Kodni aniqlash"}
        </button>
      </form>

      <div className="examples">
        <span>Misollar:</span>
        {MISOLLAR.map((m) => (
          <button
            key={m}
            type="button"
            className="example"
            onClick={() => {
              setMatn(m);
              setJavoblar({});
              void yubor(m, {});
            }}
          >
            {m}
          </button>
        ))}
      </div>

      {Object.keys(javoblar).length > 0 && (
        <div className="given-answers" data-testid="given-answers">
          <span className="given-label">Siz javob berdingiz:</span>
          {Object.entries(javoblar).map(([k, v]) => (
            <span key={k} className="given-chip">
              {k}: <b>{v}</b>
            </span>
          ))}
          <button
            type="button"
            className="clear-answers"
            data-testid="clear-answers"
            onClick={javoblarniTozala}
          >
            tozalash
          </button>
        </div>
      )}

      {xato && <div className="notice notice-error">{xato}</div>}
      {natija && <Result data={natija} onAnswer={javobBerildi} />}
    </div>
  );
}
