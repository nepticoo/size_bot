# Architecture

> Living document. Written at `/plan`, before any application code. The user does not read it; it is the **reference** you re-read and update on every fix, feature and new version. Follows `docs/constitution/02-tech-stack.md`. This version's task list is `docs/versions/0.1/checklist.md`.
>
> Business sources of truth: `prd.md` · `data-model.md` · `ux.md` · `test-scenarios.md` · `docs/decisions.md` (52 decisions). Where this document and those disagree, **they win** and this one is wrong.

## Overview

Size measures a garment the buyer already owns from one photograph, using a bank-card-sized rectangle in the frame as the scale reference, and compares it against the seller's size chart to recommend a size.

One FastAPI process serves both the JSON API under `/api` and the built React bundle, on `APP_PORT` from `.env` (**8000** — `docs/profile.md`). One SQLite file at `data/app.db` through SQLAlchemy, every schema change an Alembic migration. Uploaded photos go to `uploads/` behind a small storage interface and are deleted thirty minutes after upload. No cache, no queue, no external service of any kind (`dependencies.md`).

Three audiences, one process: buyer pages (public, mobile only), seller panel (session auth), operator panel (session auth, role `operator`).

```
backend/
  app/
    main.py               app factory, static mount, startup tasks
    config.py             settings from .env (pydantic-settings)
    db.py                 async engine, session dependency
    models/               SQLAlchemy models (one module per group)
    schemas/              Pydantic v2 request/response models
    api/
      buyer.py            public endpoints
      seller.py           panel endpoints
      operator.py         admin endpoints
      auth.py             login / logout / session
    core/
      security.py         password hashing, signed session cookie
      codes.py            unguessable link + view codes
      digits.py           Persian/Latin digit handling
      storage.py          the file-storage interface
    measure/
      pipeline.py         photo -> measurements (orchestration)
      card.py             card detection + homography
      segment.py          garment mask
      rules.py            measure_rule implementations
    sizing/
      normalise.py        seller numbers -> circumference
      compare.py          fit bands, recommendation, notes
    jobs/
      runner.py           asyncio poller over the jobs table
      handlers.py         delete_photo
  alembic/                migrations, from the first commit
  tests/
frontend/
  src/
    routes/buyer/ routes/seller/ routes/operator/
    lib/api.ts  lib/digits.ts  store/
    fonts/                    Vazirmatn woff2, self-hosted
data/     uploads/     run.sh
```

## Frontend (React 19 + Vite 7 — built to static, served by the backend)

Relative `/api/...` paths only; no CORS, no base-URL setting. TanStack Query v5 for server state, Zustand 5 for the little local state there is (the size-table editor draft). `dir="rtl"` on `<html>`, Vazirmatn **self-hosted from `src/fonts/`** — the design file pulled it from Google Fonts, which must not be relied on from inside Iran or from the deployed server. Persian digits everywhere on display; `lib/digits.ts` normalises Persian and Arabic-Indic digits to Latin on every numeric input (scenario 13).

Routes:

| Path | Screen (ux.md name) |
|---|---|
| `/p/:linkCode` | صفحهٔ آغاز → راهنمای عکس → در حالِ بررسی (one route, three states) |
| `/r/:viewCode` | صفحهٔ جواب · صفحهٔ جوابِ منقضی‌شده |
| `/panel/login` | صفحهٔ ورود |
| `/panel` | فهرستِ محصول‌ها |
| `/panel/products/:id` | صفحهٔ محصول |
| `/panel/products/:id/sizes` | صفحهٔ جدولِ سایز |
| `/panel/products/:id/link` | صفحهٔ لینک و نصب |
| `/panel/requests` | فهرستِ درخواست‌ها |
| `/admin/shops` | فهرستِ فروشگاه‌ها |
| `/admin/criteria` | صفحهٔ معیارهای اندازه |

**The answer URL is the shareable link.** `/r/:viewCode` is where the buyer lands after processing, so «کپیِ لینکِ این جواب» (decision 45) copies `window.location.href` — nothing extra to mint. This matters because the Instagram in-app browser has no address bar.

