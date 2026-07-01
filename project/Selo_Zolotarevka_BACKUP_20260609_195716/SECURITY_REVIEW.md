# SECURITY_REVIEW.md

## Scope
- Backend: `wordpress/mu-plugins/zolotarevka-backend.php`
- Frontend integration: `wordpress/themes/zolotarevka-mvp/*`
- Focus: roles/capabilities, public form submission flow, moderation defaults, REST exposure, input/output handling.

## Method
- Static code review of implemented P0 WordPress code paths.
- Threat modeling by entry points:
  - Public `admin-post.php` submission (`zolo_submit_news`).
  - Public REST route `zolo/v1/content/{type}`.
  - Theme rendering of dynamic links and form glue.

## Findings Summary
- Critical: 0
- High: 0
- Medium: 3
- Low: 3

## Threat Review by Area

### Roles and permissions
- CPTs are registered with `capability_type => 'post'` and `map_meta_cap => true`.
- Custom roles add custom caps like `edit_school_news`, `publish_sports_match`, but these caps are not connected to CPT capability mapping because CPTs use default `post` capabilities.
- Security impact: least-privilege model is not actually enforced as designed; access boundaries between role domains are weak/inaccurate.

### Validation and moderation
- Form submission uses nonce verification and sanitization (`sanitize_text_field`, `wp_kses_post`) and stores to `pending` status.
- Comments moderation defaults are enabled globally.
- Gap: no anti-automation controls (captcha/rate-limit/honeypot), so spam/flood remains practical.

### Injection, XSS, CSRF
- CSRF: covered for submission route by nonce.
- Input handling: title/content sanitized before persistence.
- Output in theme for URLs and labels uses `esc_url`/`esc_html` in relevant dynamic points.
- No direct SQL queries or raw echo of unsanitized request payload observed in reviewed code.

### Data exposure
- REST route is public (`permission_callback => __return_true`) and returns published content only.
- This is acceptable for public site behavior but requires clear intent and bounded fields. Current payload excludes sensitive user metadata.

## Residual Risks
- Role model mismatch may allow broader editorial actions than intended in policy docs.
- Form endpoint can be abused for content spam/queue flooding.
- Error path currently exposes raw WP error message to user response.
