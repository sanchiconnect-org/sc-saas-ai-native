# SAN-2109: tenants-admin dev build fails at composer install (ext-gmp)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-2109
- **Repo:** sanchiconnect-saas-tenants-admin (`ai_native_setup`)
- **Classification:** ENV_ERROR (a third-party dependency, not our code)
- **Related:** SAN-2106 (FT-007). Its push was the first dev build after the bump, so it hit this failure first.

## Problem

The Jenkins dev build of tenants-admin fails at `RUN composer install --no-interaction --optimize-autoloader`:

```
sendgrid/sendgrid 8.1.11 requires ext-gmp * -> it is missing from your system.
starkbank/ecdsa 2.2.1 requires ext-gmp * -> it is missing from your system.
```

## Root cause

Dependabot PR #51 (commit `ff1de1e`, 2026-10-27, "deps: bump the minor-and-patch group with 9 updates") bumped `sendgrid/sendgrid` from 8.0.1 to 8.1.11. That is a minor bump of sendgrid, but it pulls `starkbank/ecdsa` from 0.0.5 to 2.2.1, a major version change. Dependabot's "no majors" rule only applies to direct dependencies, so it didn't stop this. Both new versions require `ext-gmp`. The Docker image builds bcmath, exif, gd, opcache, pcntl, pdo_mysql, sodium and zip, but not gmp.

CI didn't catch it because the CI runner's PHP has gmp.

No tenants-admin PHP code uses SendGrid. sc-saas-admin is not affected: it is still on sendgrid 8.0.1 and ecdsa 0.0.5.

## Fix

- `composer.json`: `sendgrid/sendgrid` changed from `^8.0` to `~8.0.1`.
- `composer.lock`: relocked with `composer update sendgrid/sendgrid --with-dependencies`. Only three packages changed:
  - sendgrid/sendgrid 8.1.11 → 8.0.1
  - sendgrid/php-http-client 4.1.3 → 3.14.4
  - starkbank/ecdsa 2.2.1 → 0.0.5
- `.github/dependabot.yml`: ignore `sendgrid/sendgrid >=8.1.0` and `starkbank/ecdsa >=1.0.0` until the image adds gmp.

Alternative not taken: add `gmp` to the Docker image. That Dockerfile lives in the Jenkins setup, not this repo. It is the right move if SendGrid 8.1+ is ever needed; then drop the pin and the ignore.

## Verification

- `ext-gmp` requirements in `composer.lock`: 2 before, 0 after.
- Every `ext-*` the new lock requires is either built into php:8.1 or one of the image's `docker-php-ext-*` extensions.
- `composer validate`: valid. `composer install --dry-run`: resolves.
- `composer gates`: all 8 gates exit 0.
- Not reproduced in Docker locally: no Docker daemon, and local PHP has gmp compiled in. The next Jenkins dev build is the real check.

## Commit

`d6937a9` on `ai_native_setup` (sanchiconnect-saas-tenants-admin), pushed 2026-10-27.
