# Ma'lumot tasdiqlash holati

Bu fayl `data/` dagi har bir matnning **qayerdan olinishi kerakligini**
qayd etadi. Loyihaning butun qiymati asosning haqiqiyligida ekan,
tasdiqlash ishini tasodifga qoldirib bo'lmaydi.

**Joriy holat: 27 izohdan 0 tasi tasdiqlangan.** Bu raqam har bir API
javobida `ontology_version` maydonida ko'rinadi (`seed-…-0tasdiq`).

---

## Manba inventarizatsiyasi

Quyidagilar 2026-yil avgustida tekshirildi.

### 1. lex.uz — ПП-181, 14.05.2025 ⭐ birlamchi manba

<https://lex.uz/ru/docs/7533469>

Joriy TN VED ni tasdiqlaydi, **2025-yil 1-iyundan** kuchga kirgan.

| | |
|---|---|
| Nima bor | Tasnif kodlari ro'yxati (1-ilova), boj stavkalari (2-ilova) |
| Nima **yo'q** | Bo'lim va boblarga izohlar — HTML sahifada mavjud emas |
| Til | Ilovalar **o'zbek tilida** ("Приложения № 1-2 приводятся на узбекском языке") |
| Format | Word va PDF yuklab olish tugmalari; ilovalar alohida fayllarda |
| Kirish | Ochiq, bepul |

**Bizga beradi:** kodlar, nomlar, boj stavkalari — `nodes.yaml` uchun.
**Bermaydi:** huquqiy izohlar — `notes.yaml` uchun boshqa manba kerak.

### 2. tarif.customs.uz — Integratsiyalashgan tarif

<https://tarif.customs.uz/ru/directory/tnved>

Kodlar bo'yicha qidiruv va tarif ma'lumotlari.

> ⚠️ **Texnik muammo:** serverning TLS sertifikat zanjiri to'liq emas —
> oraliq CA yuborilmaydi (`unable to get local issuer certificate`,
> `subject=CN=*.customs.uz`). Brauzer buni yashiradi, lekin `curl`,
> `requests` va boshqa mijozlar rad etadi. Import skripti oraliq
> sertifikatni o'zi bilan olib yurishi kerak bo'ladi.

### 3. nrm.uz — Norma huquqiy bazasi

<https://nrm.uz/>

Asosiy tafsir qoidalari (ОПИ) ochiq ko'rinadi, **izohlar to'lovli**
("Данная функция доступно только для клиентов"). Demo kirish taklif
qilinadi. O'zbek tili interfeysi bor.

### 4. Ikkilamchi manbalar (EAES/Rossiya)

<https://www.alta.ru/poyasnenia/G61/> · <https://www.ifcg.ru/kb/tnved/notes/code/62/>

O'zbekiston EAES a'zosi emas, lekin TN VED bir xil Garmonizatsiyalashgan
Tizimga (GS) asoslanadi va bo'lim/bob izohlari GS xalqaro konvensiyasidan
keladi — ya'ni mazmunan bir xil.

> **Diqqat:** bu manbalar **yo'naltiruvchi**, hujjatli emas. Ulardan
> olingan matn `status: official` bo'la olmaydi. Ular faqat "rasmiy
> matnda nima yozilgan bo'lishi kerak" ni bilish va tarjimani
> solishtirish uchun ishlatiladi.

---

## Aniqlangan nomuvofiqliklar

Manba tekshiruvi davomida seed matnlarida **ikkita mazmuniy xato**
topildi. Ikkalasi ham tuzatildi, lekin `unverified` bo'lib qolmoqda.

### `N_61_izoh_1` — to'liqmas edi

| | |
|---|---|
| Edi | «Ushbu bob faqat tayyor trikotaj buyumlariga nisbatan qo'llaniladi.» |
| Bo'ldi | «Ushbu bobga faqat **mashinada yoki qo'lda to'qilgan** tayyor trikotaj buyumlar kiradi.» |
| Nima yetmasdi | Ishlab chiqarish usuli («машинного или ручного вязания») |

### `N_62_izoh_1` — mazmunan noto'g'ri edi

| | |
|---|---|
| Edi | «…faqat tayyor to'qima matodan tikilgan buyumlarga nisbatan qo'llaniladi va trikotaj buyumlarni qamramaydi.» |
| Bo'ldi | «…50–56, 58 va 59-boblardagi materiallardan tayyorlangan… kiyim va kiyim aksessuarlari kiradi.» |
| Nima xato edi | Haqiqiy 1-izoh **materiallarning kelib chiqishini** belgilaydi, «trikotaj emas» degan istisnoni emas. Ikkinchisi bob **sarlavhasida** turadi. |

Bu ikki xato tizim ishlashiga ta'sir qilmadi — farqlovchi mantiq to'g'ri
edi — lekin **asos matni noto'g'ri ko'rsatilardi**. Aynan shuning uchun
seed ma'lumot hech qachon `official` deb belgilanmasligi kerak.

---

## Tasdiqlash tartibi

1. **`ПП-181` ilovalarini yuklab olish** (o'zbek tilida, Word/PDF) →
   kodlar, nomlar, boj stavkalarini `nodes.yaml` ga o'tkazish →
   `status: official`.
2. **Izohlar manbasini aniqlash** — TN VED ilovalarida bo'lim/bob
   izohlari bormi? Yo'q bo'lsa, ular qaysi hujjatda tasdiqlangan?
   Bu savol bojxona qo'mitasiga yoki huquqshunosga beriladi.
3. **Har bir izohni ko'chirish** — so'zma-so'z, qisqartirmasdan.
   `source_hint` maydoniga aniq havola yozish.
4. **`status: official` qo'yish** — faqat 3-qadamdan keyin.

Kod hech qanday o'zgarish talab qilmaydi: `test_har_bir_izoh_status_maydoniga_ega`
ikkala qiymatni ham qabul qiladi, `ontology_version` esa hisobni
avtomatik yangilaydi.

---

## Nima uchun bu shunchalik muhim

Asosiy tafsir qoidasi (ОПИ 1) tizimning butun asosini belgilaydi:

> Bo'lim, guruh va kichik guruh nomlari faqat qulaylik uchun keltiriladi;
> **yuridik maqsadlar uchun** tasnif tovar pozitsiyalari matnlari **va
> tegishli bo'lim yoki guruh izohlari** asosida amalga oshiriladi.

Ya'ni izohlar bezak emas — ular tasnifning huquqiy asosi. Noto'g'ri
izoh = noto'g'ri tasnif = jarima.
