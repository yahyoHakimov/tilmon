/**
 * Landing demosi uchun ssenariylar.
 *
 * Bu backendning kichraytirilgan nusxasi emas, uning SODIQ namunasi:
 * bir xil qadamlar, bir xil savollar, bir xil iqtiboslar. Matnlar
 * `backend/data/notes.yaml` dan ko'chirilgan va `status: unverified`
 * belgisi bilan birga ko'chirilgan.
 *
 * Demo backendga murojaat qilmaydi — tashrif buyuruvchi ro'yxatdan
 * o'tmagan, unga kirish yo'q. Lekin u ko'radigan xatti-harakat
 * haqiqiysi bilan bir xil bo'lishi shart, aks holda sahifa mahsulot
 * haqida yolg'on gapirgan bo'ladi.
 */

export interface Iqtibos {
  ref: string;
  matn: string;
  tasdiqlangan: boolean;
}

export interface Qadam {
  yorliq: string;
  qiymat: string;
}

export interface Variant {
  yorliq: string;
  qisqa: string;
  keyingi: string;
}

export type Tugun =
  | {
      tur: "savol";
      xususiyat: string;
      savol: string;
      nega: string;
      nomzodlar: { kod: string; izoh: string }[];
      variantlar: Variant[];
    }
  | {
      tur: "kod";
      kod: string;
      nom: string;
      boj: string;
      ishonch: "yuqori" | "o'rta";
      iqtiboslar: Iqtibos[];
      radEtilgan: { kod: string; sabab: string };
    };

export interface Senariy {
  id: string;
  kirish: string;
  tavsif: string;
  boshlanish: string;
  tugunlar: Record<string, Tugun>;
}

// notes.yaml dan ko'chirilgan — hammasi tasdiqlanmagan.
const N_TRIKOTAJ: Iqtibos = {
  ref: "60-bob (trikotaj matolar) — tasnif izohi",
  matn:
    "Trikotaj mato ipning bir yoki bir nechta halqalar tizimiga " +
    "birlashtirilishi natijasida hosil qilinadi. To'qima mato esa " +
    "bir-biriga perpendikulyar joylashgan ikki tizim — asos va arqoq " +
    "iplarining kesishuvidan hosil bo'ladi.",
  tasdiqlangan: false,
};

const N_6106: Iqtibos = {
  ref: "6106 pozitsiyasi sarlavhasi",
  matn:
    "Ayollar yoki qizlar bluzkalari, bluzalari va bluzka-ko'ylaklari, trikotaj.",
  tasdiqlangan: false,
};

const N_6206: Iqtibos = {
  ref: "6206 pozitsiyasi sarlavhasi",
  matn:
    "Ayollar yoki qizlar bluzkalari, bluzalari va bluzka-ko'ylaklari, " +
    "trikotajdan tashqari.",
  tasdiqlangan: false,
};

const N_TARKIB: Iqtibos = {
  ref: "XI bo'limga izoh, 2(A)-band",
  matn:
    "Ikki yoki undan ortiq to'qimachilik materialidan iborat buyumlar " +
    "massa bo'yicha ustun turadigan material bo'yicha tasniflanadi.",
  tasdiqlangan: false,
};

const N_8517: Iqtibos = {
  ref: "8517 13 subpozitsiyasi izohi",
  matn:
    "Smartfonlar — uyali aloqa tarmoqlari uchun mo'ljallangan, aloqa " +
    "vazifasidan tashqari ilovalarni bajaruvchi operatsion tizim bilan " +
    "jihozlangan telefonlar.",
  tasdiqlangan: false,
};

const SAVOL_TARKIB = {
  xususiyat: "Massa bo'yicha ustun material",
  savol:
    "Massa bo'yicha qaysi material ustun — paxta, kimyoviy tola, jun yoki ipak?",
  nega: "Yakuniy 10-xonali kodni belgilaydi.",
} as const;

