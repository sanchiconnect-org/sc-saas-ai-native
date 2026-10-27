# SAN-2057 — "Upload a file" dialog shows only images, but only documents are accepted

- **Linear:** [SAN-2057](https://linear.app/sanchiconnect/issue/SAN-2057) (Repo: Frontend). Bug, Medium, assignee Vishali.
- **Classification:** CODE_ERROR.
- **Branch:** `ai_native_setup_vishali`. Commit: `e7a1cceed`.
- **Status:** Done in Linear (2026-10-27, closed at the request of the assignee). Pushed to `ai_native_setup_vishali`; not yet merged into `ai_native_setup`.

## Problem

In chat, the attachment button opens "Upload a file", which says *Accepted formats: ppt, pptx, doc, docx, pdf*. Clicking **Upload** opens the OS file dialog with only images listed. The modal is shared, so the same problem appears in:
- tickets;
- IP requests;
- community-feed posts.

## Root cause

`FeedFormFileSelectModalComponent` contradicted itself from the start (`070a92805`, "added file select modal"):

- The hidden file input had `accept=".png, .jpg, .jpeg"`. The document list was left commented out next to it.
- `fileTypeValidation()` allows only pdf, doc, docx, rtf, ppt and pptx.

So the dialog offered only images, and an image picked from it was then rejected with "Allowded File type are ppt, pptx". Only drag-and-drop into the box could upload a document.

## Fix (sc-saas-frontend)

- `feed-form-file-select-modal.component.ts`:
  - New `acceptedExtensions = '.pdf, .doc, .docx, .rtf, .ppt, .pptx'`, kept in step with `allowdedMimeTypes`.
  - The error message now reads "Allowed file types are ppt, pptx, doc, docx, pdf".
- `feed-form-file-select-modal.component.html`: `[accept]="acceptedExtensions"`. The old comment is removed.
- `feed-form-file-select-modal.component.spec.ts`: two specs.
  - The dialog offers exactly the document extensions.
  - A pdf passes `fileTypeValidation()`, and a png is rejected with the new message.

Other upload components have their own copies of the misspelled "Allowded…" message. They don't use this modal and were left alone.

## Verification

- `bash scripts/gates.sh build unit-tests`: build exit 0, unit-tests 1330/1330 SUCCESS.
- Not done: no manual browser check of the file dialog.

## Open

- Product question: today chat file attachments do not accept images; images go through the separate "Upload image" button. Allowing them here would be a separate change.
