# Tilmon

TN VED tovar kodini **rasmiy tasnif qoidalari asosida** aniqlaydigan tizim.
Ma'lumot yetarli bo'lmasa — kod bermaydi.

```
Kiritma:  "ayollar bluzkasi, 100% paxta, trikotaj, uzun yeng"
Javob:    6106 10 000 0   (ishonch: yuqori)
          + har bir qadamning huquqiy asosi, rasmiy matndan iqtibos bilan
          + rad etilgan variantlar va rad etish sabablari

Kiritma:  "ayollar bluzkasi"
Javob:    Aniq kod bera olmayman.
          6106 (trikotaj) yoki 6206 (to'qima) bo'lishi mumkin.
          Matoning turi ko'rsatilmagan.
```

## Nima uchun

Bluzka uchun kamida ikkita mumkin bo'lgan kod bor: **6106** (trikotaj) va
**6206** (to'qima). Ko'rinishidan bir xil kiyim, lekin boj stavkasi boshqa,
jarima ham boshqa. Farq matoning ishlab chiqarilish usulida — buni tadbirkor
bilmaydi, ba'zan yetkazib beruvchi ham aniq yozmaydi.

Natijada u brokerga pul to'laydi yoki taxmin qiladi. Taxmin noto'g'ri chiqsa —
jarima, tovar ushlanib qolishi, qayta rasmiylashtirish.

**Davlat uchun foydasi:** noto'g'ri deklaratsiyalar kamayadi, bojxona xodimi
kamroq qaytarish qiladi, nizolar soni tushadi.

> **Cheklov:** tizimning javobi yuridik kuchga ega emas, u tavsiya.

## Uchta tamoyil

**1. Bu qidiruv emas, tasnif.**
Kalit so'z bo'yicha ro'yxat chiqarmaydi. Foydalanuvchi matnidan xususiyatlar
ajratiladi, so'ng qaror daraxti bo'ylab yurib **bitta** kod tanlanadi.

**2. Asos haqiqiy.**
"Nega bu kod?" savoliga javob `data/notes.yaml` dagi matndan `id` bo'yicha
olinadi va **o'zgartirilmaydi**. Model asos matnini yozmaydi. Buni test
kafolatlaydi: javobdagi har bir iqtibos bazadagi matn bilan aynan teng
bo'lishi shart.

**3. Bilmaganda jim turadi.**
Farqlovchi savolning javobi noma'lum bo'lsa, dvigatel to'xtaydi va kod
bermaydi. Bu 100+ test bilan himoyalangan, jumladan har bir yakuniy kod
uchun alohida: unga olib borgan har bir atributni birma-bir olib
tashlaganda tizim jim turishi shart.

Lekin jim turish boshi berk ko'cha emas — tizim savol beradi va
foydalanuvchi javob berib davom etadi:

```
"ayollar bluzkasi"
  → Mato trikotajmi yoki to'qimami?     [trikotaj] [to'qima]
  → trikotaj                             6106 yoki 6206
  → Massa bo'yicha ustun material?      [paxta] [kimyoviy tola] [jun] [ipak]
  → paxta
  → 6106 10 000 0                        ishonch: o'rta
     (mahsulot toifasi matndan xulosa qilingan)
```

Javob ham yopiq ro'yxatdan bo'lishi shart. Farqi shundaki, noto'g'ri
javob jimgina tashlanmaydi — **422** qaytariladi: model javobi ishonchsiz
kanal, foydalanuvchi javobi esa bizning UI'mizdan keladi.

Server holat saqlamaydi: har so'rovda matn + to'liq javoblar to'plami
yuboriladi. Matn o'zgartirilsa javoblar bekor qilinadi — ular avvalgi
tovarga tegishli edi.

## Arxitektura

```
   foydalanuvchi matni
          │
          ▼
   ┌──────────────┐   model FAQAT shu yerda ishtirok etadi
   │  extractor   │   erkin matn -> yopiq qiymatlar to'plami
   └──────┬───────┘   modelga ishonilmaydi: hamma narsa filtrlanadi
          │  {"mato_turi": "trikotaj", "jins": "ayol", ...}
          ▼
   ┌──────────────┐   sof Python, modelsiz, deterministik
   │   engine     │   daraxt bo'ylab yurish; atribut yo'q -> TO'XTASH
   └──────┬───────┘
          │  Resolved | Insufficient
          ▼
   ┌──────────────┐   iqtiboslar bazadan id bo'yicha olinadi
   │   evidence   │   matn shakllantirilmaydi, qisqartirilmaydi
   └──────────────┘
```

Model kod ayta olmaydi — u ko'rilmaydi ham. Kod faqat ontologiya bo'ylab
yurish natijasida hosil bo'ladi. Shuning uchun modelning har qanday
nosozligi (buzuq JSON, timeout, o'ylab topilgan qiymat) bir xil natija
beradi: **kamroq atribut, demak jim turish** — noto'g'ri kod emas.

## ⚠️ Ma'lumot holati

Hozircha `data/` dagi **barcha** kodlar, nomlar, boj stavkalari va huquqiy
izohlar `status: unverified` — ular rasmiy manbadan (lex.uz, customs.uz,
TN VED rasmiy nashri) so'zma-so'z tasdiqlanmagan. Matnlar mazmunan
Garmonizatsiyalashgan Tizim izohlariga asoslangan, lekin aynan rasmiy
tahrir emas.

Tizim buni yashirmaydi: har bir iqtibos yonida `tasdiqlanmagan` bayrog'i
turadi va har bir javobda ogohlantirish chiqadi.

**Rasmiy ma'lumot olinganda kod o'zgarmaydi** — faqat YAML fayllar
almashadi va `status: official` qo'yiladi.

Manba inventarizatsiyasi, tasdiqlash tartibi va aniqlangan
nomuvofiqliklar: **[`data/VERIFICATION.md`](backend/data/VERIFICATION.md)**

Qisqacha: birlamchi manba — [lex.uz ПП-181 (14.05.2025)](https://lex.uz/ru/docs/7533469),
2025-yil 1-iyundan kuchga kirgan. Unda **kodlar bor, izohlar yo'q** —
izohlar uchun alohida manba kerak. Manba tekshiruvi seed matnlarida
ikkita mazmuniy xato topdi (61 va 62-boblarga 1-izohlar); ular
tuzatildi, lekin `unverified` bo'lib qolmoqda.

Qamrov: 61/62-boblar (trikotaj/to'qima kiyim) va 8471/8504/8517/8544
(kompyuter, quvvat manbai, telefon, kabel) — 34 ta yakuniy kod.

## Kirish va huquqlar

Tilmon **yopiq beta**: ro'yxatdan o'tish uchun taklif kodi kerak. Sabab
loyihaga xos — ma'lumot bazasi hali tasdiqlanmagan, shuning uchun
birinchi foydalanuvchilar doirasi nazorat ostida bo'lishi kerak.

| Rol | Nima qila oladi |
|---|---|
| `user` | Tasnif qiladi, savollarga javob beradi |
| `admin` | + foydalanuvchilarni ko'radi/bloklaydi, taklif kodlari yaratadi |

**Birinchi adminni yaratish** (endpoint orqali emas — "tovuq va tuxum"):

```bash
cd backend
uv run python scripts/admin.py create-admin sizning@email.uz
uv run python scripts/admin.py invite --note "Aziz aka" --count 5
uv run python scripts/admin.py users
```

Parol terminalga yozilmaydi — yashirin so'raladi va buyruqlar tarixiga
tushmaydi.

### Xavfsizlik qarorlari

| Qaror | Sabab |
|---|---|
| Parol — **argon2id** | PHC g'olibi; xotira talab qiladi, GPU bilan sindirish qimmat |
| Sessiya — **bazada**, JWT emas | JWT ni bekor qilib bo'lmaydi; admin bloklaganda token 2 hafta ishlashda davom etardi |
| Bazada token emas, **SHA-256 xeshi** | Baza o'g'irlansa, yozuvlar bilan hech kimning nomidan kirib bo'lmaydi |
| Cookie — `HttpOnly`, `Secure`, `SameSite=Lax` | XSS da o'g'irlanmaydi, CSRF ning asosiy vektori yopiq |
| Kirish xatolari **bir xil** | "Email yo'q" va "parol xato" farqi qaysi emaillar ro'yxatdan o'tganini oshkor qiladi |
| Topilmagan foydalanuvchi uchun ham **parol tekshiriladi** | Aks holda javob vaqti o'sha ma'lumotni oshkor qiladi |
| Bloklash **sessiyalarni ham bekor qiladi** | Aks holda blok 2 haftadan keyin kuchga kirardi |

Har biri test bilan qulflangan va mutatsiya sinovidan o'tgan.

## Ishga tushirish

```bash
./dev.sh
```

Ikkalasini birga ko'taradi, Postgres konteynerini ko'taradi,
migratsiyalarni qo'llaydi, bog'liqliklarni tekshiradi va Ctrl+C da
ikkala jarayon daraxtini ham to'liq to'xtatadi.

```
Ilova      http://localhost:5173
API        http://127.0.0.1:8000/api/healthz
Hujjatlar  http://127.0.0.1:8000/docs
```

Portni o'zgartirish: `BACKEND_PORT=9000 ./dev.sh` (Vite proksisi avtomatik
moslashadi).

`OPENAI_API_KEY` bo'lmasa skript ogohlantiradi, lekin ishlashda davom
etadi: erkin matn tahlil qilinmaydi, ammo javob tugmalari orqali qo'lda
tasnif qilish to'liq ishlaydi.

### Qo'lda ishga tushirish

#### Backend

```bash
cd backend
cp .env.example .env          # OPENAI_API_KEY ni qo'ying
uv sync
uv run uvicorn app.api:app --reload
```

#### Frontend

```bash
cd web
npm install
npm run dev
```

`/api` so'rovlari backendga proksilanadi.

## Testlar

```bash
cd backend
uv run pytest                 # 387 test (Postgres bilan), ~10 soniya
uv run pytest -m live         # 60 test, OPENAI_API_KEY talab qiladi

cd ../web
npm test                      # 61 test
```

Postgres bo'lmasa auth testlari o'tkazib yuboriladi va **273 ta yadro
testi baribir ishlaydi** — tasnif mantiqi infratuzilmaga bog'liq emas.

### Test taqsimoti

| Qatlam | Testlar | Nimani kafolatlaydi |
|---|---:|---|
| Ontologiya | 28 | Ma'lumot yaxlitligi, o'lik kod yo'qligi, asossiz farqlovchi yo'qligi |
| Dvigatel | 58 | To'liqmas kirishda kod berilmasligi (34 kod uchun alohida) |
| Asos zanjiri | 16 | Iqtiboslar bazadagi matn bilan **aynan** teng |
| Ekstraktor | 31 | Model buzilganda ham kod berilmasligi |
| Ishonch | 6 | Xulosa qilingan atribut yashirilmasligi |
| Savol-javob | 22 | Noto'g'ri javob 422; ziddiyat yashirilmasligi |
| API | 27 | To'liqmas javobda `code` maydonining **umuman yo'qligi** |
| Oltin to'plam | 62 | 54 misol: 32 kod + 22 jim turish |
| Xavfsizlik | 18 | Parol xeshdan tiklanmasligi, parol siyosati |
| Modellar | 19 | Ochiq parol/token ustuni yo'qligi |
| Sessiyalar | 15 | Bazada token emas, xesh saqlanishi |
| Kirish API | 31 | Xato javoblari ma'lumot oshkor qilmasligi |
| Ro'yxat | 28 | Taklif kodi bir marta ishlashi |
| Huquqlar | 24 | Himoyalanmagan endpoint qolmasligi |
| Deploy tekshiruvi | 16 | Xavfsiz bo'lmagan sozlama bilan ishga tushmaslik |
| **Backend jami** | **403** | (+60 `live`) |
| Web UI | 74 | Kod javob sifatida ko'rsatilmasligi; demo ham jim turishi |

### Mutatsiya sinovi

Testlarning o'zi ham sinaladi: kod ataylab buziladi va testlar ushlaydimi
tekshiriladi. Ishlab chiqish davomida bu usul **uchta haqiqiy tuynuk** topdi
(yo'qolgan asos matni jimgina o'tib ketishi; `attributes` ichiga yashiringan
kod; API kalitsiz muhitda 500 xatosi).

Dvigatelga "noma'lum bo'lsa eng ehtimolli tarmoqni tanla" mutatsiyasi
qo'yilganda **88 test yiqiladi**, jumladan barcha 22 ta jim turish misoli.

## Loyiha tuzilishi

```
dev.sh             Ikkalasini birga ishga tushiradi
backend/
  app/
    ontology.py      YAML -> tuzilma. Mantiq yo'q.
    engine.py        Tasnif dvigateli. Modelsiz, deterministik.
    evidence.py      Asos zanjiri. Matn bu yerda YOZILMAYDI.
    extractor.py     Modelning yagona kirish nuqtasi + himoya devori.
    answers.py       Foydalanuvchi javoblari. Noto'g'ri javob — ochiq xato.
    confidence.py    Ishonch darajasi (stated / inferred asosida).
    llm.py           OpenAI klienti. Yupqa, almashtiriladigan.
    api.py           FastAPI. Yangi mantiq yo'q, faqat birlashtirish.
    ── kirish tizimi ──
    security.py      argon2id parol xeshlash + parol siyosati
    models.py        User, UserSession, InviteCode
    auth.py          Sessiyalar. Bazada token emas, xeshi.
    invites.py       Taklif kodlari. Bir marta ishlatiladi.
    throttle.py      Brute-force va so'rov limiti
    api_auth.py      /api/auth/*
    api_admin.py     /api/admin/* (router darajasida himoyalangan)
  scripts/
    admin.py         Birinchi admin, taklif kodlari, bloklash
  migrations/        Alembic
  data/
    nodes.yaml           Kod daraxti
    discriminators.yaml  Farqlovchi savollar
    attributes.yaml      Yopiq qiymatlar to'plami
    notes.yaml           ⚠️ Huquqiy matnlar — hammasi unverified
  tests/
    golden.yaml      54 misol: shartnoma

web/
  src/
    App.tsx          Marshrutlash + kirish himoyasi
    auth.tsx         Kirish holati. Token saqlanmaydi (HttpOnly cookie).
  src/pages/
    Landing.tsx      Ochiq sahifa. Cheklovlar yuqorida.
    AuthForms.tsx    Kirish va ro'yxatdan o'tish
    Classify.tsx     Tasnif (himoyalangan)
    Admin.tsx        Boshqaruv (faqat admin)
  src/components/
    Result.tsx       Natija. `status` tekshirilmasa kod ko'rsatib bo'lmaydi.
    Evidence.tsx     Asos zanjiri va rad etilganlar.
  src/__tests__/
    fixtures.json    Backend'dan generatsiya qilinadi (kontraktdan ajralmaydi)
```

## Ishlab chiqarishga chiqarish

Bitta VPS: nginx + systemd + Postgres, Docker'siz. To'liq qo'llanma:
**[`deploy/README.md`](deploy/README.md)**

```bash
# Bir marta — serverni sozlaydi
ssh root@<IP> 'bash /tmp/deploy/bootstrap.sh tilmon.uz'

# Har safar — testlar → build → rsync → migratsiya → restart
./deploy/deploy.sh tilmon.uz
```

`ENV=production` da ilova **xavfsiz bo'lmagan sozlama bilan ko'tarilmaydi**:
`SECURE_COOKIES=0`, bo'sh yoki namunaviy `SESSION_SECRET`, `.env.example`
dagi baza paroli, `localhost` yoki `*` origin — har biri ishga tushishni
to'xtatadi va nima qilish kerakligini aytadi. Sekin nosozlik jim
nosozlikdan yaxshiroq.

## Keyingi qadamlar

1. **Rasmiy matnni olish** — `ПП-181` ning o'zbek tilidagi ilovalarini
   yuklab olib, `nodes.yaml` ni almashtirish. Izohlar uchun manba hali
   aniqlanmagan — bu savol bojxona qo'mitasiga beriladi. Batafsil:
   [`data/VERIFICATION.md`](backend/data/VERIFICATION.md). Bu eng muhim
   ish: usiz tizim demo bo'lib qoladi.
2. **Qamrovni kengaytirish** — brokerlar eng ko'p adashadigan yana qaysi
   juftliklar bor? Har bir yangi juftlik uchun: farqlovchi + izoh +
   oltin to'plamga misollar.
3. **Live testlarni CI'ga** — model taxmin qila boshlaganini erta bilish
   uchun oltin to'plamning jim turish qismini muntazam yugurtirish.
4. **Tasnif tarixini saqlash** — qaysi savollar eng ko'p beriladi degan
   ma'lumot ontologiyani qayerda chuqurlashtirish kerakligini ko'rsatadi.
