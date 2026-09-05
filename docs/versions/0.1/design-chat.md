# گفت‌وگوی طراحی — Design chat

> در گامِ `/design`، دستیار پرامپتِ طراحی را در همین فایل (زیرِ «دور ۱ / من گفتم») می‌نویسد.
> - اگر از **ابزارهای وب** (Claude Web Design / Google Stitch / v0 / Figma) استفاده می‌کنی: پرامپت را از همین‌جا کپی کن و در ابزار بگذار؛ هر پیامی که ردوبدل شد را زیرِ بخش‌های مربوطه در این فایل کپی کن.
> - اگر از **طراحیِ تعاملی توسطِ دستیار** استفاده می‌کنی: نظرات و درخواست‌های تغییرت را در دورهای بعدی همین فایل بنویس تا اعمال شوند.
>
> **چرا؟** تصمیم‌های واقعیِ محصولت در حین طراحی گرفته می‌شوند. این فایل، به‌علاوهٔ پوشهٔ `UI/`، خروجیِ طراحیِ توست که در روز دوم برای تطبیق اسناد (`/reconcile`) خوانده می‌شود.

---

## دور ۱

### من گفتم:

<!-- این پرامپت را دستیار در گامِ /design نوشت. اگر از ابزارِ وب استفاده می‌کنی، از «شروعِ پرامپت» تا «پایانِ پرامپت» را کپی کن و همان‌جا بگذار. -->

--- شروعِ پرامپت ---

I need you to design the screens for a product called **Size** («سایز»). Design in **Persian (Farsi), right-to-left**. All visible text must be in Persian.

**What the product does**

Online clothing shops in Iran lose sales and get returns because customers don't know which size to buy. Size solves this: the customer lays out a garment they already own and are happy with the fit of, places any bank-card-sized card on top for scale, and photographs it from above. The system measures the garment and tells them which size of the shop's product to buy — expressed as fit advice, not a bare letter.

**Two audiences, two very different design problems**

- **Buyer pages — mobile only.** They arrive from an Instagram link and open inside Instagram's in-app browser. They are mid-purchase, hesitant, in a hurry, and have never heard of us. These screens must be extremely sparse: one job and one primary button per screen, large text, generous space.
- **Seller panel — mobile-first, but must stay tidy on desktop.** Working screens for data entry, denser and more utilitarian. Instagram shop owners run their business from a phone, but the size chart is easier to fill on a bigger screen.

**Visual direction**

- Personality: trustworthy, simple, unpretentious. Calm and safe, never advert-like — the buyer is hesitating and anything flashy loses them.
- White or near-white base, dark text, and **one** accent colour: a calm, slightly dark blue. Use the accent only on primary buttons and the recommended-size row.
- The accent is deliberately neutral because different shop names appear at the top of the buyer page and it must not clash with any brand.
- Medium, soft corner rounding. Not sharp and formal, not overly round and childish.
- Persian numerals displayed throughout.

**Screens to design — buyer (mobile)**

