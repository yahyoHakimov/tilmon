/**
 * Landing sahifasidagi interaktiv demo.
 *
 * Mahsulotni tushuntirish o'rniga ko'rsatadi. Tashrif buyuruvchi
 * ro'yxatdan o'tmasdan turib eng muhim xususiyatni o'z ko'zi bilan
 * ko'radi: ma'lumot yetarli bo'lmaganda kod berilmaydi, savol beriladi.
 *
 * Backendga murojaat yo'q — tashrif buyuruvchida kirish huquqi ham
 * yo'q. Lekin xatti-harakat haqiqiysi bilan bir xil: bir xil savollar,
 * bir xil iqtiboslar, bir xil `tasdiqlanmagan` bayrog'i.
 */

import { useMemo, useState } from "react";

import { SENARIYLAR, type Qadam, type Tugun } from "./demoData";

function Iqtiboslar({ tugun }: { tugun: Extract<Tugun, { tur: "kod" }> }) {
  return (
    <div className="d-asos">
      <div className="d-asos-h">Asos</div>
      {tugun.iqtiboslar.map((c) => (
        <div key={c.ref} className="d-citation" data-testid="demo-citation">
          <div className="d-citation-head">
            <span className="d-citation-ref">{c.ref}</span>
            {!c.tasdiqlangan && (
              <span className="badge badge-warn" data-testid="demo-unverified">
                tasdiqlanmagan
              </span>
            )}
          </div>
          <blockquote>{c.matn}</blockquote>
        </div>
      ))}
    </div>
  );
}

export function Demo() {
  const [senariyId, setSenariyId] = useState(SENARIYLAR[0].id);
  const [tugunId, setTugunId] = useState(SENARIYLAR[0].boshlanish);
  const [javoblar, setJavoblar] = useState<Qadam[]>([]);

  const senariy = useMemo(
    () => SENARIYLAR.find((s) => s.id === senariyId)!,
    [senariyId],
  );
  const tugun = senariy.tugunlar[tugunId];

  function senariyTanla(id: string) {
    const s = SENARIYLAR.find((x) => x.id === id)!;
    setSenariyId(id);
    setTugunId(s.boshlanish);
    setJavoblar([]);
  }

  function javobBer(yorliq: string, qisqa: string, keyingi: string) {
    setJavoblar((j) => [...j, { yorliq, qiymat: qisqa }]);
    setTugunId(keyingi);
  }

  function qaytaBoshla() {
    setTugunId(senariy.boshlanish);
    setJavoblar([]);
  }

  return (
    <div className="demo" data-testid="demo">
      <div className="d-presets">
        {SENARIYLAR.map((s) => (
          <button
            key={s.id}
            type="button"
            data-testid="demo-preset"
            className={`d-preset ${s.id === senariyId ? "d-preset-on" : ""}`}
            onClick={() => senariyTanla(s.id)}
          >
            {s.tavsif}
          </button>
        ))}
      </div>

      <div className="d-panel">
        <div className="d-input" data-testid="demo-input">
          <span className="d-input-label">Siz yozdingiz</span>
          <span className="d-input-text">{senariy.kirish}</span>
        </div>

        {javoblar.length > 0 && (
          <div className="d-answers">
            {javoblar.map((j) => (
              <span key={j.yorliq} className="d-chip" data-testid="demo-answered">
                {j.qiymat}
              </span>
            ))}
          </div>
        )}

        {tugun.tur === "savol" ? (
          <div className="d-stop" key={tugunId}>
            <div className="d-stop-title">
              <span className="d-dot" /> Aniq kod bera olmayman
            </div>

            <div className="d-cands">
              {tugun.nomzodlar.map((n) => (
                <span key={n.kod} className="d-cand">
                  <code>{n.kod}</code>
                  <em>{n.izoh}</em>
                </span>
              ))}
            </div>

            <div className="d-q" data-testid="demo-question">
              <span className="d-q-label">{tugun.xususiyat}</span>
              {tugun.savol}
            </div>
            <p className="d-why">
              <b>Nega muhim:</b> {tugun.nega}
            </p>

            <div className="d-options">
              {tugun.variantlar.map((v) => (
                <button
                  key={v.qisqa}
                  type="button"
                  className="d-option"
                  data-testid="demo-option"
                  onClick={() => javobBer(v.yorliq, v.qisqa, v.keyingi)}
                >
                  {v.yorliq}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="d-ok" key={tugunId}>
            <div className="d-code" data-testid="demo-code">
              {tugun.kod}
            </div>
            <div className="d-name">{tugun.nom}</div>
            <div className="d-meta">
              <span>
                Boj stavkasi <b>{tugun.boj}</b>
              </span>
              <span>
                Ishonch <b>{tugun.ishonch}</b>
              </span>
            </div>

            <Iqtiboslar tugun={tugun} />

            <div className="d-rejected">
              <b>Ko'rib chiqildi, rad etildi:</b>{" "}
              <code>{tugun.radEtilgan.kod}</code> — {tugun.radEtilgan.sabab}
            </div>
          </div>
        )}

        {(javoblar.length > 0 || tugun.tur === "kod") && (
          <button
            type="button"
            className="d-reset"
            data-testid="demo-reset"
            onClick={qaytaBoshla}
          >
            ↺ Qaytadan
          </button>
        )}
      </div>
    </div>
  );
}
