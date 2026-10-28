---
id: SAN-2021
title: "createHlsJob getRandomValues is not a function: dev image resolved a Node-20-only AWS SDK onto Node 16"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2021
sentry: [SC-SAAS-BACKEND-5Z, SC-SAAS-BACKEND-5Y, SC-SAAS-BACKEND-5X]
repos: [backend]
related: []
commit: backend@238c53e7 (branch ai_native_setup_vishali, pushed)
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2021: AWS SDK caret ranges floated past Node 16 on the dev image

## Root cause
* There is one event each, all at 2026-10-23 06:44:27 on dev host `aea0ace17546`, runtime node v16.20.2:
  * **5Y:** `getRandomValues is not a function` in `createHlsJob()`.
  * **5Z:** the wrapped `InternalServerErrorException`, raised via `LearningManagementController.processVideoForHls`.
  * **5X:** the SDK's `NodeVersionSupportWarning`.
* Versions declared and installed:
  * `.nvmrc` is `16.20.2`, and CI runs `npm ci`.
  * `package.json` declared `"@aws-sdk/client-mediaconvert": "^3.131.0"`, and the lockfile pins 3.131.0, which works on Node 16.
* Why a newer SDK breaks:
  * `NodeVersionSupportWarning` only exists in very new SDK releases. The latest is `3.1156.0`, with `engines.node >=20`.
  * Those releases depend on `@smithy/core`, which does `require("node:crypto").getRandomValues`.
  * On Node 16 that is undefined, which is exactly this error when the SDK generates the `ClientRequestToken` for `CreateJobCommand` (`aws-mediaconvert.service.ts:177`).
* So the dev image did not install from the lockfile: it ran `npm install`, or copied only `package.json`. This is inferred, because the Jenkins/Docker config is outside the repo (`docs/DEPLOYMENT.md:320` already lists this as an open question).

## Fix
Pinned the three caret-ranged AWS SDK packages to the exact versions already in the lockfile, in both `package.json` and the lockfile root entry:

| Package | Before | After |
|---|---|---|
| `@aws-sdk/client-elastic-transcoder` | `^3.131.0` | `3.131.0` |
| `@aws-sdk/client-mediaconvert` | `^3.131.0` | `3.131.0` |
| `@aws-sdk/cloudfront-signer` | `^3.127.0` | `3.127.0` |

`@aws-sdk/client-sesv2` was already pinned (`3.600.0`). The resolved package entries in the lockfile do not change.

## Blast radius / existing-flow impact
Backend only. Nothing changes wherever `npm ci` is used, because these are the same versions. A non-`ci` install can no longer pull a Node-20-only SDK.

## Verification
* `npm ls @aws-sdk/client-mediaconvert @aws-sdk/client-elastic-transcoder @aws-sdk/cloudfront-signer` → 3.131.0 / 3.131.0 / 3.127.0, with no "invalid" markers.
* `npm run gates`: everything passed (the same run as SAN-2026).
* After deploy:
  * inside the container, `npm ls @aws-sdk/client-mediaconvert` should show 3.131.0;
  * `processVideoForHls` from the LMS admin on dev should return a jobId.

## Ops follow-ups
* The backend Docker/Jenkins build must run `npm ci` against the committed lockfile. Other caret-ranged dependencies can drift the same way.
* Long term: Node 16 has been EOL since 2023-09. Move backend and 3rdparty-webservices to Node 20/22 together, updating `.nvmrc`, the base image, `@types/node` and CI.

## Regression check
* I copied `package.json` and `package-lock.json` into a scratch folder and ran `npm install --package-lock-only`. The lockfile came out unchanged, so the two are in sync and `npm ci` installs exactly the same versions as before.
