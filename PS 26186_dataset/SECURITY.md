# Backend Security Configuration & Architecture (Phase 17)

## Overview
This document details the security posture and configuration for the **ManoBal: AI-Based Predictive Personnel Stress and Welfare Monitoring System** backend.

> **Prototype Disclaimer:**
> This system is an SIH prototype utilizing a synthetically augmented dataset for research demonstration and operational feasibility testing. It does not process live classified defense telemetry. The security controls documented here represent Phase 17 hardening (removing hardcoded secrets, securing CORS, protecting inference endpoints, and enforcing RBAC). Further enterprise-grade deployment hardening (WAF, HSM, rate-limiting, network segmentation) is deferred to future operational phases.

---

## 1. Environment Configuration & Secrets Management

The backend enforces strict environment-driven configuration. No secret fallbacks exist in the source code.

### Required Environment Variables

| Variable | Required? | Default / Fallback | Description |
| :--- | :---: | :--- | :--- |
| `SECRET_KEY` (or `JWT_SECRET`) | **YES** | *None (raises RuntimeError)* | Cryptographic signing key for JWT access tokens. Must be a long, high-entropy secret string. |
| `DATABASE_URL` | No | `sqlite:///./personnel_welfare.db` | SQLAlchemy connection string (PostgreSQL in production; SQLite local fallback). |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000,http://localhost:3001,http://localhost:3002` | Comma-delimited list of trusted frontend origins for CORS preflight. |
| `ALGORITHM` | No | `HS256` | Symmetric signature algorithm for JWT generation and verification. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` (24 hours) | Token validity lifespan before re-authentication is required. |
| `LOG_LEVEL` | No | `INFO` | Standardized application logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

### Safe Failure on Missing Secret
If neither `SECRET_KEY` nor `JWT_SECRET` is present in the environment or `.env` file, `core.config.Settings` immediately raises:
```python
RuntimeError("JWT secret environment variable is required. Please set 'SECRET_KEY' or 'JWT_SECRET' in your environment or .env file.")
```
This guarantees the service will never boot with default or insecure cryptographic keys.

---

## 2. Cross-Origin Resource Sharing (CORS)

### Vulnerability Remediated
Previous iterations utilized `allow_origins=["*"]` with `allow_credentials=True`, which is rejected by standard web security specifications and allows arbitrary cross-origin request forgery.

### Current Implementation
- `CORSMiddleware` in `api/main.py` is configured with `settings.ALLOWED_ORIGINS`.
- Wildcard `*` has been eliminated.
- Explicit development origins permitted by default:
  - `http://localhost:3000` / `http://127.0.0.1:3000` (Commander Dashboard)
  - `http://localhost:3001` / `http://127.0.0.1:3001` (Jawan Mobile Web App)
  - `http://localhost:3002` / `http://127.0.0.1:3002` (Alternative local port)
- Explicit allowed HTTP methods: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`.
- Arbitrary untrusted origins (e.g., `http://malicious-site.com`) are rejected during preflight.

---

## 3. Endpoint Authentication & Protection

### `/api/predict` Hardening
- Previously accessible without credentials.
- Now protected using the `get_current_user` FastAPI dependency.
- Unauthenticated requests are rejected with `HTTP 401 Unauthorized` (`WWW-Authenticate: Bearer`).
- Authenticated requests must pass a valid Bearer token in the `Authorization` header.
- Token validation verifies signature, expiry (`exp`), and subject (`sub`) against active database accounts.

---

## 4. Role-Based Access Control (RBAC) Policy

The system strictly enforces the four backend roles defined in Phase 14-16:

| Role | Access Scope | Protected Endpoints |
| :--- | :--- | :--- |
| `admin` | Full administrative access | System registry, user provisioning, all personnel records, telemetry, dashboard, recommendations |
| `officer` | Operational command | Unit dashboard, stress aggregates, high-risk rosters, personnel creation/update, assessment triggers |
| `welfare` | Welfare counseling | Unit dashboard, high-risk rosters, review/patch welfare recommendation status (`pending`, `acknowledged`, `completed`, `dismissed`) |
| `personnel` | Jawan self-service | **Strictly bounded to self**: individual profile (`GET /api/personnel/{id}` where `id == user.personnel_id`), personal assessments, check-ins. Access to other personnel or dashboard summaries returns `HTTP 403 Forbidden`. |

---

## 5. Known Prototype Limitations & Future Enhancements

1. **Token Storage**: Prototype frontends currently store the Bearer JWT in browser `localStorage`. Production deployments should evaluate `HttpOnly`, `SameSite=Strict`, `Secure` cookies.
2. **Database Engine**: Local testing uses SQLite (`personnel_welfare.db`) when local PostgreSQL is not provisioned. Production hosting will connect to a hardened PostgreSQL cluster.
3. **Transport Security**: Local communications use HTTP over localhost. Production requires TLS 1.3 termination via reverse proxy (Nginx / Caddy / Cloudflare).
4. **Rate Limiting**: Request rate limiting (e.g., Redis-backed slowapi) is deferred to future operational deployment.