1. **صفحهٔ آغاز** — Shop name at top, product name below, one short sentence explaining what will happen, one large «شروع» button. Two small lines at the bottom: «عکست نیم‌ساعت بعد پاک می‌شود» and «قدرت‌گرفته از سایز». Also show the error variant: the product is no longer active.
2. **صفحهٔ راهنمای عکس** — The most important screen in the product. A simple line illustration of a garment laid flat with a card on it. Three short numbered instructions: lay one of your own well-fitting garments flat / place a bank-card-sized card on it / photograph from directly above. A small note that a national ID card, metro card, or the back of a bank card all work and the card number is not needed. Large button: «عکس بگیر یا انتخاب کن».
3. **صفحهٔ در حالِ بررسی** — A calm waiting state, a few seconds. Simple activity indicator and «داریم لباست را اندازه می‌گیریم…». Nothing else, no buttons.
4. **صفحهٔ جواب** — The payoff screen. At top, the recommended size with a «پیشنهادِ ما» badge. Below, **every** available size as a row: size name plus a fit description — «تنگ‌تر از لباسِ خودت» / «مثلِ لباسِ خودت» / «کمی آزادتر» / «آزاد». The recommended row is highlighted. Below that, at most two short notes about secondary measurements, e.g. «آستینش کمی بلندتر از لباسی است که فرستادی». **Never show raw measurement numbers.** At the bottom, an optional «برگرد و خرید کن» button and the «قدرت‌گرفته از سایز» line. **Also design the variant where no size fits**: an honest message that the product isn't available in their size, plus the nearest size with a frank explanation.
5. **صفحهٔ عکسِ ردشده** — Must be helpful, never blaming; this is where someone either retries or leaves forever. One clear sentence naming exactly what was wrong (card not found / photo blurry / garment not fully in frame), the guide illustration again, and a large «دوباره عکس بگیر» button.
6. **صفحهٔ جوابِ منقضی‌شده** — Shown when a result link is opened after 30 minutes. «این جواب پاک شده — عکس‌ها را بیشتر از نیم‌ساعت نگه نمی‌داریم.» plus a «از اول شروع کن» button.

**Screens to design — seller (mobile-first, tidy on desktop)**

7. **صفحهٔ ورود** — Product name, two fields, one button. Error: «نام کاربری یا رمز درست نیست» without saying which. No password-reset link; instead one line: «رمزت را فراموش کردی؟ به ما پیام بده.»
8. **فهرستِ محصول‌ها** — Rows showing product name, garment type, number of sizes, and whether the link is live or the chart is still incomplete. A «محصولِ تازه» button. Design the empty state too.
9. **صفحهٔ محصول** — Product name; garment type (بالاتنه / پایین‌تنه); a choice of whether the seller's numbers are **circumference («دور») or flat width («عرض»)**, with a small illustration showing the difference — this choice is critical and must be visually prominent; optional shop product-page link; optional product photo.
10. **صفحهٔ جدولِ سایز** — The seller's heaviest task. **On mobile: one card per size**, expanding to show its measurement fields. **On desktop: the full grid**, all sizes and all measurements at once. In both, the two main criteria appear above the rest and are marked as required. A short hint next to each measurement saying where on the garment it is taken. A calm banner while incomplete: «لینکِ این محصول هنوز فعال نشده — دو اندازهٔ اصلی برای همهٔ سایزها لازم است.» Design the empty state.
11. **صفحهٔ لینک و نصب** — The product link in a large box with a copy button. Below, an "if you have a website" section with a paste-in snippet and its own copy button. A small preview of what the buyer sees. Empty state: if the chart is incomplete, show that instead of the link.
12. **فهرستِ درخواست‌ها** — Requests in time order: which product, when, which size was recommended, or that the photo was rejected. **No photos and nothing identifying the buyer.** A summary line at top: «این ماه ۲۳ نفر سایز گرفتند.» Design the empty state.

**Screens to design — operator**

13. **فهرستِ فروشگاه‌ها** — Shops with name, Instagram handle, phone, product count, active status. A «فروشگاهِ تازه» button that creates the shop and its account and **shows the generated password in full** so it can be passed to the seller.
14. **صفحهٔ معیارهای اندازه** — Per garment type, the list of measurements with name, whether it is a main criterion, whether it is a circumference or a length, and where it is measured. A «معیارِ تازه» button.

**Reference: the twelve measurements that ship**

- بالاتنه: دورِ سینه★ · طولِ لباس★ · عرضِ شانه · طولِ آستین · دورِ بازو · دورِ کمرِ لباس
- پایین‌تنه: دورِ کمر★ · قد★ · دورِ باسن · دورِ ران · دورِ دمِ پا · فاق

(★ = main criterion, the two that decide the size.)

**How to work with me**

Ask everything in plain text. Do not generate uncopyable forms. Give me **at least two distinct options per screen**. Export the result as a `UI/` folder.

--- پایانِ پرامپت ---

### دیزاین گفت:

