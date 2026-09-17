# CycleStore — confirmed live facts

Base URL (this test instance): `http://10.134.60.215:3000/`. Confirmed live by actually driving
the app (not inferred from other tests). Trust this for anything it covers; only live-verify
what's genuinely new, or if something here turns out to be wrong.

## Navigation (top nav, `html.a` unless noted)

- Logged out: `Shop`, `Contact`, `Login`, `Register`.
- Logged in (customer): `Shop`, `Contact`, `<FirstName>` (not clickable, just a name display),
  `Orders`, `Logout` (`html.button`), and a cart link `🛒<count>` (e.g. `🛒1`) → `/cart`.
- Logged in (admin): same shape, plus `Admin` → `/admin`.
- `Logout` (`html.button`, content `Logout`) always redirects to `/shop`.

## Home (`/`)

- `Shop Now` (`html.a`, content `Shop Now`) → `/shop`. **Only present on Home, not on `/shop`
  itself** — if a flow needs to reach `/shop` via this link (e.g. to reuse
  `modules/Add Product To Cart.dtx.yaml`, which starts here), make sure the test is actually on
  Home first (an explicit `open:` back to the base URL if the previous step landed on `/shop`).

## Register (`/register`)

- Fields: `Email` (`html.inputemail`, label `Email`), `First Name` / `Last Name`
  (`html.inputtext`, labels `First Name` / `Last Name`), `Password` (`html.inputpassword`, label
  `Password`). Submit: `html.button`, content `Create Account`.
- **Registration auto-signs the user in** and redirects to `/shop` — there is no separate login
  step unless the test explicitly signs out first to exercise login.

## Login (`/login`)

- Fields: `Email` (`html.inputemail`, label `Email`), `Password` (`html.inputpassword`, label
  `Password`). Submit: `html.button`, content `Sign In`.
- Redirect after login differs by role: **customer → `/shop`, admin → `/admin`** (directly, no
  extra nav click needed for admin — see Admin console below).
- The page displays a "Demo Admin Account" hint box: `admin@senditcycles.com` / `admin123`.
  Confirmed live this session — re-check if a test using it ever fails at admin login.

## Shop (`/shop`) and product page (`/product/<n>`)

- Filter buttons: `All` / `Downcountry` / `Downhill` / `Enduro` / `Trail` / `XC` (`html.button`).
- Product cards have an `html.img` whose `src` ends in a stable per-product filename, e.g.
  `2-trailblazer-elite.jpg` for "TrailBlazer Elite" — clicking the image navigates to
  `/product/<n>`. Use the image `src` as the identifier (matches `modules/Add Product To
  Cart.dtx.yaml`'s convention), not the product name text.
- Product page: size buttons `S`/`M`/`L`/`XL`, quantity `−`/`+`, and `Add to Cart` (all
  `html.button`). Cart link becomes `🛒<count>` after adding.

## Cart (`/cart`)

- `h1` content `Shopping Cart`. Buttons: `Remove`, `Checkout` (`html.button`).

## Checkout (`/checkout`)

- Fields (all with visible labels, `*` included in the label text): `First Name *`, `Last Name *`,
  `Email *`, `Phone *` (`input[type=tel]` — recorded module uses an `xpath` + `inside` locator for
  this one rather than `label`, still valid), `Address *`, `City *`, `State/Province *`,
  `Country *`, then payment: `Cardholder Name *`, `Card Type` (`html.select`: `visa`/`mastercard`/
  `amex`/`discover`, defaults to `visa`), `Card Number *`, `Month *` (`html.select`, `01`-`12`),
  `Year *` (`html.select`, starts at the current year), `CVV *`.
- **`Card Type` and `Year` are not present in the older recorded `modules/Check Out.dtx.yaml`** —
  the app gained these fields since that module was recorded. Their defaults (`visa`, current
  year) are accepted without selecting them, so the module still works, but doesn't exercise
  those two fields. If a test specifically needs a non-default card type or year, add explicit
  `select:` steps for them.
- Submit: `html.button`, content `Complete Purchase`. Redirects to `/orders` on success.

## Orders — customer view (`/orders`)

- Heading `My Orders`. Each order shows `Order #`, `Date`, `Total`, `Status`, `Items`.
- **The status value's raw DOM text is lowercase** (`pending`, `shipped`) but is rendered
  capitalized via CSS `text-transform`. Match on the rendered form (`Pending`, `Shipped`) in
  `content`, not the raw lowercase text — this is what the existing modules already do and what
  DevOps Test Hub's own element resolution compares against.
- Status element is an `html.p`.

## Admin console (`/admin`)

- Reached directly after admin login — **no need to click an `Admin` nav link or an `Orders` tab
  first**, contrary to what the older `Admin Portal Login.dtx.yaml` test does; it lands straight
  on the Orders tab, showing "Customer Orders". Tabs: `Orders` / `Products` / `Categories`
  (`html.button`).
- Each order card shows: Order ID (`html.p`, class `font-bold`, e.g. `#81`), Customer name +
  email, Total, Date, Items, a status badge, and two action buttons `Mark Pending` / `Mark
  Shipped` (`html.button`).
- **The status badge here is an `html.span` whose text is UPPERCASE** (`PENDING`/`SHIPPED`) —
  a different element and case convention than the customer-facing `/orders` page. Don't reuse
  a selector that matches one for the other.
- **Order IDs increment globally across every test run, for every user** — never hardcode one to
  identify "the order this test just created". Anchor the right card instead via a `locators:
  inside` on the card's `html.div`, matching `content: includes: '${Email}'` with the test's own
  (uniquely-generated) customer email.
- **App quirk, not a test-authoring mistake**: after clicking `Mark Shipped` on a card, that
  order's Customer name/email stop rendering in the admin list (the fields go blank) — confirmed
  live, not something to fix. Don't rely on reading the customer name/email back off a card after
  changing its status in the same test.

## Modules — confirmed still valid against the live app (as of this session)

- `modules/Sign In.dtx.yaml`: still matches; works for both customer and admin login when its
  `Email`/`Password` are overridden via `run: {url: ..., in: {...}}`.
- `modules/Add Product To Cart.dtx.yaml`: still matches, **but only if the browser is on Home
  first** (see "Home" above) — its first step clicks `Shop Now`, which doesn't exist on `/shop`.
- `modules/Check Out.dtx.yaml`: still matches; doesn't set the newer `Card Type`/`Year` fields
  (see Checkout above), which is fine since their defaults are acceptable.
- `modules/Sign Out.dtx.yaml`: matches **only** in a context where a `Pending` (customer-view,
  `html.p`) element is genuinely on screen (e.g. right after checking an order's status). It does
  **not** match on the Admin console (no matching element there) — use a plain `Logout` click in
  that context instead.
