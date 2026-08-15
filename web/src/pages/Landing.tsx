/**
 * Ochiq sahifa.
 *
 * Tuzilish qarori: sahifa mahsulotni TUSHUNTIRMAYDI, KO'RSATADI.
 * Markazda ishlaydigan demo turadi — tashrif buyuruvchi birinchi
 * ekranda tizimning eng g'ayrioddiy xususiyatini o'z ko'zi bilan
 * ko'radi: u javob bermay, savol beradi.
 *
 * Cheklov demodan OLDIN keladi. Pastda, mayda shriftda turgan
 * ogohlantirish — yashirilgan ogohlantirish, va bu loyihaning
 * 3-tamoyiliga zid. Test buni tartib bo'yicha qulflaydi.
 *
 * Foyda davlat tomonidan tushuntiriladi: "tadbirkor jarima
 * to'lamaydi" to'g'ri, lekin u tizimni shaxsiy manfaat vositasi
 * qilib ko'rsatadi; asosiy qiymat esa deklaratsiyalar sifatida.
 */

import { Demo } from "./Demo";

const TAMOYILLAR = [
  {
    belgi: "≠",
    sarlavha: "Bu qidiruv emas, tasnif",
    matn: `Kalit so'z bo'yicha ro'yxat chiqarmaydi. Tavsifingizdan
      xususiyatlar ajratiladi, so'ng rasmiy tasnif qoidalari bo'ylab
      yurib bitta kod tanlanadi.`,
  },
  {
    belgi: "§",
    sarlavha: "Asos haqiqiy",
    matn: `"Nega bu kod?" degan savolga javob rasmiy izohlar matnidan
      iqtibos bilan beriladi. Matn o'zgartirilmaydi va qisqartirilmaydi —
      uni o'qib, o'zingiz tekshira olasiz.`,
  },
  {
    belgi: "⏸",
    sarlavha: "Bilmaganda jim turadi",
    matn: `Ma'lumot yetarli bo'lmasa, kod bermaydi. Nima yetishmayotganini
      aytadi va savol beradi. Har qanday kiritmaga ishonch bilan javob
      beradigan tizim xavfli.`,
  },
];