خواندم — PRD، UX و مدلِ داده هر سه کامل‌اند و جهتِ بصری هم در خودشان تعیین شده، پس دربارهٔ رنگ و لحن سؤالی ندارم. شش سؤال دارم که واقعاً روی چیزی که می‌سازم اثر می‌گذارد. اگر حوصله نداری، فقط بنویس «با پیش‌فرض‌ها برو» و شروع می‌کنم.

**۱. «دو گزینه به ازای هر صفحه» را چطور می‌خواهی؟** سه برداشتِ ممکن هست:

- الف) دو **چیدمانِ متفاوت** از همان زبانِ بصری — مثلاً صفحهٔ جواب یک‌بار «سایزِ پیشنهادی به‌عنوانِ کارتِ بزرگِ جدا + فهرستِ بقیه زیرش» و یک‌بار «همه در یک فهرست، ردیفِ پیشنهادی برجسته». تفاوت در ساختار و سلسله‌مراتب.
- ب) دو **زبانِ بصری** کاملاً جدا (دو تایپوگرافی/فاصله‌بندی/شخصیت) که روی هر ۱۴ صفحه اجرا می‌شوند و تو یکی را انتخاب می‌کنی.
- پیش‌فرضِ من: **الف** — چون تم را خودت قطعی کرده‌ای و کارِ باز مانده چیدمان است. ولی اگر ب را می‌خواهی، منطقی است که اول فقط روی ۳ صفحهٔ کلیدی (آغاز، راهنمای عکس، جواب) دو زبان بسازم، انتخاب کنی، بعد بقیه.

**۲. ساختارِ پوشهٔ `UI/`؟** پیش‌فرضِ من: یک فایل به‌ازای هر گروه (`UI/Buyer.dc.html`، `UI/Seller.dc.html`، `UI/Operator.dc.html`) که همهٔ صفحه‌ها و حالت‌هایشان را کنار هم روی یک بوردِ قابلِ پن/زوم نشان می‌دهد، به‌علاوهٔ یک `UI/index.html` به‌عنوانِ فهرست. جایگزین: یک فایل به‌ازای هر صفحه (۱۴ فایل). کدام؟

**۳. صفحه‌های خریدار: تصویرِ ثابت یا قابلِ کلیک؟** پیش‌فرضِ من: تصویرِ ثابت در قابِ گوشی، همهٔ حالت‌ها کنارِ هم دیده می‌شوند (برای بررسیِ طراحی بهتر است). اگر مسیرِ کلیک‌شدنی می‌خواهی (شروع → راهنما → بررسی → جواب) بگو، جدا می‌سازم.

**۴. قلم؟** پیش‌فرضِ من: **وزیرمتن** برای همه‌چیز (خوانا، بی‌ادعا، برای اعدادِ فارسی هم خوب است). گزینهٔ دیگر: **استعداد** یا **یکان‌بخ**. اگر قلمِ برندِ خاصی داری، فایلش را بفرست.

**۵. دادهٔ نمونه — اسم‌های واقعی داری یا بسازم؟** لازم دارم: نامِ یک فروشگاهِ نمونه، نامِ یک محصولِ نمونه، و نام‌گذاریِ سایزها (S/M/L یا ۳۶/۳۸/۴۰). پیش‌فرضِ من: فروشگاه «نخ و نقش»، محصول «تی‌شرت اورسایزِ کتان»، سایزها اسمال/مدیوم/لارج/ایکس‌لارج — و یک محصولِ پایین‌تنه با ۳۶ تا ۴۴ برای اینکه هر دو حالتِ سایز‌گذاری دیده شود.

**۶. یک محدودیت که باید بدانی:** من عکس تولید نمی‌کنم. جای عکسِ محصول یک placeholder می‌گذارم. تصویرِ راهنما (لباسِ پهن‌شده + کارت رویش) و تصویرِ «دور در برابر عرض» را با خطوطِ هندسیِ ساده می‌کشم — تمیز درمی‌آید ولی در حدِ دیاگرام است، نه تصویرسازیِ حرفه‌ای. اگر بعداً تصویرسازِ واقعی داشتی، جایش آماده می‌ماند. مشکلی نیست؟
---

