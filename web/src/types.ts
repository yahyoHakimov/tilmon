/**
 * Backend javob shakli.
 *
 * Diqqat: `code` maydoni faqat `Resolved` da bor. Bu tasodifiy emas —
 * backend uni to'liqmas javobga ATAYLAB kiritmaydi (null ham emas).
 * TypeScript tomonida bu ajratilgan birlashma (discriminated union)
 * bo'lib, `status` tekshirilmasa `resp.code` ni o'qib bo'lmaydi.
 *
 * Ya'ni "kodni tasodifan ko'rsatib qo'yish" xatosi kompilyatsiya
 * bosqichida ushlanadi, ish vaqtida emas.
 */

export interface Citation {
  note_id: string;
  ref: string;
  text: string;
  status: "official" | "unverified";
}

export interface EvidenceStep {
  node: string;
  node_title_uz: string;
  attribute: string;
  attribute_label_uz: string;
  value: string;
  target: string;
  target_title_uz: string;
  why_uz: string;
  citations: Citation[];
}

export interface RejectionEvidence {
  code: string;
  title_uz: string;
  attribute: string;
  required_value: string;
  actual_value: string;
  citations: Citation[];
}

export interface Evidence {
  steps: EvidenceStep[];
  rejections: RejectionEvidence[];
  has_unverified: boolean;
  unverified_note_ids: string[];
}

export interface ExtractedAttribute {
  name: string;
  value: string;
  source: "stated" | "inferred" | "answered";
  evidence_uz: string;
}

export interface DroppedValue {
  name: string;
  value: string | null;
  reason: string;
}

export interface Candidate {
  branch_value: string;
  /** Odam o'qiydigan yorliq — UI tugmasida shu ko'rsatiladi. */
  label_uz: string;
  code: string;
  title_uz: string;
  is_final: boolean;
}

/** Matndan ajratilgan qiymat foydalanuvchi javobiga zid kelgan holat. */
export interface Conflict {
  attribute: string;
  extracted_value: string;
  answered_value: string;
}

interface Umumiy {
  attributes: ExtractedAttribute[];
  dropped: DroppedValue[];
  conflicts: Conflict[];
  model_ok: boolean;
  evidence: Evidence;
  disclaimer_uz: string;
  ontology_version: string;
  data_warning_uz?: string;
}

export interface ResolvedResponse extends Umumiy {
  status: "resolved";
  code: string;
  title_uz: string;
  duty_rate: number | null;
  confidence: {
    level: "yuqori" | "orta";
    inferred_attributes: string[];
  };
}

export interface InsufficientResponse extends Umumiy {
  status: "insufficient";
  stopped_at: string;
  stopped_at_title_uz: string;
  missing_attribute: string;
  missing_attribute_label_uz: string;
  reason: "korsatilmagan" | "notanish_qiymat";
  provided_value: string | null;
  question_uz: string;
  hint_uz: string;
  why_uz: string;
  candidates: Candidate[];
}

export type ClassifyResponse = ResolvedResponse | InsufficientResponse;
