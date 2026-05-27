# TrocLégumes — Roadmap

Each phase ends with something runnable and testable.

---

## Phase 0 — Project Scaffold
- Django project + app structure
- PostgreSQL + Docker Compose (dev environment)
- Base template with HTMX + Tailwind (or Bootstrap)
- Django auth wired up (login/logout/register)
- Django admin enabled

## Phase 1 — Models & Admin
- All 13 models created and migrated
- All models registered in Django admin
- Seed fixtures for dev (a few farms, products, a current week)

> From this point the admin panel is a working back-office.

## Phase 2 — Farms & Social Graph
- Farm profile pages (public view + edit)
- User → Farm link (registration flow)
- Follow / unfollow
- Farm map (lat/lng, Leaflet.js or simple static map) — displayed in `/fermes/`, not on the dashboard

## Phase 3 — Weekly Listings & Marketplace
- `farm_products` CRUD
- Current week management (admin creates week, one active at a time)
- `listings` CRUD for current week
- Marketplace — Offres view (followed farms first, dynamic stock display)

## Phase 4 — Order Flow (Supply Side)
- Place order (stock check, creates `order` + `order_items`)
- Seller email with signed Accept/Decline URLs
- Incoming Orders view (same actions, no login required via URL)
- Accept → mutual introduction email to both parties
- Decline → buyer notified
- Confirm → two `tab_entries` created
- Cancel (either party) → stock freed

> This is the core loop. Everything before this is setup; everything after is extension.

## Phase 5 — Wanted Listings (Demand Side)
- Wanted listing CRUD
- Notification email to matching followed farms on post
- Wanted response form (seller side)
- Buyer reviews responses, accepts one → mutual intro email, others auto-declined
- Mark as fulfilled (manual)

## Phase 6 — Tab & Settlements
- My Tab view — bilateral balance computed on the fly per farm pair
- Settlement declaration form (type, amount, description)
- Counterpart confirms → two `tab_entries` created
- Relevé de compte PDF export (period picker, list of orders between two farms)

## Phase 7 — Async & Notifications
- Celery + Redis (or `django-q`) wired up
- All emails moved to async tasks
- Weekly reset cron — reminder to farms with no active listing

## Phase 8 — Polish & Deployment
- Mobile-responsive layouts for Marketplace, Incoming Orders, My Tab
- Admin dashboard (user management, ledger overview)
- Optional: invitation system
- Docker production config + VPS deployment
- Optional later: PWA manifest + service worker, Capacitor shell

---

## Critical Path

Phase 0 → 1 → 3 → 4 gets to a working exchange loop.
Phases 2, 5, 6 fill in the social and financial layers.
Phases 7–8 are hardening.