export function Landing({
  onLogin,
  onRegister,
  registrationOpen = false,
}: {
  onLogin: () => void;
  onRegister: () => void;
  /** Ro'yxat ochiq bo'lsa, sahifa taklif kodi haqida gapirmasligi kerak —
   *  aks holda u foydalanuvchini ro'yxatdan o'tishdan qaytaradi. */
  registrationOpen?: boolean;
}) {
  return (
    <div className="landing">
      <header className="l-header">
        <div className="l-brand">Tilmon</div>
        <nav className="l-nav">
          <button
            type="button"
            className="l-link"
            data-testid="cta-login"
            onClick={onLogin}
          >
            Kirish
          </button>
          <button
            type="button"
            className="l-btn"
            data-testid="cta-register"
            onClick={onRegister}
          >
            Ro'yxatdan o'tish
          </button>
        </nav>
      </header>

      <section className="l-hero">
        <div className="l-pill">
          TN VED tasniflash · {registrationOpen ? "beta" : "yopiq beta"}
        </div>
        <h1>
          Kodni <span className="l-accent">asosi bilan</span> aniqlang
        </h1>
        <p className="l-sub">
          Tovarni o'z so'zingiz bilan tavsiflang. Tizim rasmiy tasnif
          qoidalari bo'ylab yurib kodni aniqlaydi va har bir qadamning
          huquqiy asosini ko'rsatadi. Ma'lumot yetarli bo'lmasa —{" "}
          <b>kod bermaydi, savol beradi.</b>
        </p>

        {/* Cheklov demodan OLDIN. Test tartibni qulflaydi. */}
        <div className="l-disclaimer" data-testid="disclaimer">
          <span className="l-warn-icon">!</span>
          <span>
            Javob <b>tavsiya xarakteriga ega va yuridik kuchga ega emas</b>.
            Yakuniy tasnif javobgarligi deklarantda qoladi. Shubhali
            holatlarda bojxona organidan dastlabki qaror oling.
          </span>
        </div>
      </section>

      {/* --- Interaktiv demo: sahifaning markazi --- */}
      <section className="l-demo-wrap" data-testid="example">
        <div className="l-demo-head">
          <h2>Sinab ko'ring</h2>
          <p>
            Tadbirkor Xitoydan 500 dona <b>ayollar bluzkasi</b> olib
            kelmoqchi. Bluzka uchun kamida ikkita kod bor:{" "}
            <code>6106</code> (trikotaj — ip halqalaridan to'qilgan) yoki{" "}
            <code>6206</code> (to'qima — tayyor matodan tikilgan).
            Ko'rinishidan bir xil kiyim, lekin stavka boshqa, jarima ham
            boshqa.
          </p>
        </div>

        <Demo />

        <p className="l-demo-note">
          Farq matoning qanday ishlab chiqarilganida — buni tadbirkor
          bilmaydi, ba'zan yetkazib beruvchi ham aniq yozmaydi. Natijada u
          brokerga pul to'laydi yoki taxmin qiladi.
        </p>
      </section>

      {/* --- Uchta tamoyil --- */}
      <section className="l-section">
        <h2 className="l-h2">Qanday ishlaydi</h2>
        <div className="l-principles">
          {TAMOYILLAR.map((t) => (
            <div key={t.sarlavha} className="l-principle" data-testid="principle">
              <div className="l-psym">{t.belgi}</div>
              <h3>{t.sarlavha}</h3>
              <p>{t.matn}</p>
            </div>
          ))}
        </div>
      </section>

      {/* --- Davlat uchun foyda --- */}
      <section className="l-state" data-testid="state-benefit">
        <h2 className="l-h2">Nima uchun bu kerak</h2>
        <p>
          To'g'ri tasnif — bu birinchi navbatda{" "}
          <b>deklaratsiyalar sifati</b> masalasi. Noto'g'ri deklaratsiyalar
          kamayganda bojxona xodimi kamroq qaytarish qiladi, hujjatlar
          tezroq o'tadi, nizolar soni tushadi. Rasmiylashtirish xarajati
          ham, davlat tomonidagi nazorat yuki ham kamayadi.
        </p>
        <p>
          Importchi va broker uchun bevosita foyda — tekshiruv tezroq va
          arzonroq bo'ladi, taxminga asoslangan qarorlar o'rnini asosli
          qarorlar egallaydi.
        </p>
      </section>

      {/* --- Halollik --- */}
      <section className="l-section">
        <h2 className="l-h2">Nimani bilishingiz kerak</h2>
        <div className="l-honest">
          <div className="l-honest-card" data-testid="data-status">
            <h3>Ma'lumot bazasi hali tasdiqlanmagan</h3>
            <p>
              Kodlar, nomlar va huquqiy izohlar rasmiy nashrdan so'zma-so'z{" "}
              <b>tasdiqlanmagan</b> (sinov ma'lumotlari). Tizim buni
              yashirmaydi — har bir iqtibos yonida belgi turadi va har bir
              javobda ogohlantirish chiqadi.
            </p>
          </div>
          <div className="l-honest-card" data-testid="beta-notice">
            <h3>{registrationOpen ? "Beta bosqichi" : "Yopiq beta"}</h3>
            {registrationOpen ? (
              <p>
                Tizim sinov bosqichida. Ro'yxatdan o'ting va o'z tovaringiz
                bilan sinab ko'ring — natijani rasmiy manba bilan
                solishtirishni unutmang.
              </p>
            ) : (
              <p>
                Ro'yxatdan o'tish uchun <b>taklif kodi</b> kerak. Ma'lumot
                tasdiqlangunicha foydalanuvchilar doirasi ataylab cheklangan.
              </p>
            )}
          </div>
        </div>
      </section>

      <section className="l-cta">
        <h2>{registrationOpen ? "Sinab ko'rasizmi?" : "Taklif kodingiz bormi?"}</h2>
        <p>Ro'yxatdan o'ting va o'z tovaringiz bilan sinab ko'ring.</p>
        <div className="l-cta-row">
          <button type="button" className="l-btn l-btn-lg" onClick={onRegister}>
            Ro'yxatdan o'tish
          </button>
          <button type="button" className="l-link" onClick={onLogin}>
            Akkauntim bor
          </button>
        </div>
      </section>

      <footer className="l-footer">
        Tilmon — TN VED tasniflash tizimi. Javoblar tavsiya xarakteriga ega.
      </footer>
    </div>
  );
}
