# TrocLégumes — Project Brief

## Context

**TrocLégumes** is a web application for market gardeners and small farmers to exchange and sell produce directly with each other, outside of traditional distribution channels.

The project is initiated by a market gardener who is also a former developer. The initial user base is a small, known community of producers. The app is built to be simple, practical, and respectful of how farmers actually work — including their existing invoicing habits and preference for direct communication.

### What the app does

- Producers publish a **weekly listing** of products they have available, with quantities and prices
- Other producers can **browse and order** from those listings
- Producers can also post **wanted listings** when they are looking for something specific
- All exchanges are tracked in a **bilateral tab system** — each farm pair has a running balance
- Balances are settled periodically via **settlements** (monetary, labor exchange, or mutual write-off)
- The app generates **relevés de compte** (account statements) to support the seller's own invoicing, but never produces legal invoices itself
- **Logistics are handled by email** — the app sends a mutual introduction email with full contact details when an order is accepted; farmers sort out pickup/delivery between themselves

### Key design decisions

- **Python + PostgreSQL** stack (Django, HTMX, no JavaScript framework)
- Prices are set weekly; each product has a default price overridable per listing
- Stock is computed dynamically (no stored remaining quantity); pending orders reserve stock immediately
- Bilateral balances are computed from orders and settlements, never stored
- The app never produces legal invoices — only relevés de compte (account statements)
- Settlements cover any agreed amount (one invoice, several invoices, a full period) — no link to specific orders
- Three settlement types: monetary (cash/virement), labor exchange, mutual write-off
- Orders require seller acceptance; wanted listings require buyer acceptance of a seller response — both trigger the same mutual introduction email (Flow B)
- Follow/unfollow mechanism so each farm curates its marketplace view
- Open registration; optional invitation system for managed onboarding
- Farm map with lat/lng for geographic filtering

---

## 1. Suggested Features

### Core
- **Farm profiles** — each producer has an account linked to their farm
- **Weekly product board** — producers publish available products each week (name, quantity, unit, price)
- **Wanted listings** — farmers post what they are looking for this week; matching producers are notified
- **Marketplace view** — browse all current listings from other farms, filterable by category
- **Order/exchange workflow** — a buyer selects products → transaction is recorded
- **Tab system** — bilateral balances computed per farm pair (who owes whom and how much)
- **Transaction history** — full log of all exchanges per farm
- **Relevé de compte** — exportable PDF account statement per farm pair, to help producers issue their own invoices
- **Email-based logistics** — on acceptance, app sends a mutual introduction email to both parties with full contact details (email + phone); all logistics discussion happens directly between farmers outside the app
- **Follow / unfollow farms** — each farm curates a list of farms it follows; marketplace defaults to followed farms only, with an option to browse all

### Nice to have
- **Weekly reset reminder** — notification (email or in-app) prompting producers to update their listings
- **Product catalog** — reusable product definitions (tomatoes, zucchini…) to avoid re-typing
- **Seasonal calendar** — indicate typical availability periods per product
- **Admin dashboard** — manage users, resolve disputes, export ledger
- **Simple mobile-friendly UI** — farmers may use phones in the field

### The two exchange flows

The app has two symmetric flows. Understanding the symmetry is key to the codebase structure.

| Step | Supply flow | Demand flow |
|---|---|---|
| 1 — Initiate | Seller publishes a **listing** | Buyer posts a **wanted listing** |
| 2 — Respond | Buyer places an **order** | Seller submits a **wanted response** |
| 3 — Validate | **Seller** accepts or declines (email or app) | **Buyer** accepts or declines |
| 4 — Outcome | Mutual introduction email sent | Mutual introduction email sent |
| 5 — Logistics | Farmers arrange pickup/delivery by email | Farmers arrange pickup/delivery by email |
| 6 — Close | Seller confirms goods exchanged → tab entry | *(no tab entry until a formal order is created)* |

Both flows use the same introduction email mechanism and the same accept/decline pattern — only the roles are swapped.

### Non-obvious design choices

> **1. Bilateral balance is computed, not stored.**
> The balance between Farm A and Farm B is derived from `orders` and `settlements` on the fly. There is no stored balance field. This avoids synchronisation bugs and is always accurate. See the SQL note in the `tab_entries` section.

> **2. Signed URL token flow for Accept/Decline emails.**
> When a buyer places an order, the seller receives an email with [Accepter] and [Décliner] buttons. Each button is a one-time signed URL generated with `django.core.signing` (no token stored in DB, expiry enforced). Clicking it does not require the seller to log in. The same action is also available in the Incoming Orders view inside the app — both paths update the same order status.

---

