# Build checklist — version 0.1

> Ordered. Each item: `id — what it is · done when: <proof, and which scenario it satisfies> · after: <ids>`
> Tick an item only when its "done when" is actually true. If something cannot be finished, mark it **BLOCKED** with one line saying why — never silently skip it.
> Scenario numbers refer to `docs/living/test-scenarios.md` (28 scenarios). Every one is covered below.

## A — foundation

- [ ] A1 — project skeleton per `architecture.md` (backend/, frontend/, data/, uploads/), `.env` from `.env.example` with `APP_PORT=8000` · done when: the tree exists and `.env` has a generated `SECRET_KEY` · after: —
- [ ] A2 — FastAPI app factory, settings from `.env`, async SQLAlchemy engine over `data/app.db`, `/api/health` · done when: `GET /api/health` returns ok · after: A1
- [ ] A3 — Alembic wired, first migration creates every table in `architecture.md` · done when: `alembic upgrade head` builds the schema from empty · after: A2
- [ ] A4 — seed migration: garment types بالاتنه/پایین‌تنه and the twelve criteria with `is_main`, `kind`, `where_text`, `measure_rule`, `sort_order` · done when: a fresh database has 2 types and 12 criteria · after: A3
- [ ] A5 — `Storage` interface + `LocalStorage` under `UPLOADS_DIR`, opaque keys · done when: unit test round-trips save/open/delete · after: A2
- [ ] A6 — `core/codes.py` unguessable codes, `core/digits.py` Persian↔Latin digits · done when: unit tests — codes are non-sequential and ۱۲۳ parses to 123 · after: A2
- [ ] A7 — React + Vite scaffold, RTL, self-hosted Vazirmatn, theme tokens from `ux.md` (white base, calm dark blue accent, amber warning, soft corners) · done when: `npm run build` emits static files and FastAPI serves them at `/` · after: A2
- [ ] A8 — `run.sh` end to end: build, migrate, start on `APP_PORT`, detached, `run.log` · done when: `bash run.sh` twice in a row restarts cleanly and the page loads at `http://localhost:8000` · after: A7

## B — accounts, shops, the operator

- [ ] B1 — account + shop models, bcrypt hashing, signed session cookie · done when: unit tests cover hash/verify and cookie sign/verify · after: A3
- [ ] B2 — login / logout / `GET /api/me`; one identical error for wrong username and wrong password · done when: **scenario 10** · after: B1
- [ ] B3 — صفحهٔ ورود, and the panel top bar with shop name and «خروج» · done when: **scenarios 10, 17** · after: B2, A7
- [ ] B4 — operator: فهرستِ فروشگاه‌ها, create shop + account in one transaction, generated password shown once in clear · done when: **scenarios 22, 23** · after: B2
- [ ] B5 — operator: deactivate a shop (shop + account together) · done when: the shop's links stop answering · after: B4
- [ ] B6 — impersonation: `POST /admin/shops/{id}/impersonate`, `acting_as_shop_id` in the session, banner + way back; a seller session can never set it · done when: **scenario 24**, plus a test that a seller cannot impersonate · after: B4
- [ ] B7 — operator: صفحهٔ معیارهای اندازه, add a criterion, duplicate name per garment type rejected · done when: **scenario 25** · after: B4

## C — products and the size chart

- [ ] C1 — product model + CRUD, `link_code` on create, `numbers_kind` pre-filled from the shop's last choice · done when: **scenario 11** · after: B2
- [ ] C2 — فهرستِ محصول‌ها with name, type, size count, link state; empty state · done when: the list matches `UI/` and the empty state appears on a new shop · after: C1
- [ ] C3 — صفحهٔ محصول: name, garment type, the prominent circumference-or-width choice with its illustration, optional shop URL, optional photo · done when: **scenario 11** · after: C1
- [ ] C4 — sizes: add, delete (asking first when the size has past requests), order = insertion order · done when: **scenario 21** · after: C1
- [ ] C5 — صفحهٔ جدولِ سایز — mobile: one expanding card per size; desktop: the full grid; main criteria first and marked; `where_text` beside each; zero and negative rejected; Persian and Latin digits both accepted · done when: **scenario 13** · after: C4, A6
- [ ] C6 — completeness + link activation: link goes live only when every size has both main criteria · done when: **scenario 12** · after: C5
- [ ] C7 — **an incomplete size never takes a live link down** — it is excluded from answers instead, and the seller sees the amber warning (decision 49) · done when: **scenario 19** · after: C6
- [ ] C8 — guarded `numbers_kind` switch: locked once the chart has values; explicit confirmation; **clears every measurement**; no automatic conversion (decision 50) · done when: **scenario 20** · after: C5
- [ ] C9 — صفحهٔ لینک و نصب: link + copy, site snippet + copy, buyer preview; incomplete state names the two criteria and counts the unfinished sizes · done when: **scenarios 12, 14** · after: C6
- [ ] C10 — deactivate a product from the bottom of صفحهٔ محصول, with confirmation saying the link sleeps and past data stays · done when: **scenario 16** · after: C3

## D — the measurement engine

