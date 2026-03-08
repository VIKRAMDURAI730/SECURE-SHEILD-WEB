# Web Security — Attacks & Mitigations

**College Project Example — Secure Shield Web**

This document explains how this e-commerce application demonstrates **known** and **unknown** web attacks, and how they are **fixed** or **mitigated**. Use it as a reference for your project report or presentation.

---

## Overview

| Attack Type | Status | Mitigation |
|-------------|--------|------------|
| SQL Injection | ✅ Blocked | Parameterized queries |
| XSS (Cross-Site Scripting) | ✅ Blocked | Output encoding, safe DOM APIs |
| CSRF (Cross-Site Request Forgery) | ✅ Mitigated | Bearer token auth (not cookies) |
| Password exposure | ✅ Protected | Secure hashing (Werkzeug) |
| Session hijacking | ✅ Reduced | Random tokens, HTTPS in production |
| Unknown/Zero-day | 🛡️ Defense in depth | Multiple layers, input validation |

---

## 1. SQL Injection (Known Attack)

### What it is
An attacker injects malicious SQL into input fields by concatenating user input into query strings. Example: `' OR 1=1 --` in login to bypass authentication.

### How it would be exploited

```sql
-- Vulnerable code (we do NOT use this):
query = "SELECT * FROM users WHERE email = '" + user_input + "'"
-- If user_input = "' OR 1=1 --", the query becomes:
-- SELECT * FROM users WHERE email = '' OR 1=1 --'  (always true!)
```

### How we fix it

- **Parameterized queries** — All user input is passed as parameters, not concatenated:
  ```python
  cur.execute('SELECT * FROM users WHERE email = ?', (email,))
  ```
- **No string concatenation** anywhere in SQL queries.

### Live demo
On the login page, click **"Try SQL injection test (blocked)"**. The payload `' OR 1=1 --` is blocked — login fails as expected.

---

## 2. XSS — Cross-Site Scripting (Known Attack)

### What it is
An attacker injects malicious JavaScript into the page so it runs in another user's browser. Example: `<script>alert('XSS')</script>` in a product name.

### How it would be exploited

```javascript
// Vulnerable code (we avoid this):
element.innerHTML = userData;  // If userData = "<script>stealCookies()</script>", it runs!
```

### How we fix it

- **Use `textContent`** instead of `innerHTML` when displaying user input (e.g. `Welcome, user.name`).
- **Escape HTML** when we must use `innerHTML` — convert `<`, `>`, `"`, `'` to safe entities.
- **Content Security Policy (CSP)** — Can be added in production to block inline scripts.

### Where we apply it
- User names: `textContent` on welcome message.
- Order data: Only safe values (order IDs, dates, totals) are rendered.
- Product names: Come from DB; if ever user-controlled, we would escape.

---

## 3. CSRF — Cross-Site Request Forgery (Known Attack)

### What it is
A malicious site tricks the user's browser into sending a request to our site (e.g. place an order) while the user is logged in.

### How we mitigate it

- **Bearer token in `Authorization` header** — We use `Authorization: Bearer <token>`, not cookies.
- **Same-origin policy** — Browsers block cross-origin requests from other sites to our API unless they explicitly include our token.
- **CORS** — We control which origins can call our API.

### Why we don't use cookies
Cookies are sent automatically with every request to our domain. If we used cookies, a malicious site could embed a form that POSTs to our API and the browser would send the cookie. With Bearer tokens, the malicious site cannot read our token (stored in JS), so it cannot forge the request.

---

## 4. Password Security (Known Attack)

### What we protect against
- **Plain-text storage** — If DB is stolen, attackers get passwords.
- **Weak hashing** — MD5/SHA1 can be cracked with rainbow tables.

### How we fix it

- **Werkzeug** `generate_password_hash` / `check_password_hash` — Uses industry-standard hashing (PBKDF2 by default).
- Passwords are never stored or logged in plain text.
- Minimum length: 4 characters (can be increased for production).

---

## 5. Unknown / Emerging Attacks (Defense in Depth)

### What we mean by "unknown"
Unknown attacks are zero-day exploits, new attack vectors, or techniques not yet widely documented. We cannot predict every attack, so we use **defense in depth** — multiple layers.

### Mitigations in this project

| Layer | Purpose |
|-------|---------|
| **Input validation** | Reject invalid data early (email format, length, etc.) |
| **Parameterized queries** | Prevents SQL injection even if attacker finds new payloads |
| **Output encoding** | Prevents XSS even if new injection points appear |
| **Token-based auth** | Reduces CSRF and session fixation risks |
| **Error handling** | Generic messages to users; avoid leaking stack traces or DB paths |
| **HTTPS** | In production, encrypts traffic; prevents man-in-the-middle |

### General principles
- **Never trust user input** — Validate and sanitize.
- **Least privilege** — DB user, file permissions, etc.
- **Fail securely** — On error, deny access rather than default to allow.

---

## 6. Quick Reference

### For your project report

1. **Attack** — Describe the attack (OWASP, CWE references).
2. **Vulnerable code** — Show what *would* be vulnerable (pseudo-code).
3. **Mitigation** — Show our actual code (parameterized query, `textContent`, etc.).
4. **Demo** — SQL injection demo on login page; explain what happens.

### Files to cite

- `app.py` — Parameterized queries, password hashing.
- `database.py` — Schema, no raw SQL with user input.
- `js/app.js` — API client, token handling.
- `index.html` — SQL injection demo, security explanations.

---

## 7. Summary

This project serves as an **example model** for a college security project:

- **Known attacks** (SQL injection, XSS, CSRF, password exposure) are clearly mitigated and documented.
- **Unknown attacks** are addressed through defense in depth and secure coding practices.
- **Live demos** (e.g. SQL injection test) show that mitigations work in practice.

Use this document as the foundation for your project documentation and presentation.
