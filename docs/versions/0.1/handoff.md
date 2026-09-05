# Handoff — build version 0.1

> You are starting fresh and cannot ask anyone anything. Everything you need is written down. Read this page, then `docs/versions/0.1/checklist.md`, then `docs/living/architecture.md`. The business documents (`prd.md`, `data-model.md`, `ux.md`, `test-scenarios.md`) are the source of truth; `docs/decisions.md` holds 52 numbered decisions with their reasons, and the code comments should cite them by number.

## What the product is

An Iranian online-clothing buyer clicks a link from an Instagram bio, lays out a garment they already own and are happy with, puts any bank-card-sized card on it for scale, and photographs it from above. Size measures the garment from that one photo and says which size of the shop's product to buy — as fit advice («مثلِ لباسِ خودت»), **never as a number**. The photo is deleted thirty minutes later; the anonymous measurements stay.

Three audiences: buyers (public, mobile only), sellers (a panel, mobile-first), and one operator (you/the founder).

## Layout and how it runs

Create exactly this; `run.sh` depends on it:

```
backend/    FastAPI app, SQLAlchemy models, Alembic migrations, tests
frontend/   React 19 + Vite 7
data/       app.db          (git-ignored)
uploads/    buyer photos    (git-ignored)
run.sh      build, migrate, start
```

One process serves the API under `/api` and the built React bundle at `/`, on **port 8000** (`APP_PORT` in `.env`, from `docs/profile.md`). No CORS, no API base URL. `bash run.sh` is the only way to start or restart it. **No containers on this machine** — that is `/deploy`'s business, and the build must not touch it.

The full file layout, every table, every endpoint and both algorithms are in **`architecture.md`** — do not re-derive them.

## The order to build in

Work the checklist top to bottom: **A** foundation → **B** accounts and the operator → **C** products and the size chart → **D** the measurement engine → **E** sizing → **F** the buyer's screens → **G** privacy and the deletion promise → **H** closing.

**Start at A1.** A and B unblock everything. Do not start D before C5 exists — you need a real size chart to compare against, and D8 (the tape-measure accuracy check) is the item most likely to send you back into D, so leave it room.

## Six things that are not obvious

1. **Length is never doubled.** `numbers_kind` (`circumference` | `width`) describes how the seller wrote their **circumference** figures. When it is `width`, you double circumference criteria only — a length is a length. Getting this wrong makes every answer confidently twice wrong, which `prd.md` calls the worst thing that can happen to trust. **Scenario 18 exists solely to catch it:** the same product entered both ways must give the identical answer.

2. **The blur check runs before card detection**, not after. A blurry photo also fails card detection, so whichever check runs first decides the message the buyer sees. Scenario 3 requires «عکس تار است», not «کارت پیدا نشد».

3. **The all-sizes-complete rule gates only the link's *first* activation** (decision 49). Once a link is live, adding an empty size must **not** take it down — that size is simply excluded from answers as if it did not exist, and the seller gets an amber warning. This looks like an inconsistency in the rule and is deliberate: a seller adding a size must never silently kill the link sitting in their Instagram bio.

4. **Switching circumference↔width clears the chart; it does not convert it** (decision 50). Automatic conversion is the tempting choice and the wrong one — if the seller picked wrong the first time, converting multiplies one error by another and nobody ever finds out.

5. **The thirty minutes runs from upload**, never extended by a view (decision 52), and it is the product's central promise. Three mechanisms enforce it: the scheduled job, a startup sweep for anything overdue while the process was down, and `410 Gone` computed live from `photo_delete_at`. Scenario 7 checks the actual file is gone from `uploads/`, not just that the page says so.

6. **`measure_rule` is nullable and that is intended.** `where_text` is prose for the seller; `measure_rule` is the key the engine dispatches on. An operator can add a criterion with no rule — it still appears in the chart for the seller to type into, it simply is not extracted from photos. Do not make it required.

Two smaller ones: the answer URL `/r/:viewCode` **is** the shareable link, so «کپیِ لینکِ این جواب» copies the current URL — the Instagram in-app browser has no address bar, which is why the button exists at all. And Vazirmatn is **self-hosted** from `frontend/src/fonts/`; do not load it from Google Fonts.

## Nothing external, nothing to wait for

Version 0.1 calls no outside service — no API key, no bot token, no SMS, no payment gateway (`dependencies.md`). Measurement is local OpenCV geometry. `SECRET_KEY` and the operator login are generated at `/setup-dev` into `secrets/secrets.local.md`; if they are somehow missing, generate them and write them there — **never into the chat and never into git**.

## Four open questions

`docs/versions/0.1/13-questions.md` holds four numbers that turn measurements into words: the fit bands, the no-size-fits threshold, the note thresholds, and confirmation of the `measure_rule` column. **Defaults are already written into `architecture.md`, so build with them and do not wait.** If the founder answers differently, they are constants in `sizing/compare.py` — a small edit, not a redesign.

## What "done" means

Every checklist item ticked or explicitly **BLOCKED** with a reason · the automated suite green from a clean database · the app running via `bash run.sh` on `http://localhost:8000` · and **all 28 scenarios in `docs/living/test-scenarios.md` walked by hand against that address**, each passing or written down with exactly what differed.

**Deployment is not part of done.** Do not write a Dockerfile, do not touch a server, do not attempt `/deploy`.