Buyer pages are mobile-only by design; the panel is mobile-first with a desktop grid for the size table (decision 38).

## Backend / API (FastAPI)

Session is a signed cookie (`itsdangerous`, `SECRET_KEY`), HttpOnly, SameSite=Lax, carrying `{account_id, role, acting_as_shop_id, issued_at}`. Logout clears it (decision 43).

**Resolving "the current shop"** — one dependency, used by every seller endpoint:
- role `seller` → their own shop, always; `acting_as_shop_id` is ignored and can never be set on a seller session.
- role `operator` with `acting_as_shop_id` → that shop (decision 46).
- role `operator` without it → 403 on seller endpoints.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/p/{link_code}` | shop name, product name, photo URL, active flag. 404 for unknown or inactive (scenarios 8, 9) |
| `POST` | `/api/p/{link_code}/measure` | multipart photo. Returns `{view_code}`. Creates the request, schedules deletion |
| `GET` | `/api/r/{view_code}` | the answer, or `410 Gone` once expired (scenario 7) |
| `POST` | `/api/auth/login` · `/api/auth/logout` | one error message for both wrong username and wrong password (scenario 10) |
| `GET` | `/api/me` | account, role, shop, impersonation banner text |
| `GET/POST` | `/api/products` · `GET/PATCH` `/api/products/{id}` | |
| `POST` | `/api/products/{id}/deactivate` | decision 47 |
| `POST` | `/api/products/{id}/numbers-kind` | the guarded switch — decision 50 |
| `GET` | `/api/products/{id}/sizes` | rows plus `is_complete` per size |
| `POST/DELETE` | `/api/products/{id}/sizes` · `/api/sizes/{id}` | decision 51 |
| `PUT` | `/api/sizes/{id}/measurements` | upsert by criterion |
| `GET` | `/api/products/{id}/link` | link, snippet, readiness detail |
| `GET` | `/api/requests` | no photo, nothing identifying (scenario 15) |
| `GET/POST` | `/api/admin/shops` · `POST /api/admin/shops/{id}/impersonate` | |
| `GET/POST` | `/api/admin/criteria` | |

Uploads: 10 MB cap, `image/jpeg|png|webp|heic` only, re-encoded on ingest. A small per-IP throttle on `/measure` (in-memory counter, 20/hour) — the endpoint is public and does real CPU work.

**Measurement must not block the event loop.** The pipeline is CPU-bound OpenCV; the endpoint runs it via `asyncio.to_thread` and the request row moves `processing → answered | rejected`.

## Data model (SQLAlchemy + Alembic over one SQLite file)

Business source: `data-model.md`. Technical shape here. All timestamps UTC. Money: none. Lengths: centimetres, stored as `Numeric(5,1)`, always positive.

| Table | Columns |
|---|---|
| `accounts` | `id` · `username` **unique** · `password_hash` · `role` (`operator`\|`seller`) · `is_active` · `created_at` |
| `shops` | `id` · `name` · `instagram` null · `phone` null · `is_active` · `account_id` FK→accounts **unique** (one-to-one) |
| `garment_types` | `id` · `name` **unique** · `is_active` |
| `measurement_criteria` | `id` · `garment_type_id` FK · `name` · `is_main` · `kind` (`circumference`\|`length`) · `where_text` · `measure_rule` **null** · `sort_order` — unique(`garment_type_id`,`name`) |
| `products` | `id` · `shop_id` FK · `name` · `garment_type_id` FK · `numbers_kind` (`circumference`\|`width`) · `link_code` **unique** · `shop_url` null · `photo_path` null · `is_active` · `created_at` |
| `product_sizes` | `id` · `product_id` FK · `name` · `sort_order` — unique(`product_id`,`name`) |
| `size_measurements` | `id` · `product_size_id` FK · `criterion_id` FK · `value_cm` — unique(`product_size_id`,`criterion_id`) |
| `measure_requests` | `id` · `product_id` FK · `created_at` · `status` (`processing`\|`answered`\|`rejected`) · `reject_reason` null · `recommended_size_id` FK null · `photo_path` null · `photo_delete_at` · `view_code` **unique** |
| `extracted_measurements` | `id` · `request_id` FK · `criterion_id` FK · `value_cm` |
| `jobs` | `id` · `kind` · `run_at` · `payload` JSON · `done_at` null · `attempts` · `last_error` null |

`link_code` and `view_code` are `secrets.token_urlsafe(8)` — never sequential (scenario 9).

**`measure_rule` is the one column `data-model.md` does not have** (open question ۵۶). `where_text` is prose for the seller; it cannot drive an algorithm. `measure_rule` is a key the engine knows (`chest_width`, `garment_length`, …). **Nullable on purpose:** a criterion the operator adds with no rule is still shown to the seller and still typed into the chart — it simply is not extracted from the photo. That is exactly decision 31's world, degrading gracefully instead of breaking.

**Size completeness** — `is_complete(size)` = it has a value for **every `is_main` criterion** of the product's garment type. Used in two different places and they are not the same rule (decision 49):
- **First activation of the link:** every size complete → link goes live.
- **Once live:** the link **stays** live. An incomplete size is excluded from answers as though it did not exist, and the seller sees an amber warning.

Seed migration: two garment types and the twelve criteria of `prd.md`, with rules and `is_main` flags.

**Post-MVP note — record, do not build.** Every query goes through SQLAlchemy and every schema change through Alembic, so PostgreSQL later is one `DATABASE_URL` plus the same migrations. Never use a SQLite-only or Postgres-only feature. Redis and a real queue belong to that same later moment.

## The measurement pipeline

Input: one photo. Output: a value per criterion that has a `measure_rule`, or a rejection reason. Runs entirely on this machine (`dependencies.md`).

1. **Downscale** long edge to 2000 px, remember the factor.
2. **Blur check first.** Variance of the Laplacian over the whole frame; below threshold → reject `blurry`. Doing this *before* card detection is what makes scenario 3 report «عکس تار است» rather than «کارت پیدا نشد» — a blurry photo also fails card detection, so order decides the message.
3. **Find the card.** Canny → dilate → `findContours` → `approxPolyDP`, keep convex 4-gons. Score each by how close its perspective-corrected aspect ratio is to **1.5858** (ISO/IEC 7810 ID-1: 85.60 × 53.98 mm — a national ID card, a metro card and a bank card are all this size), plus area between 0.2 % and 15 % of frame and high solidity. No candidate → reject `card_not_found`.
4. **Rectify.** `getPerspectiveTransform` from the card's four corners to a rectangle of 85.60 × 53.98 mm at **10 px/mm**, then `warpPerspective` the whole frame. **After this, 1 mm is 10 px everywhere on the table plane** — the card gives scale *and* corrects the tilt of a hand-held phone in one step. Only exact for the card's plane; garment thickness of a few millimetres is far inside our error budget.
5. **Segment the garment.** Sample the four corners for the background colour, threshold in Lab distance, largest connected component excluding the card quad, morphological close, fill holes. Mask touching the frame border on more than 2 % of its perimeter → reject `garment_cropped`.
6. **Apply each `measure_rule`** to the mask (see below) and convert px → cm.
7. **Flat span → circumference.** A horizontal span across a laid-flat garment is **half** the circumference: for a criterion of `kind = circumference`, buyer value = `2 × span`. `kind = length` is taken as-is.

**The measure rules.** Silhouette convention: y grows downward, the garment's own bounding box defines top/bottom.

| rule | how |
|---|---|
| `chest_width` ★ | horizontal span 1 cm below the armpit notches (deepest inward notches of the left/right silhouette in the upper third) |
| `garment_length` ★ | highest shoulder point → lowest hem point, vertical |
| `shoulder_width` | horizontal span at the y of the highest shoulder points |
| `sleeve_length` | shoulder point → farthest sleeve-tip point along the sleeve axis |
| `bicep_width` | widest span across the sleeve region, perpendicular to the sleeve axis |
| `garment_waist_width` | narrowest body span between the chest line and the hem |
| `waist_width` ★ | horizontal span of the top edge |
| `bottom_length` ★ | top edge → lowest hem, vertical |
| `hip_width` | widest span in the upper third |
| `thigh_width` | span 2 cm below the crotch point (highest point of the inner notch between the legs) |
| `leg_opening_width` | span at the hem |
| `rise` | top edge → crotch point, vertical |

**Note this property, it is not an accident:** the four ★ rules — the *main* criteria that actually decide the size — are the simplest and most robust of the twelve (one horizontal span, one vertical span, per garment type). The fragile ones (`sleeve_length`, `shoulder_width`) are secondary and can only ever produce a note. A poor measurement there costs a sentence; it never costs a wrong size.

Accuracy target from `prd.md`: about **0.5 cm** on a good photo. Consecutive sizes are 2–4 cm apart in width, so the error budget is comfortable. **Never promise a number on screen.**

## The sizing algorithm

**Step 1 — normalise the seller's chart to circumference.**

```
value = stored value
if criterion.kind == 'circumference' and product.numbers_kind == 'width':
    value = value * 2