## دور ۲

### من گفتم: اوکیه همش

### دیزاین گفت:
پوشهٔ `UI/` آماده است — از `Index.dc.html` شروع کن، سه بورد به آن وصل‌اند:

- **`Buyer.dc.html`** — ۶ صفحه، شناسه‌های `1a`–`6b`. حالت‌های خطا و خالی (محصولِ غیرفعال، طول‌کشیدنِ بررسی، «هیچ سایزی اندازه نیست») به‌عنوانِ قابِ جدا کنارِ هر گزینه‌اند.
- **`Seller.dc.html`** — ۶ صفحه، `7a`–`12b`. جدولِ سایز هم به‌صورتِ کارتِ تاشوی گوشی و هم جدولِ کاملِ کامپیوتر با دو ستونِ اصلیِ نشان‌دار.
- **`Operator.dc.html`** — `13a`–`14b`، شاملِ نمایشِ کاملِ رمزِ ساخته‌شده در دو حالتِ متفاوت (پنجره یا نوارِ ماندگار).

شناسه‌ها به‌جای `1a/1b` بر اساسِ شمارهٔ خودِ صفحه‌ها هستند تا با فهرستِ خودت یکی باشد؛ دورِ بعد `4c`/`4d` ادامه می‌گیرد.

سه چیز که عمداً تصمیم گرفتم و ممکن است بخواهی عوض کنی: در صفحهٔ جواب **مدیوم** را پیشنهاد گذاشتم تا هر چهار توصیفِ فیت یک‌بار دیده شود؛ خطای «خانهٔ خالی» را با یک نارنجیِ خیلی کم‌رنگ نشان دادم (اگر می‌خواهی فقط با یک آبی کار کنیم، حذفش می‌کنم)؛ و آدرسِ نمونه را `sizeapp.ir` گذاشتم.
سه اشکالِ راست‌به‌چپ درست شد: برچسبِ فارسیِ داخلِ قطعهٔ چسباندنی با `<bdi>` جدا شد تا کد سالم خوانده شود، خطِ شناسه‌های `Index` فقط روی بخشِ لاتین جهت‌دهی می‌شود، و برچسبِ «کارت» در تصویرِ `5b` بالای کارت رفت و از روی آستین کنار شد.

---

<!-- به همین شکل ادامه بده. هر رفت‌وبرگشت یک «دور». -->

---

## در پایان — چه چیزهایی عوض شد؟

<!-- بعد از اینکه از طرح‌ها راضی شدی، اینجا در چند خط بنویس: موقعِ طراحی چه تصمیمی عوض شد که با سندهای قبلی (سندِ محصول، مدلِ داده، تجربهٔ کاربری) نمی‌خواند؟ لازم نیست کامل باشد — روزِ دوم دستیار خودش دنبالِ تناقض‌ها می‌گردد، ولی هر چیزی که اینجا بنویسی کارِ آن روز را کوتاه‌تر می‌کند. -->

---
## دور ۳

### من گفتم: 
1a but i want the photo of the product on it  
2a  
3a  
4a  
5a  
6b  
7a  
8a  
9a  
10a  
11a  
12a  
13b  
14b

### دیزاین گفت:
`UI/Screens v2.dc.html` — فقط چیدمان‌های انتخابیِ تو، بی‌گزینه و بی‌شناسه، به‌ترتیبِ ۱ تا ۱۴ با حالت‌های خطا و خالی کنارِ هر صفحه.

در صفحهٔ آغاز عکسِ محصول را وسط و بالای نامِ محصول گذاشتم (نه کنارش، تا وسط‌چینیِ ۱a حفظ شود)؛ در حالتِ محصولِ غیرفعال هم همان عکس محو نشسته تا خریدار بداند حرف از کدام محصول است.

فایل‌های دورِ اول (`All Screens` و سه بوردِ جدا) دست‌نخورده ماندند؛ اگر دیگر لازم نیستند بگو حذف کنم.