## 2. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Backend | **Django** | Batteries included: ORM, admin panel, auth, forms — ideal for a solo Pythonista |
| Database | **PostgreSQL** | As requested; Django integrates natively |
| Frontend | **HTMX + Django Templates** | Interactive without a JS framework; keeps everything in Python |
| Task queue | **Celery + Redis** (or `django-q`) | Weekly reminders, async email sending |
| Email | **Django EmailMultiAlternatives** + SMTP | HTML emails with Accept/Decline buttons; `Reply-To` set to counterpart's address |
| Auth | Django built-in | Sufficient for this use case |
| Deployment | **Docker + VPS** (Hetzner/OVH) | Simple, low-cost, full control |

> Django's built-in `/admin` gives you a free back-office on day one — very useful early on.

---

## 3. Tables

### `farms`
```sql
farms (
  id,
  name,
  description,
  address,
  phone,
  logo,           -- path to image file
  latitude,       -- for map display
  longitude,      -- geocoded from address
  is_active,
  created_at,
  updated_at
)
```

### `users`
```sql
users (
  id,
  email,          -- login identifier
  first_name,
  last_name,
  phone,          -- direct mobile; included in mutual introduction email
  farm_id FK,     -- nullable (admin may have no farm)
  role,           -- producer | admin
  is_active,
  created_at,
  last_login
)
-- Password is managed by Django's auth system
```

### `crop_categories`
Top-level classification only (not farm-specific products).
Examples: Légumes, Fruits, Herbes aromatiques, Céréales, Légumineuses, Œufs & Laitiers, Produits transformés.
```sql
crop_categories (
  id,
  name,
  description,
  icon            -- optional, for UI display
)
```

### `farm_products`
Each farm creates and owns its own named products. This is intentional: farm-specific names, varieties and descriptions matter and there will be many.
```sql
farm_products (
  id,
  farm_id FK,
  crop_category_id FK,
  name,           -- e.g. "Tomates cerises cœur de bœuf"
  description,
  default_unit,   -- kg | g | litre | bouquet | botte | pièce
  default_price,  -- producer's usual price; overridable per listing
  photo,          -- path to image file
  is_active,
  created_at,
  updated_at
)
```

### `weeks`
Manages the weekly cycle explicitly rather than relying on raw dates scattered across listings.
```sql
weeks (
  id,
  start_date,     -- Monday
  end_date,       -- Sunday
  is_active,      -- only one active week at a time
  created_at
)
```

### `listings`
What a farm offers during a given week.
```sql
listings (
  id,
  farm_product_id FK,
  farm_id FK,       -- denormalized for easier querying
  week_id FK,
  quantity_available,   -- total stock declared by the farmer (editable mid-week)
  unit,             -- can override farm_product.default_unit
  price_per_unit,   -- defaults to farm_product.default_price, editable per week
  notes,            -- e.g. "récolte du mardi, très mûres"
  is_active,
  created_at,
  updated_at
)
```
> **Stock remaining** is never stored — it is computed:
> `quantity_available − SUM(order_items.quantity WHERE order.status IN ('pending', 'confirmed'))`
> Pending orders reserve stock immediately. Cancellations free it automatically.
> When remaining hits 0, the listing is marked « épuisé » and new orders are blocked.

### `orders`
One order groups items purchased from a single seller in one go.
```sql
orders (
  id,
  buyer_farm_id FK,
  seller_farm_id FK,  -- denormalized for easier querying
  status,             -- pending | accepted | confirmed | declined | cancelled
  buyer_notes,        -- message from buyer to seller
  seller_notes,       -- reason for decline, pickup instructions, etc.
  created_at,
  updated_at
)
```
> **Status flow:**
> `pending` (buyer placed) → `accepted` (seller agrees) → `confirmed` (goods exchanged, tab entries created) ← terminal state
> `pending` → `declined` (seller refuses, e.g. too far) → stock freed, buyer notified
> `accepted` | `pending` → `cancelled` (either party) → stock freed
> Financial settlement of the order is tracked separately via `settlements`, not via order status.

### `order_items`
Line items within an order (one order can cover multiple listings from the same seller).
```sql
order_items (
  id,
  order_id FK,
  listing_id FK,
  quantity,
  unit_price,     -- snapshot at time of order (price may change next week)
  total_price,    -- quantity × unit_price
  notes
)
```

### `tab_entries`
The financial ledger. Every monetary event creates entries here.
```sql
tab_entries (
  id,
  farm_id FK,
  order_id FK,          -- nullable (settlements and adjustments have no order)
  settlement_id FK,     -- nullable (set when entry_type = 'settlement')
  amount,               -- positive = credit, negative = debit
  balance_after,        -- global running balance for this farm
  entry_type,           -- order | settlement | adjustment
  description,          -- human-readable note
  created_at
)
```
> Two entries are created per confirmed order: one debit on the buyer, one credit on the seller. Confirmed settlements and manual adjustments also flow through here.

