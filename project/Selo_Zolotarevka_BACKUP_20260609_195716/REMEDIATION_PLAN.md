# REMEDIATION_PLAN.md

## Priority 0 (before scaling traffic)

1. Fix capability mapping to enforce least privilege
- Change CPT registration to explicit `capabilities` per post type (or coherent shared map) and align role grants exactly to those caps.
- Add verification matrix test: each role vs CRUD action per CPT.
- Success criteria: unauthorized role cannot edit/publish outside its domain CPTs.

2. Add anti-abuse controls for `zolo_submit_news`
- Add rate limiting (IP + UA + short burst window).
- Add honeypot field and optional CAPTCHA.
- Success criteria: automated spam throughput materially reduced; flood attempts throttled.

## Priority 1

3. Add request size and basic content constraints
- Enforce max title/content length server-side before `wp_insert_post`.
- Reject oversized payloads with user-safe generic error.

4. Replace raw backend errors with generic response
- Keep detailed error in server logs; return user-safe message only.

## Priority 2

5. Make moderation defaults idempotent and admin-respecting
- Apply defaults on activation/provisioning path only, not every `init`.

6. REST hardening hygiene
- Keep published-only return, but add cache headers/rate controls as needed.
- Document intended public API contract (fields, limits, purpose).

## Verification Checklist
- Unit/integration checks for nonce, rate-limit, and size limits.
- Role permission tests for each CPT and action.
- Negative tests for cross-domain role edits.
- Manual smoke for approved happy path form submission.