# kind == 'length' is NEVER doubled, whatever numbers_kind says
```

That last line is the whole of scenario 18 and the easiest thing in this codebase to get wrong. `numbers_kind` says how the seller wrote their **circumference** figures. A length is a length (`data-model.md`: «فقط برای دورها قاعدهٔ تبدیلِ دور و عرض معنا دارد»).

**Step 2 — compare, per complete size.** `d_circ = size.main_circumference − buyer.main_circumference`, `d_len` likewise.

**Step 3 — fit bands**, on `d_circ` in cm (open question ۵۳):

| `d_circ` | word |
|---|---|
| < −6 | خیلی تنگ‌تر از لباسِ خودت |
| −6 … −2 | تنگ‌تر از لباسِ خودت |
| −2 … +3 | مثلِ لباسِ خودت |
| +3 … +8 | کمی آزادتر |
| > +8 | آزاد |

Sized against reality: buyer circumference carries about ±1 cm (a ±0.5 cm span, doubled), and consecutive sizes are 4–8 cm apart in circumference. A "same" band narrower than ±2 would flicker on measurement noise; wider than ±3 would swallow a whole size.

**Step 4 — recommend** the size with the smallest `|d_circ|`; on a tie prefer the larger. Circumference decides, always (decision 25) — a garment that is too tight is unwearable, while a few centimetres of length is something many people wear on purpose.

**Step 5 — no size fits** (open question ۵۴) when the best `d_circ < −6` or `> +12`. Then: the honest message plus that nearest size and a frank sentence.

**Step 6 — the notes**, two separate groups that never mix (decision 48):
- **The length line, always, when `|d_len| > 1.5`** — mandatory, above the others, outside the two-line cap. This is part of the answer, not a nicety.
- **Secondary notes**, at most two, largest difference first, for criteria differing by more than **2 cm length / 4 cm circumference** (open question ۵۵). Criteria with no `measure_rule`, or no extracted value, are skipped silently.

## Background work (no cache, no queue)

One `asyncio` task from app startup polls `jobs` every 30 s for `run_at <= now AND done_at IS NULL`.

`delete_photo` is the only kind in 0.1: scheduled at upload for `created_at + 30 minutes` (decision 52 — from **upload**, never extended by a view), deletes the file through the storage interface and nulls `photo_path`.

**Two safety nets, because this is the product's central promise:**
1. **A startup sweep** runs the same deletion for anything already overdue — if the process was down at the appointed minute, the file still goes the moment it comes back.
2. **A belt-and-braces pass** in the same tick deletes any file whose `measure_requests.photo_delete_at <= now` even if its job row was lost.

`GET /api/r/{view_code}` computes expiry from `photo_delete_at`, so a late reader gets `410 Gone` even if the sweep has not run yet. `extracted_measurements` are never deleted; they are anonymous and are the future signal for a wrong seller chart (roadmap ۹).

## File storage (a folder on disk behind one small interface)

```python
class Storage(Protocol):
    def save(self, data: bytes, suffix: str) -> str   # returns an opaque key
    def open(self, key: str) -> bytes
    def delete(self, key: str) -> None