- [ ] D1 — image ingest: EXIF rotation, HEIC, re-encode, 10 MB cap, downscale to 2000 px · done when: an iPhone HEIC and a rotated JPEG both come out upright · after: A5
- [ ] D2 — blur check **before** card detection, so a blurry photo says «عکس تار است» and not «کارت پیدا نشد» · done when: **scenario 3** · after: D1
- [ ] D3 — card detection: 4-gons scored on the 1.5858 ratio, area and solidity · done when: **scenario 2** — no card gives `card_not_found`, never a guess · after: D2
- [ ] D4 — rectify: homography from the card to 10 px/mm, warp the frame · done when: a deliberately tilted photo of a known rectangle measures within 0.5 cm · after: D3
- [ ] D5 — garment segmentation; reject `garment_cropped` when the mask runs off the frame · done when: a half-in-frame garment is rejected with that reason · after: D4
- [ ] D6 — the twelve `measure_rule` implementations, px→cm, horizontal spans doubled for `circumference` criteria only · done when: unit tests on fixture masks hit each rule within 0.5 cm · after: D5
- [ ] D7 — pipeline orchestration returning values-or-reason, run under `asyncio.to_thread` · done when: two uploads at once do not block each other · after: D6
- [ ] D8 — **accuracy check against a real photo**: photograph a garment measured by hand with a tape, compare · done when: both main criteria land within 0.5 cm of the tape · after: D7

## E — sizing and the answer

- [ ] E1 — normalise the chart to circumference; **length is never doubled**, whatever `numbers_kind` says · done when: **scenario 18** — the same product entered as circumference and as half-widths answers identically — plus a unit test at the normalise level · after: C5
- [ ] E2 — fit bands, recommendation by smallest `|d_circ|`, larger on a tie · done when: unit tests at every band boundary · after: E1, D6
- [ ] E3 — no-size-fits detection and the honest message with the nearest size · done when: **scenario 5** · after: E2
- [ ] E4 — notes: the mandatory length line above, separate from and outside the two-line secondary cap · done when: **scenario 4** — the length line is present and distinct · after: E2
- [ ] E5 — **the answer must not contain a raw measurement anywhere**, including the API payload · done when: **scenario 1**, plus a test asserting no numeric measurement in the response · after: E2

## F — the buyer's four screens

- [ ] F1 — صفحهٔ آغاز, two layouts (with and without a product photo — decision 41), inactive-product state · done when: **scenarios 1, 8** · after: C1, A7
- [ ] F2 — صفحهٔ راهنمای عکس with the line illustration; camera or gallery, gallery always available · done when: **scenario 1** inside the Instagram in-app browser · after: F1
- [ ] F3 — صفحهٔ در حالِ بررسی plus the took-too-long state with retry · done when: **scenario 1** · after: F2, D7
- [ ] F4 — صفحهٔ جواب: recommendation, every complete size with its fit word, notes, «برگرد و خرید کن» **only when the seller gave a URL** (decision 44) · done when: **scenarios 1, 4, 5, 19** · after: E5
- [ ] F5 — «کپیِ لینکِ این جواب» + «تا نیم‌ساعت با این لینک برمی‌گردی» (decision 45) · done when: **scenario 6** · after: F4
- [ ] F6 — صفحهٔ عکسِ ردشده: the exact reason, the guide illustration again, retry; helpful not blaming · done when: **scenarios 2, 3** · after: F3
- [ ] F7 — صفحهٔ جوابِ منقضی‌شده on `410` · done when: **scenario 7** · after: F4

## G — privacy, requests, the promise

- [ ] G1 — `jobs` table + asyncio poller, 30 s tick · done when: a job with a past `run_at` runs within a tick · after: A3
- [ ] G2 — `delete_photo` scheduled at **upload** time + 30 min, never extended by a view (decision 52) · done when: **scenario 7** — the file is gone from `uploads/` · after: G1, D1
- [ ] G3 — startup sweep and the belt-and-braces pass over `photo_delete_at` · done when: the app is stopped across a deletion time, restarted, and the file goes immediately · after: G2
- [ ] G4 — `410 Gone` computed from `photo_delete_at`, independent of the sweep · done when: **scenario 7** · after: G2
- [ ] G5 — فهرستِ درخواست‌ها: time order, product, hour, size or rejection reason, two summary lines, empty state · done when: **scenario 15** · after: C1
- [ ] G6 — **no endpoint anywhere returns a buyer photo, and no table holds anything identifying a buyer** · done when: **scenario 27**, plus a route audit · after: G5
- [ ] G7 — inactive product or shop 404s the link; a tampered code 404s and never reaches another shop · done when: **scenarios 8, 9** · after: C10, B5

## H — closing 0.1

- [ ] H1 — upload limits and the per-IP throttle on `/measure` · done when: an oversized file and a flood are both refused politely · after: D7
- [ ] H2 — automated test suite green: unit (digits, codes, normalise, bands, rules) and API (auth, impersonation, activation, expiry) · done when: the whole suite passes from a clean database · after: all of A–G
- [ ] H3 — **walk all 28 scenarios by hand against `http://localhost:8000`** and record the result · done when: every scenario passes or is written down with exactly what differed · after: H2
- [ ] H4 — end-to-end from an empty database: operator → seller → buyer → request visible · done when: **scenario 26** with no database poking · after: H3
- [ ] H5 — the two-minute walk with someone who has never seen it · done when: **scenario 28** — under two minutes, no questions asked · after: H4

> **Deployment is not on this list.** `/deploy` is a separate phase; the build must not attempt it.