**Note on bilateral balances:** The balance between Farm A and Farm B is never stored — it is computed on the fly from `orders` and `settlements`. This avoids redundancy and is always accurate:
```sql
-- What Farm A owes Farm B (net)
SELECT
  SUM(oi.total_price) FILTER (WHERE o.buyer_farm_id = A AND o.seller_farm_id = B)
  - SUM(oi.total_price) FILTER (WHERE o.buyer_farm_id = B AND o.seller_farm_id = A)
  - SUM(s.amount) FILTER (WHERE s.farm_a_id = A AND s.farm_b_id = B AND s.status = 'confirmed')
  + SUM(s.amount) FILTER (WHERE s.farm_a_id = B AND s.farm_b_id = A AND s.status = 'confirmed')
FROM orders o JOIN order_items oi ... LEFT JOIN settlements s ...
```

### `settlements`
A clearing event that reduces the bilateral balance between two farms. No link to specific orders — what it covers is described in free text and supported by a relevé de compte PDF generated separately.
```sql
settlements (
  id,
  farm_a_id FK,       -- who proposes the settlement
  farm_b_id FK,       -- counterpart
  amount,             -- the € value being cleared (even if no money moves)
  type,               -- monetary | labor | mutual_writeoff
  method,             -- cash | virement (only when type = monetary)
  description,        -- e.g. "Facture janv. 2026 — commandes du 05/01 au 31/01"
                      --      "2 journées d'aide aux semis, accord du 15/06"
                      --      "On solde — accord mutuel"
  proposed_by FK,     -- user who initiated
  confirmed_by FK,    -- user who accepted (counterpart side)
  confirmed_at,
  status,             -- pending | confirmed | disputed
  created_at
)
```
> A confirmed settlement creates two `tab_entries` (debit farm_a, credit farm_b) regardless of type.
> The app generates a **relevé de compte** PDF separately — a list of all orders between the two farms for a chosen period — which the seller uses to draft their own invoice outside the app. The app never produces legal invoices.
>
> **Settlement types:**
> - `monetary` — cash or bank transfer; buyer declares it, seller confirms receipt
> - `labor` — no money moves; both agree on a € value for work done (e.g. harvest help)
> - `mutual_writeoff` — both agree to forgive the balance entirely or partially

### `wanted_listings`
The demand side of the marketplace. A farm posts what it is looking for this week.
```sql
wanted_listings (
  id,
  farm_id FK,             -- who is looking
  crop_category_id FK,    -- broad category filter (nullable)
  description,            -- free text: "cherche 10kg de courges butternut bio"
  quantity_wanted,        -- optional indicative quantity
  unit,                   -- optional
  week_id FK,
  is_fulfilled,           -- marked true when the farm has found what it needed
  is_active,
  created_at,
  updated_at
)
```
> When posted, farms that (1) follow the poster and (2) have a `farm_product` in the matching category are notified by email.
> Sellers respond with a `wanted_response` (quantity offered, notes). The **buyer reviews all responses and accepts one** — only then is the mutual introduction email sent. All other pending responses are auto-declined.

### `wanted_responses`
A seller's offer in response to a wanted listing. The buyer reviews all responses and accepts one.
```sql
wanted_responses (
  id,
  wanted_listing_id FK,
  responding_farm_id FK,
  quantity_offered,     -- seller adjusts if needed
  notes,
  status,               -- pending | accepted | declined
  created_at
)
```
> On seller response: buyer is notified by email. Multiple sellers can respond to the same wanted listing.
> When buyer **accepts** one response: mutual introduction email sent to both parties; `wanted_listing.is_fulfilled = true`; all other pending responses auto-declined.

### `farm_follows`
A farm follows another to see its listings in the marketplace by default.
```sql
farm_follows (
  id,
  follower_farm_id FK,
  followed_farm_id FK,
  created_at,
  UNIQUE (follower_farm_id, followed_farm_id)
)
```

### `invitations` *(optional, for managed onboarding)*
```sql
invitations (
  id,
  email,
  invited_by FK,  -- user who sent the invite
  token,          -- secure random token for the sign-up link
  used_at,        -- null if not yet accepted
  created_at
)
```

---

## 4. Views (Pages)

| View | Description | Actions |
|---|---|---|
| **Dashboard** | Current balance, this week's listings summary, recent activity | — |
| **Marketplace — Offres** | Active listings this week, filtered by followed farms by default | Place order |
| **Marketplace — Demandes** | Wanted listings this week, filtered by followed farms by default | Post wanted listing · Respond to wanted listing · Accept / decline wanted response · Mark as fulfilled |
| **My Listings** | CRUD for the current week's offerings | Publish listing · Update stock · Close listing |
| **Order Flow** | Select quantity (capped at remaining stock) → add buyer note → submit | Place order |
| **Incoming Orders** | Seller view of pending orders | Accept order · Decline order · Confirm order · Cancel order |
| **My Tab** | Global balance + bilateral breakdown (who I owe, who owes me) + history | Generate relevé |
| **Settlement** | Declare a settlement for a farm pair | Declare settlement · Confirm settlement · Generate relevé |
| **Farm Profile** | Public page for each farm | Follow / unfollow |
| **Farm Map** | Map of all farms | Follow / unfollow |
| **Admin** | User management, ledger overview, export | Manual adjustment |
| **Email (signed URL)** | One-click shortcut outside the app — same actions as Incoming Orders | Accept order · Decline order |

