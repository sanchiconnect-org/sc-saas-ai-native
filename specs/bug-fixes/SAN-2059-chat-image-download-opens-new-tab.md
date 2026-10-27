# SAN-2059 — Chat image viewer's Download opens a new tab instead of saving

- **Linear:** [SAN-2059](https://linear.app/sanchiconnect/issue/SAN-2059) (Repo: Frontend). Bug, Medium, assignee Vishali.
- **Classification:** CODE_ERROR.
- **Branch:** `ai_native_setup_vishali`. Commit: `45e9cca9f`.
- **Status:** Done in Linear (2026-10-27, closed at the request of the assignee). Pushed to `ai_native_setup_vishali`; not yet merged into `ai_native_setup`.

## Problem

In chat, clicking an image opens the full-screen viewer (lightGallery 2.6.1). Its **Download** (⬇) button does not save the file. It opens the image in a new tab.

## Root cause

1. **The button ignores `download` for another domain.** lightGallery's download button is `<a download target="_blank" href="…">`, and its `href` is the item's URL. Chat images are S3 signed URLs (`s3.ap-south-1.amazonaws.com/sanchi-saas-dev/…`), which are cross-origin. Browsers ignore `download` on cross-origin links, so the link just opens in a new tab.
2. **The cache defeated the first fix.** The first fix fetched the image as a blob and saved that, but it still opened a tab.
   - The chat `<img>` had already loaded the same URL with no `Origin` header.
   - S3 answers such a request without `Access-Control-Allow-Origin` and without `Vary: Origin`. With an `Origin` header it does send both (checked with curl; the bucket's CORS rule is `*`, GET/HEAD).
   - The browser reused the cached, CORS-less response for `fetch()`. The CORS check failed and the code fell back to a new tab.

## Fix (sc-saas-frontend)

- New `src/app/shared/utils/lightgallery-download.util.ts`:
  - `enableLightGalleryBlobDownload(detail)` is used as the gallery's `[onInit]`. lightGallery builds its toolbar before firing `lgInit`, so the button already exists. The function takes over the button's click: it prevents the navigation and calls `downloadUrlAsFile(button.href, button.download || fileNameFromUrl(href))`.
  - `downloadUrlAsFile` runs `fetch(url, { cache: 'no-store' })`, then saves the blob through a temporary `<a download>`. On any failure it opens the URL in a new tab, which was the old behaviour.
  - `fileNameFromUrl` returns the last path segment without the query string, or `'download'`.
- `sent-message` / `received-message` (`.ts` + `.html`):
  - `onGalleryInit = enableLightGalleryBlobDownload` and `[onInit]="onGalleryInit"`.
  - `[attr.data-download]="message.metadata?.fileName"`, so the saved file has its original upload name, not the S3 key.
- `lightgallery-download.util.spec.ts`: 5 specs.
  - File-name parsing and its fallback.
  - The blob is saved under the given name.
  - A failed fetch opens a new tab.
  - A button click is prevented and fetched with `no-store`.

## Verification

- `bash scripts/gates.sh build unit-tests`: build exit 0, unit-tests 1335/1335 SUCCESS.
- curl against the bucket:
  - no `Origin` → 403 with no CORS headers;
  - `Origin: http://localhost:4200` or `https://thub.sanchidev.in` → `Access-Control-Allow-Origin: *`.
- Not done: no real download tried in a browser, and no confirmation yet after the `no-store` change. To check after deploy:
  1. Open a chat image and click ⬇.
  2. The file should save under its original name, with no new tab.
  3. If a tab still opens, look in the console for a fetch or CORS error.

## Known gaps

- Other lightGallery uses (community feed, etc.) still have the old new-tab behaviour. They can adopt the same `[onInit]` helper if needed.
- Production and staging buckets were not checked. If a bucket has no CORS rule, the download falls back to a new tab.
