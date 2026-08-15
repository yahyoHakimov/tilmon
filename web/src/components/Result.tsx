/**
 * Tasnif natijasi.
 *
 * Eng muhim qaror shu faylda: `status === "resolved"` bo'lmasa,
 * yakuniy kod bloki UMUMAN render qilinmaydi. Nomzod kodlar
 * ko'rsatiladi, lekin alohida ko'rinishda va "mumkin bo'lgan
 * variantlar" sarlavhasi ostida — ular javob emas, xavf doirasi.
 *
 * TypeScript ajratilgan birlashmasi tufayli `data.code` ni
 * `status` tekshirmasdan o'qib bo'lmaydi: xato kompilyatsiyada
 * ushlanadi.
 */

import type {
  ClassifyResponse,
  InsufficientResponse,
  ResolvedResponse,
} from "../types";
import { EvidenceChain, Rejections } from "./Evidence";

function Warnings({ data }: { data: ClassifyResponse }) {
  return (
    <>
      {!data.model_ok && (
        <div className="notice notice-error" data-testid="model-error">
          <b>Til modeli javob bermadi.</b> Matn tahlil qilinmadi — quyidagi
          natija faqat aniqlangan ma'lumotga asoslangan. Qayta urinib ko'ring.
        </div>
      )}
      {data.data_warning_uz && (
        <div className="notice notice-warn" data-testid="data-warning">
          {data.data_warning_uz}
        </div>
      )}
    </>
  );
}

function Attributes({ data }: { data: ClassifyResponse }) {
  if (data.attributes.length === 0) return null;
  return (
    <section className="panel" data-testid="attributes">
      <h3>Tizim kiritmani qanday tushundi</h3>
      <ul className="attrs">
        {data.attributes.map((a) => (
          <li
            key={a.name}
            data-testid={a.source === "inferred" ? "attr-inferred" : "attr-stated"}
          >
            <span className="attr-name">{a.name}</span>
            <span className="attr-value">{a.value}</span>
            {a.source === "inferred" ? (
              <span className="badge badge-soft">
                xulosa{a.evidence_uz && `: «${a.evidence_uz}»`}
              </span>
            ) : (
              a.evidence_uz && <span className="attr-ev">«{a.evidence_uz}»</span>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

function ResolvedCard({ data }: { data: ResolvedResponse }) {
  return (
    <section className="card card-ok">
      <div className="code" data-testid="final-code">
        {data.code}
      </div>
      <div className="card-title" data-testid="final-title">
        {data.title_uz}
      </div>
      <div className="card-meta">
        <span data-testid="duty-rate">
          Boj stavkasi: <b>{data.duty_rate}%</b>
        </span>
        <span data-testid="confidence">
          Ishonch: <b>{data.confidence.level === "yuqori" ? "yuqori" : "o'rta"}</b>
          {data.confidence.inferred_attributes.length > 0 && (
            <> (xulosa: {data.confidence.inferred_attributes.join(", ")})</>
          )}
        </span>
      </div>
    </section>
  );
}

function Conflicts({ data }: { data: ClassifyResponse }) {
  if (data.conflicts.length === 0) return null;
  return (
    <div className="notice notice-warn" data-testid="conflict">
      {data.conflicts.map((z) => (
        <div key={z.attribute}>
          <b>{z.attribute}</b>: matndan «{z.extracted_value}» tushunilgan edi,
          siz «{z.answered_value}» deb javob berdingiz. Javobingiz olindi.
        </div>
      ))}
    </div>
  );
}

function InsufficientCard({
  data,
  onAnswer,
}: {
  data: InsufficientResponse;
  onAnswer?: (attribute: string, value: string) => void;
}) {
  return (
    <>
      <section className="card card-stop">
        <div className="stop-title">Aniq kod bera olmayman</div>
        <p className="stop-sub">
          {data.reason === "notanish_qiymat" ? (
            <>
              «{data.provided_value}» qiymati bu bosqichda mos kelmadi (
              {data.stopped_at_title_uz}).
            </>
          ) : (
            <>
              <b>{data.missing_attribute_label_uz}</b> ko'rsatilmagan.
            </>
          )}
        </p>

        <div className="question" data-testid="question">
          {data.question_uz}
        </div>
        {data.hint_uz && <div className="hint">{data.hint_uz}</div>}
        <div className="why" data-testid="why">
          <b>Nega muhim:</b> {data.why_uz}
        </div>

        {onAnswer && data.candidates.length > 0 && (
          <div className="answer-options">
            {data.candidates.map((c) => (
              <button
                key={c.branch_value}
                type="button"
                className="answer-option"
                data-testid="answer-option"
                onClick={() => onAnswer(data.missing_attribute, c.branch_value)}
              >
                {c.label_uz}
              </button>
            ))}
          </div>
        )}
      </section>

      {data.candidates.length > 0 && (
        <section className="panel candidates" data-testid="candidates">
          <h3>Mumkin bo'lgan variantlar</h3>
          <p className="candidates-note">
            Bular <b>javob emas</b>. Yuqoridagi savolga javob berilmaguncha
            qaysi biri to'g'ri ekani aniqlanmaydi.
          </p>
          <ul>
            {data.candidates.map((c) => (
              <li key={c.code}>
                <code>{c.code}</code>
                <span className="cand-branch">{c.branch_value}</span>
                <span className="cand-title">{c.title_uz}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}

export function Result({
  data,
  onAnswer,
}: {
  data: ClassifyResponse;
  /** Berilmasa javob tugmalari chiqmaydi (masalan, faqat ko'rish rejimi). */
  onAnswer?: (attribute: string, value: string) => void;
}) {
  return (
    <div className="result">
      <Warnings data={data} />
      <Conflicts data={data} />

      {data.status === "resolved" ? (
        <ResolvedCard data={data} />
      ) : (
        <InsufficientCard data={data} onAnswer={onAnswer} />
      )}

      <Attributes data={data} />
      <EvidenceChain evidence={data.evidence} />
      <Rejections evidence={data.evidence} />

      <footer className="disclaimer" data-testid="disclaimer">
        {data.disclaimer_uz}
        <div className="version">Ma'lumot bazasi: {data.ontology_version}</div>
      </footer>
    </div>
  );
}
