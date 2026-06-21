# FT-157: Writing reviews to Google, Yelp, and Instagram

Status: Design only — no code shipped under this ticket. Designed jointly by
Gavin and Claude (via abigail), 2026-06-20.

## Problem statement

The ticket asks for a way to push Food Table reviews out to Google, Yelp, and
Instagram. The ticket itself has no description or acceptance criteria, so
this document first establishes what's actually possible on each platform,
then specifies the agreed design.

## Platform feasibility (hard constraints)

| Platform  | Public "create review" API for third parties? | Notes |
|-----------|------------------------------------------------|-------|
| Google    | No. Business Profile API is for owners managing their own listing, not third parties posting on a user's behalf. | `Restaurant.google_place_id` already exists and is usable for a "view/leave a review" deep link. |
| Yelp      | No. Yelp's API ToS explicitly prohibits automating/soliciting reviews. | No Yelp credentials or listing reference exist in this codebase, and none will be added (see below). |
| Instagram | No "review" concept at all — only posts/captions via the Graph API, which requires app review to publish. | Existing Instagram code is inbound-only (scrapes `og:description` for wishlist intake). |

**Conclusion:** none of the three support automated posting on a user's
behalf. The design below is a **share-assist** tool: it helps the user
compose content and hands them off to post it themselves.

## Design: unified compose-and-share page

One page serves all three platforms, since the source material (dishes,
notes, photos) is the same — only the final text/format differs per platform.

### Content model

- **`main_text`** — one shared body of text, written once, used as the base
  for every platform.
- **Per-platform "extra"** — short platform-exclusive additions appended to
  `main_text`:
  - *Instagram*: things like a location line (`📍 Pizza Cafe`), address, hashtags.
  - *Google* / *Yelp*: things like a blurb about service, wait time, etc. —
    relevant to a review site, not to a social caption.
- A platform "lens" (tab/toggle) switches which extra you're editing and
  shows a live preview of `main_text` + that platform's extra, rendered the
  way that platform would actually display it.

### Source panel

The page surfaces everything that already exists on the review so the user
isn't retyping it:
- Each `ReviewDish`: dish name, its own `notes`, its own photos (`Image` via
  `GenericRelation`) — individually selectable for inclusion/attachment.
- The `Review` itself: overall `notes`, restaurant-level photos — also
  selectable.

### AI rewrite assist

Scoped, not generative-by-default: the user highlights a span of text inside
`main_text` or a platform extra, clicks "Suggest rewrite," and gets one
alternative phrasing back for that span only (accept to replace the
selection, or discard). The AI never writes the review outright — it only
rewrites what's explicitly selected. Implemented as a small addition
alongside the existing `ai_service.py` pattern (settings-driven key, logged
latency, raises a typed error on failure).

### Per-platform action

- **Instagram**: compose caption = `main_text` + Instagram extra; selected
  photos are made available to attach; user posts via native share / copy.
- **Google**: compose text = `main_text` + Google extra; deep-link to the
  restaurant's existing Google listing via `Restaurant.google_place_id` so
  the user can paste their review in directly.
- **Yelp**: compose text = `main_text` + Yelp extra; copy-only. No stored
  Yelp listing reference and no deep link — the user finds the restaurant on
  Yelp themselves. (Decided explicitly: not worth adding a `Restaurant`
  field or search-link fallback for this.)

### Draft persistence

Schemaless — no new model, no migration. Stored under a conventional key in
the existing `Review.metadata` JSONField, e.g.:

```json
{
  "share_draft": {
    "main_text": "...",
    "platforms": {
      "instagram": {"extra_text": "...", "image_ids": [12, 45]},
      "google": {"extra_text": "...", "image_ids": []},
      "yelp": {"extra_text": "...", "image_ids": []}
    },
    "updated_at": "2026-06-20T12:00:00Z"
  }
}
```

Autosaved (debounced) as the user edits, so navigating away mid-draft doesn't
lose work.

## Explicitly out of scope

- Automated/unattended posting to any platform.
- Any new model/migration for tracking share state — deliberately schemaless
  via `Review.metadata`.
- A Yelp listing reference field or Yelp deep link — manual lookup is fine.

## Follow-on implementation tickets to file

1. Compose-and-share page: source panel (dish/restaurant notes + photo
   picker), shared `main_text` box, per-platform lens tabs with extra-text
   boxes and live preview, autosaved draft in `Review.metadata`.
2. AI rewrite-suggestion endpoint + UI: selection-scoped "Suggest rewrite"
   button, accept/discard.
3. Instagram action: caption + selected photos handoff (native share or copy).
4. Google action: composed text copy + deep link via `google_place_id`.
5. Yelp action: composed text copy (no deep link).

These can be built and shipped independently of each other.