export const SENARIYLAR: Senariy[] = [
  {
    id: "bluzka",
    kirish: "ayollar bluzkasi",
    tavsif: "Ma'lumot yetarli emas",
    boshlanish: "mato",
    tugunlar: {
      mato: {
        tur: "savol",
        xususiyat: "Matoning ishlab chiqarilish usuli",
        savol:
          "Mato trikotajmi yoki to'qimami? Trikotaj — ipning halqalaridan " +
          "hosil qilingan, cho'ziluvchan. To'qima — tayyor matodan tikilgan.",
        nega:
          "61-bob va 62-bob o'rtasidagi yagona farq. Ko'rinishidan bir xil " +
          "kiyim, lekin boj stavkasi va jarima boshqa.",
        nomzodlar: [
          { kod: "6106", izoh: "trikotaj bo'lsa" },
          { kod: "6206", izoh: "to'qima bo'lsa" },
        ],
        variantlar: [
          {
            yorliq: "Trikotaj — ip halqalaridan to'qilgan",
            qisqa: "trikotaj",
            keyingi: "tarkib_trikotaj",
          },
          {
            yorliq: "To'qima — tayyor matodan tikilgan",
            qisqa: "to'qima",
            keyingi: "tarkib_toqima",
          },
        ],
      },
      tarkib_trikotaj: {
        tur: "savol",
        ...SAVOL_TARKIB,
        nomzodlar: [
          { kod: "6106 10 000 0", izoh: "paxta" },
          { kod: "6106 20 000 0", izoh: "kimyoviy tola" },
        ],
        variantlar: [
          { yorliq: "Paxta", qisqa: "paxta", keyingi: "kod_6106_10" },
          {
            yorliq: "Kimyoviy tola (poliester, viskoza)",
            qisqa: "kimyoviy tola",
            keyingi: "kod_6106_20",
          },
        ],
      },
      tarkib_toqima: {
        tur: "savol",
        ...SAVOL_TARKIB,
        nomzodlar: [
          { kod: "6206 30 000 0", izoh: "paxta" },
          { kod: "6206 40 000 0", izoh: "kimyoviy tola" },
        ],
        variantlar: [
          { yorliq: "Paxta", qisqa: "paxta", keyingi: "kod_6206_30" },
          {
            yorliq: "Kimyoviy tola (poliester, viskoza)",
            qisqa: "kimyoviy tola",
            keyingi: "kod_6206_40",
          },
        ],
      },
      kod_6106_10: {
        tur: "kod",
        kod: "6106 10 000 0",
        nom: "Ayollar bluzkalari, paxtadan, trikotaj",
        boj: "10%",
        ishonch: "yuqori",
        iqtiboslar: [N_TRIKOTAJ, N_6106, N_TARKIB],
        radEtilgan: {
          kod: "6206",
          sabab: "«to'qima» talab qilinardi, siz «trikotaj» dedingiz",
        },
      },
      kod_6106_20: {
        tur: "kod",
        kod: "6106 20 000 0",
        nom: "Ayollar bluzkalari, kimyoviy tolalardan, trikotaj",
        boj: "10%",
        ishonch: "yuqori",
        iqtiboslar: [N_TRIKOTAJ, N_6106, N_TARKIB],
        radEtilgan: {
          kod: "6206",
          sabab: "«to'qima» talab qilinardi, siz «trikotaj» dedingiz",
        },
      },
      kod_6206_30: {
        tur: "kod",
        kod: "6206 30 000 0",
        nom: "Ayollar bluzkalari, paxtadan, to'qima",
        boj: "10%",
        ishonch: "yuqori",
        iqtiboslar: [N_TRIKOTAJ, N_6206, N_TARKIB],
        radEtilgan: {
          kod: "6106",
          sabab: "«trikotaj» talab qilinardi, siz «to'qima» dedingiz",
        },
      },
      kod_6206_40: {
        tur: "kod",
        kod: "6206 40 000 0",
        nom: "Ayollar bluzkalari, kimyoviy tolalardan, to'qima",
        boj: "10%",
        ishonch: "yuqori",
        iqtiboslar: [N_TRIKOTAJ, N_6206, N_TARKIB],
        radEtilgan: {
          kod: "6106",
          sabab: "«trikotaj» talab qilinardi, siz «to'qima» dedingiz",
        },
      },
    },
  },
  {
    id: "toliq",
    kirish: "ayollar bluzkasi, 100% paxta, trikotaj, uzun yeng",
    tavsif: "Ma'lumot yetarli",
    boshlanish: "kod",
    tugunlar: {
      kod: {
        tur: "kod",
        kod: "6106 10 000 0",
        nom: "Ayollar bluzkalari, paxtadan, trikotaj",
        boj: "10%",
        ishonch: "yuqori",
        iqtiboslar: [N_TRIKOTAJ, N_6106, N_TARKIB],
        radEtilgan: {
          kod: "6206",
          sabab: "«to'qima» talab qilinardi, matnda «trikotaj» yozilgan",
        },
      },
    },
  },
  {
    id: "smartfon",
    kirish: "Xitoydan 200 dona smartfon olib kelmoqchiman",
    tavsif: "Boshqa bo'lim",
    boshlanish: "kod",
    tugunlar: {
      kod: {
        tur: "kod",
        kod: "8517 13 000 0",
        nom: "Smartfonlar",
        boj: "0%",
        ishonch: "yuqori",
        iqtiboslar: [N_8517],
        radEtilgan: {
          kod: "8504 40 900 0",
          sabab: "zaryadlovchi alohida tasniflanadi, telefonning qismi emas",
        },
      },
    },
  },
];
