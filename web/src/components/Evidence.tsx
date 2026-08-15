/**
 * Asos zanjiri va rad etilgan variantlar.
 *
 * Iqtibos matni bu yerda HECH QANDAY o'zgartirilmaydi — qisqartirilmaydi,
 * qayta yozilmaydi. Backend'dagi bir xil qoida frontendda ham amal qiladi:
 * foydalanuvchi rasmiy matnni ko'rib, o'zi tekshira olishi kerak.
 */

import { useState } from "react";
import type { Citation, Evidence as EvidenceData } from "../types";

function CitationBlock({ c }: { c: Citation }) {
  return (
    <li className="citation">
      <div className="citation-head">
        <span className="citation-ref">{c.ref}</span>
        {c.status === "unverified" && (
          <span className="badge badge-warn" data-testid="unverified-badge">
            tasdiqlanmagan
          </span>
        )}
      </div>
      <blockquote className="citation-text">{c.text}</blockquote>
    </li>
  );
}

export function EvidenceChain({ evidence }: { evidence: EvidenceData }) {
  if (evidence.steps.length === 0) return null;

  return (
    <section className="panel">
      <h3>Asos</h3>
      <ol className="steps">
        {evidence.steps.map((q, i) => (
          <li key={`${q.node}-${q.attribute}`} data-testid="evidence-step">
            <div className="step-head">
              <span className="step-num">{i + 1}</span>
              <div>
                <div className="step-title">
                  {q.attribute_label_uz}: <b>{q.value}</b>
                </div>
                <div className="step-target">
                  → {q.target} · {q.target_title_uz}
                </div>
              </div>
            </div>
            <ul className="citations">
              {q.citations.map((c) => (
                <CitationBlock key={c.note_id} c={c} />
              ))}
            </ul>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function Rejections({ evidence }: { evidence: EvidenceData }) {
  const [ochiq, setOchiq] = useState(false);
  if (evidence.rejections.length === 0) return null;

  return (
    <section className="panel">
      <button
        className="toggle"
        data-testid="rejections-toggle"
        onClick={() => setOchiq((v) => !v)}
        aria-expanded={ochiq}
      >
        {ochiq ? "▾" : "▸"} Ko'rib chiqildi, rad etildi (
        {evidence.rejections.length})
      </button>

      {ochiq && (
        <ul className="rejections">
          {evidence.rejections.map((r) => (
            <li key={`${r.code}-${r.attribute}`} data-testid="rejection">
              <div className="rejection-head">
                <code>{r.code}</code> — {r.title_uz}
              </div>
              <div className="rejection-why">
                «{r.required_value}» talab qilinardi, kiritmada «{r.actual_value}»
              </div>
              <ul className="citations">
                {r.citations.slice(0, 2).map((c) => (
                  <CitationBlock key={c.note_id} c={c} />
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