---

## 5. Actions

| Action | Trigger | Effect |
|---|---|---|
| Post wanted listing | Buyer | Creates `wanted_listing`; notifies matching followed farms by email |
| Respond to wanted listing | Seller | Creates `wanted_response` (status: pending); buyer notified by email |
| Accept wanted response | Buyer | Status → accepted; mutual introduction email sent to both parties; wanted listing marked fulfilled; other pending responses auto-declined |
| Decline wanted response | Buyer | Status → declined; seller notified |
| Mark wanted as fulfilled | Buyer | Sets `is_fulfilled = true` manually (e.g. found product outside the app) |
| Publish listing | Producer | Creates/updates a `listing` for current week |
| Close listing | Producer / auto (week end) | Sets `is_active = false` |
| Place order | Buyer | Checks stock; creates `order` (pending); sends HTML email to seller with Accept/Decline buttons and `Reply-To: buyer@...` |
| Accept order | Seller | Clicks signed URL; status → accepted; app sends one email to **both parties** with name, email and phone of each; logistics handled directly between farmers |
| Decline order | Seller | Clicks signed URL in email; status → declined; stock freed; buyer notified with seller’s reason |
| Confirm order | Seller | Status → confirmed (goods exchanged); creates two `tab_entries` |
| Cancel order | Either party | Status → cancelled; stock freed automatically |
| Update stock | Producer | Updates `listings.quantity_available` mid-week (e.g. extra harvest) |
| Weekly reset | Cron job | Sends reminder, optionally archives old listings |
| Follow / unfollow farm | Producer | Creates or deletes a `farm_follows` row; affects marketplace default view |
| Declare settlement | Proposer | Creates `settlement` (pending); choose type: monetary / labor / write-off; enter amount + description |
| Confirm settlement | Counterpart | Status → confirmed; two `tab_entries` created; bilateral balance reduces |
| Generate relevé | Either party | Exports PDF of all orders between two farms for a chosen period; used by seller to draft their own invoice |
| Manual adjustment | Admin | Creates `tab_entry` directly (e.g. to correct an error) |

---

## 6. Email & Notification Summary

| Event | Recipient(s) | Content |
|---|---|---|
| Order placed | Seller | Order summary, buyer notes, [Accepter] / [Décliner] signed URL buttons |
| Order accepted | Both parties | Mutual introduction: name, email, phone of each farm |
| Order declined | Buyer | Seller's reason (`seller_notes`) |
| Order cancelled | The other party | Cancellation notice |
| Wanted listing posted | Farms that follow the poster AND have a product in the matching category | Listing description + link to respond |
| Wanted response posted | Buyer | Seller's offer (quantity, notes) |
| Wanted response accepted | Both parties | Mutual introduction: name, email, phone of each farm |
| Wanted response declined | Seller | Decline notice |
| Settlement declared | Counterpart | Settlement details + confirmation request |
| Settlement confirmed | Proposer | Confirmation receipt |
| Weekly reset (cron) | All farms with no active listing for the current week | Reminder to publish listings |

> All emails use `Reply-To` set to the sender's own email address, so any reply goes directly to them, not to the app.

---

## Open Questions to Resolve Early

1. ~~**Is price fixed in advance**~~ ✅ Prices are set weekly. `farm_products.default_price` is the baseline; producers override it per listing.
2. ~~**Tab settlement**~~ ✅ Bilateral balances computed from orders + settlements. A `settlement` is any clearing event: monetary (cash/virement), labor exchange, or mutual write-off. Proposer declares it, counterpart confirms. App generates a **relevé de compte** PDF (not a legal invoice) for a chosen period to support the seller’s own invoicing.
3. ~~**Closed-circle or open**~~ ✅ Open registration. `invitations` table kept for optional managed onboarding. Map of farms included — `farms` stores lat/lng geocoded from address.
4. ~~**Mobile-first or desktop?**~~ ✅ Responsive web app, mobile-friendly but not mobile-first. The views most used on a phone (Marketplace, Incoming Orders, My Tab) get a clean mobile layout; heavy admin views can stay desktop-only. PWA (manifest + service worker) and Capacitor wrapping are both retrofittable later — neither affects the Django architecture now.
