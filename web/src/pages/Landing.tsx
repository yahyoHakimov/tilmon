/**
 * Ochiq sahifa.
 *
 * Tartib ataylab shunday: cheklov va ma'lumot holati asosiy mazmundan
 * OLDIN keladi. Pastda, mayda shriftda turgan ogohlantirish — yashirilgan
 * ogohlantirish, va bu loyihaning 3-tamoyiliga zid.
 *
 * Foyda davlat tomonidan tushuntiriladi. "Tadbirkor jarima to'lamaydi"
 * degan gap to'g'ri, lekin u tizimni shaxsiy manfaat vositasi qilib
 * ko'rsatadi; asosiy qiymat esa deklaratsiyalar sifatida.
 */

const TAMOYILLAR = [
  {
    sarlavha: "Bu qidiruv emas, tasnif",
    matn: `Kalit so'z bo'yicha ro'yxat chiqarmaydi. Tavsifingizdan
      xususiyatlar ajratiladi, so'ng rasmiy tasnif qoidalari bo'ylab
      yurib bitta kod tanlanadi.`,
  },
  {
    sarlavha: "Asos haqiqiy",
    matn: `"Nega bu kod?" degan savolga javob rasmiy izohlar matnidan
      iqtibos bilan beriladi. Matn o'zgartirilmaydi va qisqartirilmaydi —
      uni o'qib, o'zingiz tekshira olasiz.`,
  },
  {
    sarlavha: "Bilmaganda jim turadi",
    matn: `Ma'lumot yetarli bo'lmasa, kod bermaydi. Nima yetishmayotganini
      aytadi va savol beradi. Har qanday kiritmaga ishonch bilan javob
      beradigan tizim xavfli.`,
  },
];

export function Landing({
  onLogin,
  onRegister,
}: {
  onLogin: () => void;
  onRegister: () => void;
}) {
  return (
    <div className="landing">
      <header className="l-header">
        <div className="l-brand">Tilmon</div>
        <nav className="l-nav">
          <button type="button" className="l-link" data-testid="cta-login" onClick={onLogin}>
            Kirish
          </button>
          <button type="button" className="l-btn" data-testid="cta-register" onClick={onRegister}>
            Ro'yxatdan o'tish
          </button>
        </nav>
      </header>

      <section className="l-hero">
        <h1>
          TN VED kodini <span className="l-accent">asosi bilan</span> aniqlang
        </h1>
        <p className="l-sub">
          Tovarni o'z so'zingiz bilan tavsiflang. Tizim rasmiy tasnif
          qoidalari asosida kodni aniqlaydi va har bir qadamning huquqiy
          asosini ko'rsatadi. Ma'lumot yetarli bo'lmasa —{" "}
          <b>kod bermaydi, savol beradi</b>.
        </p>
      </section>

      {/* Cheklovlar asosiy mazmundan OLDIN. Test buni tartib bo'yicha
          tekshiradi — pastga surib qo'yib bo'lmaydi. */}
      <section className="l-notices">
        <div className="notice notice-warn" data-testid="disclaimer">
          <b>Javob tavsiya xarakteriga ega va yuridik kuchga ega emas.</b>{" "}
          Yakuniy tasnif javobgarligi deklarantda qoladi. Shubhali holatlarda
          bojxona organidan dastlabki qaror oling.
        </div>

        <div className="notice notice-warn" data-testid="data-status">
          <b>Ma'lumot bazasi hali tasdiqlanmagan.</b> Kodlar, nomlar va
          huquqiy izohlar rasmiy nashrdan so'zma-so'z tasdiqlanmagan (sinov
          ma'lumotlari). Tizim har bir iqtibos yonida buni belgilab boradi.
        </div>

        <div className="notice notice-info" data-testid="beta-notice">
          <b>Yopiq beta.</b> Ro'yxatdan o'tish uchun <b>taklif kodi</b>{" "}
          kerak. Ma'lumot tasdiqlangunicha foydalanuvchilar doirasi
          cheklangan.
        </div>
      </section>

      {/* --- Muammo --- */}
      <section className="l-section">
        <h2>Muammo</h2>
        <p className="l-lead">
          Tadbirkor Xitoydan 500 dona ayollar bluzkasini olib kelmoqchi.
          Deklaratsiyada u tovarga kod yozishi shart — bu kod boj stavkasini
          belgilaydi. Bluzka uchun kamida ikkita mumkin bo'lgan kod bor.
        </p>

        <div className="l-example" data-testid="example">
          <div className="l-ex-row">
            <code className="l-code">6106</code>
            <div>
              <b>Trikotaj</b> — ip halqalaridan to'qilgan, tayyor mato emas
            </div>
          </div>
          <div className="l-ex-vs">yoki</div>
          <div className="l-ex-row">
            <code className="l-code">6206</code>
            <div>
              <b>To'qima</b> — tayyor matodan tikilgan
            </div>
          </div>
          <p className="l-ex-note">
            Ko'rinishidan bir xil kiyim. Lekin stavka boshqa, jarima ham
            boshqa. Farq matoning qanday ishlab chiqarilganida — buni
            tadbirkor bilmaydi, ba'zan yetkazib beruvchi ham aniq yozmaydi.
          </p>
        </div>

        <p className="l-lead">
          Natijada u brokerga pul to'laydi yoki taxmin qiladi. Taxmin
          noto'g'ri chiqsa — jarima, tovar ushlanib qolishi, qayta
          rasmiylashtirish.
        </p>
      </section>

      {/* --- Uchta tamoyil --- */}
      <section className="l-section">
        <h2>Qanday ishlaydi</h2>
        <div className="l-principles">
          {TAMOYILLAR.map((t, i) => (
            <div key={t.sarlavha} className="l-principle" data-testid="principle">
              <div className="l-pnum">{i + 1}</div>
              <h3>{t.sarlavha}</h3>
              <p>{t.matn}</p>
            </div>
          ))}
        </div>
      </section>

      {/* --- Davlat uchun foyda --- */}
      <section className="l-section l-state" data-testid="state-benefit">
        <h2>Nima uchun bu kerak</h2>
        <p className="l-lead">
          To'g'ri tasnif — bu birinchi navbatda <b>deklaratsiyalar sifati</b>{" "}
          masalasi. Noto'g'ri deklaratsiyalar kamayganda bojxona xodimi
          kamroq qaytarish qiladi, hujjatlar tezroq o'tadi, nizolar soni
          tushadi. Rasmiylashtirish xarajati ham, davlat tomonidagi nazorat
          yuki ham kamayadi.
        </p>
        <p className="l-lead">
          Importchi va broker uchun bevosita foyda — tekshiruv tezroq va
          arzonroq bo'ladi, taxminga asoslangan qarorlar o'rnini asosli
          qarorlar egallaydi.
        </p>
      </section>

      <section className="l-cta">
        <h2>Sinab ko'rish</h2>
        <p>Taklif kodingiz bo'lsa, ro'yxatdan o'ting.</p>
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