```
`LocalStorage` writes under `UPLOADS_DIR`, sharded by date. Keys are stored, never paths, so a bucket can replace it at `/deploy` with a setting rather than a rewrite. **No photo is ever served to the seller** — there is no endpoint that returns one (scenario 27).

## Dependencies / integrations

**None.** See `dependencies.md`. No API key, no bot token, no SMS, no payment gateway, nothing to wait for. `SECRET_KEY` and the operator login are generated locally at `/setup-dev`. Because nothing external is called, the choice of server location at `/deploy` is unconstrained.

## Main flows, end to end

**Buyer.** `GET /p/:code` → 404 if the product or shop is inactive → guide → `POST /measure` (multipart) → row `processing`, deletion job scheduled → pipeline in a worker thread → reject (reason recorded, `rejected`) or measure → normalise chart, compare, pick → `answered` with `recommended_size_id` → `{view_code}` → client navigates to `/r/:viewCode`. Thirty minutes after upload the photo is gone and that URL returns `410`.

**Seller.** login → products → new product (name, type, **circumference-or-width**) → size table → per size, values per criterion → all sizes complete → link goes live → copy link and snippet. Adding a size later never takes the link down.

**Operator.** shops → new shop creates account + shop in one transaction and returns the generated password **once, in clear** → or `impersonate` → the same six seller screens with a banner → criteria, where a new one appears in the next product's chart with no rebuild (scenario 25).

## How it runs locally

`bash run.sh` — builds the frontend, applies migrations, starts Uvicorn on `APP_PORT` from `.env` (8000), detached, log in `run.log`. It is the only way the app starts or restarts. No containers on this machine.

## How it is deployed

Filled in at `/deploy`. Not part of the build.

---

## چه چیزی باید نصب باشد

پایه — مستقل از این محصول:

- **Python 3.14** (installed on this machine)
- **Node.js 26** (installed on this machine)

چیزی که این محصول اضافه می‌کند:

| بسته | برای چه | نکته |
|---|---|---|
| `opencv-python-headless` | پیدا کردنِ کارت، اصلاحِ پرسپکتیو، جدا کردنِ لباس | حتماً `-headless`؛ نسخهٔ معمولی به کتابخانه‌های گرافیکی سیستم نیاز دارد که روی سرور نیستند |
| `numpy` | همراهِ ناگزیرِ OpenCV | معمولاً با آن نصب می‌شود |
| `Pillow` | خواندنِ فایلِ آپلودی، چرخشِ EXIF، تبدیل به JPEG | عکسِ گوشی تقریباً همیشه EXIF orientation دارد؛ بدونِ اصلاحش لباس ۹۰ درجه چرخیده اندازه‌گیری می‌شود |
| `pillow-heif` | عکسِ HEIC آیفون | آیفون پیش‌فرض HEIC می‌دهد و بدونِ این، آپلودِ کاربرانِ آیفون رد می‌شود |
| `bcrypt` | رمزِ فروشنده | |
| `itsdangerous` | کوکیِ امضاشدهٔ نشست | |

فونتِ **وزیرمتن** به‌صورتِ فایلِ `woff2` داخلِ `frontend/src/fonts/` گذاشته می‌شود. **از گوگل‌فونت خوانده نمی‌شود** — نه از داخلِ ایران قابلِ اتکاست و نه از سرور.

هیچ چیزِ دیگری لازم نیست: نه دیتابیسِ جدا، نه Redis، نه Docker روی این کامپیوتر.
