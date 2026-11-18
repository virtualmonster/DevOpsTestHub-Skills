"""Generate SendIt Cycles API tests for DevOps Test Hub (Script/2026 DSL).

Only constructs that appear in the vendor corpus or in the already-passing Health test are used:
  send {url, request.fields, response.fields}, `- val:` item lists, `- var:` capture,
  auth/bearer/token, content/<path>/* + repeat, verify: [js], assign: vars, run: {url, out}.
"""
import os, sys

ROOT = sys.argv[1]
BASE = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5000/api"
COMP = os.path.join(ROOT, "SendItCycles-API")


def q(s):
    """single-quoted YAML scalar"""
    return "'" + str(s).replace("'", "''") + "'"


def send(note, path, method="GET", token=None, body=None, status="200", checks=(), caps=(), whole=None, indent=2):
    """checks: [(json-path, expected)], caps: [(json-path, VAR)], whole: VAR to capture whole body."""
    p = " " * indent
    L = [f"{p}- send:",
         f"{p}    note: {q(note)}",
         f"{p}    url: ${{BASE_URL}}{path}",
         f"{p}    request:",
         f"{p}      fields:",
         f"{p}        - method:",
         f"{p}            - val: {method}",
         f"{p}        - headers/accept:",
         f"{p}            - val: application/json"]
    if token:
        L += [f"{p}        - auth/bearer/token:",
              f"{p}            - val: {q('${' + token + '}')}"]
    if body is not None:
        L += [f"{p}        - headers/content-type:",
              f"{p}            - val: application/json",
              f"{p}        - content:",
              f"{p}            - val: {q(body)}"]
    L += [f"{p}    response:",
          f"{p}      fields:",
          f"{p}        - status-code:",
          f"{p}            - val: {q(status)}"]
    for jp, exp in checks:
        L += [f"{p}        - content/{jp}:", f"{p}            - val: {q(exp)}"]
    for jp, var in caps:
        L += [f"{p}        - content/{jp}:", f"{p}            - var: {var}"]
    if whole:
        L += [f"{p}        - content:", f"{p}            - var: {whole}"]
    return L


def items_capture(note, path, token, caps):
    """GET returning an object that has an `items` array; caps: [(field, VAR)] captured per item."""
    p = "  "
    L = [f"{p}- send:",
         f"{p}    note: {q(note)}",
         f"{p}    url: ${{BASE_URL}}{path}",
         f"{p}    request:",
         f"{p}      fields:",
         f"{p}        - method:",
         f"{p}            - val: GET",
         f"{p}        - headers/accept:",
         f"{p}            - val: application/json",
         f"{p}        - auth/bearer/token:",
         f"{p}            - val: {q('${' + token + '}')}",
         f"{p}    response:",
         f"{p}      fields:",
         f"{p}        - status-code:",
         f"{p}            - val: '200'",
         f"{p}        - content/items/*:",
         f"{p}            - repeat: {{}}",
         f"{p}            - fields:"]
    for fld, var in caps:
        L += [f"{p}                - {fld}:", f"{p}                    - var: {var}"]
    return L


def verify(*exprs):
    return ["  - verify:"] + [f"      - {q(e)}" for e in exprs]


def assign(**kv):
    return ["  - assign:", "      vars:"] + [f"        {k}: {q(v)}" for k, v in kv.items()]


def log(msg):
    return [f"  - log: {q(msg)}"]


def run_module(out_map):
    L = ["  - run:", "      url: ../modules/Register And Login.dtx.yaml", "      out:"]
    # Module var -> caller var. An empty `{}` maps to NOTHING (Test Hub run 6087: TOKEN came back empty),
    # so always spell the caller name, even when it is the same: `TOKEN: [TOKEN]`.
    for k, v in out_map.items():
        L.append(f"        {k}: [{v}]")
    return L


PARSE = ["    PARSE:",
         "      expr: 'b => typeof b === \"string\" ? JSON.parse(b) : b'",
         "      type: js"]


def test(path, note, steps, extra_vars=(), parse=False, decl=()):
    """steps: list of line-lists. extra_vars: [(name, yaml scalar)]. decl: caller-side var names."""
    L = [f"note: {q(note)}", "configuration:", "  vars:", f"    BASE_URL: {BASE}"]
    for n, v in extra_vars:
        L.append(f"    {n}: {v}")
    for n in decl:
        L.append(f"    {n}: ''")
    if parse:
        L += PARSE
    L.append("steps:")
    for s in steps:
        L += s
    full = os.path.join(COMP, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")


AUTHVARS = ("TOKEN", "USER_ID", "EMAIL", "PASSWORD")
OUT = {v: v for v in AUTHVARS}

# ---------------------------------------------------------------------------- module
mod = f"""note: 'Registers a throwaway user with generated credentials, logs in, and returns TOKEN, USER_ID, EMAIL, PASSWORD'
configuration:
  vars:
    BASE_URL: {BASE}
    EMAIL:
      expr: unset
      modifier: out
    PASSWORD:
      expr: unset
      modifier: out
    TOKEN:
      expr: unset
      modifier: out
    USER_ID:
      expr: unset
      modifier: out
steps:
  - assign:
      vars:
        EMAIL: '${{"apitest+" + Date.now() + "-" + Math.floor(Math.random() * 100000) + "@example.com"}}'
        PASSWORD: '${{"Pw" + Date.now() + "x" + Math.floor(Math.random() * 1000000)}}'
"""
mod_steps = []
mod_steps += send("Register the generated user", "/auth/register", "POST",
                  body='{"email":"${EMAIL}","password":"${PASSWORD}","first_name":"Api","last_name":"Test"}',
                  status="201", checks=[("message", "User registered successfully")])
mod_steps += send("Log in as the generated user", "/auth/login", "POST",
                  body='{"email":"${EMAIL}","password":"${PASSWORD}"}',
                  checks=[("message", "Login successful"), ("user/email", "${EMAIL}"), ("user/role", "user")],
                  caps=[("token", "TOKEN"), ("user/id", "USER_ID")])
mod_steps += verify("typeof TOKEN === 'string' && TOKEN.length > 20")
os.makedirs(os.path.join(COMP, "modules"), exist_ok=True)
with open(os.path.join(COMP, "modules", "Register And Login.dtx.yaml"), "w", encoding="utf-8", newline="\n") as f:
    f.write(mod + "\n".join(mod_steps) + "\n")

# ---------------------------------------------------------------------------- 1 Atomic
A = "1 Atomic/"
test(A + "GET Health.dtx.yaml", "GET /health returns ok",
     [send("GET /health", "/health", checks=[("status", "ok")], caps=[("database", "DATABASE")]),
      log("Backend database: ${DATABASE}")])

test(A + "GET Categories.dtx.yaml", "GET /categories returns a non-empty list of categories",
     [send("GET /categories", "/categories", whole="BODY"),
      verify("PARSE(BODY).length >= 1",
             "PARSE(BODY).every(c => c.id > 0 && typeof c.name === 'string' && c.name.length > 0)")],
     parse=True)

test(A + "GET Products.dtx.yaml", "GET /products returns products with a price, stock and category",
     [send("GET /products", "/products", whole="BODY"),
      verify("PARSE(BODY).length >= 1",
             "PARSE(BODY).every(p => p.id > 0 && p.price > 0 && p.stock_quantity >= 0 && typeof p.category_name === 'string')")],
     parse=True)

test(A + "GET Product By Id.dtx.yaml", "GET /products/{id} returns the product (seed product 1)",
     [send("GET /products/1", "/products/${PRODUCT_ID}",
           checks=[("id", "${PRODUCT_ID}")],
           caps=[("name", "NAME"), ("price", "PRICE"), ("stock_quantity", "STOCK"), ("category_name", "CATEGORY")]),
      verify("Number(PRICE) > 0", "Number(STOCK) >= 0", "NAME.length > 0 && CATEGORY.length > 0"),
      log("Product ${PRODUCT_ID}: ${NAME} (${CATEGORY}) price ${PRICE}, stock ${STOCK}")],
     extra_vars=[("PRODUCT_ID", "'1'")])

test(A + "GET Product Not Found.dtx.yaml", "GET /products/{id} for an unknown id returns 404",
     [send("GET /products/99999", "/products/99999", status="404", checks=[("error", "Product not found")])])

test(A + "GET Product Non-Numeric Id.dtx.yaml", "GET /products/abc returns 404 rather than a server error",
     [send("GET /products/abc", "/products/abc", status="404")])

test(A + "GET Product Image.dtx.yaml", "GET /images/{file} serves a JPEG",
     [send("GET /images/1-swift-xc-pro.jpg", "/images/1-swift-xc-pro.jpg")]
     )
# image: also assert the content type header
_p = os.path.join(COMP, A + "GET Product Image.dtx.yaml")
_t = open(_p, encoding="utf-8").read().replace(
    "        - status-code:\n            - val: '200'\n",
    "        - status-code:\n            - val: '200'\n        - headers/content-type:\n            - val: image/jpeg\n")
open(_p, "w", encoding="utf-8", newline="\n").write(_t)

# ---------------------------------------------------------------------------- 2 Auth
U = "2 Auth/"
test(U + "POST Register User.dtx.yaml", "Registering a new user returns 201 and a token",
     [assign(EMAIL='${"apitest+" + Date.now() + "-" + Math.floor(Math.random() * 100000) + "@example.com"}',
             PASSWORD='${"Pw" + Date.now() + "x" + Math.floor(Math.random() * 1000000)}'),
      send("POST /auth/register", "/auth/register", "POST",
           body='{"email":"${EMAIL}","password":"${PASSWORD}","first_name":"Api","last_name":"Test"}',
           status="201", checks=[("message", "User registered successfully")],
           caps=[("token", "TOKEN"), ("user/id", "USER_ID")]),
      verify("typeof TOKEN === 'string' && TOKEN.length > 20", "Number(USER_ID) > 0")],
     extra_vars=[("EMAIL", "unset"), ("PASSWORD", "unset")])

test(U + "POST Register Missing Password.dtx.yaml", "Registration without a password is rejected with 400",
     [send("POST /auth/register without password", "/auth/register", "POST",
           body='{"email":"nobody@example.com"}', status="400",
           checks=[("error", "Email and password required")])])

test(U + "POST Login Valid.dtx.yaml", "A registered user can log in and receives a token and profile summary",
     [run_module(OUT),
      verify("typeof TOKEN === 'string' && TOKEN.length > 20", "Number(USER_ID) > 0"),
      log("Logged in as ${EMAIL} (user ${USER_ID})")],
     decl=AUTHVARS)

test(U + "POST Login Wrong Password.dtx.yaml", "Login with a wrong password returns 401",
     [run_module(OUT),
      send("POST /auth/login with the wrong password", "/auth/login", "POST",
           body='{"email":"${EMAIL}","password":"definitely-not-the-password"}', status="401",
           checks=[("error", "Invalid credentials")])],
     decl=AUTHVARS)

test(U + "POST Login Unknown User.dtx.yaml", "Login for an unknown email returns 401",
     [send("POST /auth/login for an unknown user", "/auth/login", "POST",
           body='{"email":"no-such-user-0000@example.com","password":"x"}', status="401",
           checks=[("error", "Invalid credentials")])])

test(U + "POST Login Missing Password.dtx.yaml", "Login without a password returns 400",
     [send("POST /auth/login without password", "/auth/login", "POST",
           body='{"email":"nobody@example.com"}', status="400",
           checks=[("error", "Email and password required")])])

test(U + "GET Profile With Token.dtx.yaml", "An authenticated user can read their own profile",
     [run_module(OUT),
      send("GET /auth/profile", "/auth/profile", token="TOKEN",
           checks=[("email", "${EMAIL}"), ("role", "user"), ("first_name", "Api"), ("last_name", "Test")],
           caps=[("id", "PROFILE_ID"), ("created_at", "CREATED")]),
      verify("Number(PROFILE_ID) === Number(USER_ID)", "CREATED.length > 0")],
     decl=AUTHVARS)

test(U + "GET Profile No Token.dtx.yaml", "Profile without a token returns 401",
     [send("GET /auth/profile without a token", "/auth/profile", status="401",
           checks=[("error", "No token provided")])])

test(U + "GET Profile Invalid Token.dtx.yaml", "Profile with a garbage token returns 401",
     [send("GET /auth/profile with a bad token", "/auth/profile", token="BAD_TOKEN", status="401",
           checks=[("error", "Invalid token")])],
     extra_vars=[("BAD_TOKEN", "not-a-real-token")])

test(U + "GET Orders Requires Token.dtx.yaml", "Listing orders without a token returns 401",
     [send("GET /orders without a token", "/orders", status="401", checks=[("error", "No token provided")])])

test(U + "GET Admin Categories Forbidden For User.dtx.yaml",
     "A normal user is refused on an admin route with 403 (read-only admin call)",
     [run_module(OUT),
      send("GET /admin/categories as a normal user", "/admin/categories", token="TOKEN", status="403",
           checks=[("error", "Admin access required")])],
     decl=AUTHVARS)

test(U + "GET Admin Categories No Token.dtx.yaml", "An admin route without a token returns 401",
     [send("GET /admin/categories without a token", "/admin/categories", status="401",
           checks=[("error", "No token provided")])])

# ---------------------------------------------------------------------------- 3 Workflows
W = "3 Workflows/"
test(W + "Register Login Profile.dtx.yaml",
     "Register, log in and read the profile; the id is consistent across all three calls",
     [assign(EMAIL='${"apitest+" + Date.now() + "-" + Math.floor(Math.random() * 100000) + "@example.com"}',
             PASSWORD='${"Pw" + Date.now() + "x" + Math.floor(Math.random() * 1000000)}'),
      send("Register", "/auth/register", "POST",
           body='{"email":"${EMAIL}","password":"${PASSWORD}","first_name":"Flow","last_name":"Tester"}',
           status="201", caps=[("user/id", "REG_ID")]),
      send("Log in", "/auth/login", "POST",
           body='{"email":"${EMAIL}","password":"${PASSWORD}"}',
           checks=[("user/email", "${EMAIL}"), ("user/first_name", "Flow"), ("user/last_name", "Tester")],
           caps=[("token", "TOKEN"), ("user/id", "LOGIN_ID")]),
      send("Read profile", "/auth/profile", token="TOKEN",
           checks=[("email", "${EMAIL}")], caps=[("id", "PROFILE_ID")]),
      verify("Number(REG_ID) === Number(LOGIN_ID)", "Number(LOGIN_ID) === Number(PROFILE_ID)")],
     extra_vars=[("EMAIL", "unset"), ("PASSWORD", "unset")])

test(W + "Browse Catalog Consistency.dtx.yaml",
     "The first product in the list matches its own detail page (id, name, price, stock)",
     [send("GET /products", "/products", whole="LIST"),
      assign(FIRST_ID='${PARSE(LIST)[0].id}', FIRST_NAME='${PARSE(LIST)[0].name}',
             FIRST_PRICE='${PARSE(LIST)[0].price}', FIRST_STOCK='${PARSE(LIST)[0].stock_quantity}'),
      send("GET /products/{id} for the first product", "/products/${FIRST_ID}",
           caps=[("name", "D_NAME"), ("price", "D_PRICE"), ("stock_quantity", "D_STOCK")]),
      verify("D_NAME === FIRST_NAME", "Number(D_PRICE) === Number(FIRST_PRICE)",
             "Number(D_STOCK) === Number(FIRST_STOCK)")],
     parse=True)

test(W + "Order Quantity 2 Totals And Stock.dtx.yaml",
     "Order 2 of product 1: total = 2 x catalog price, line item price matches, stock falls by 2",
     [run_module(OUT),
      send("Catalog price and stock before", "/products/${PRODUCT_ID}",
           caps=[("price", "PRICE"), ("stock_quantity", "STOCK_BEFORE"), ("name", "NAME")]),
      send("POST /orders with quantity ${QTY}", "/orders", "POST", token="TOKEN",
           body='{"items":[{"product_id":${PRODUCT_ID},"quantity":${QTY}}]}', status="201",
           checks=[("status", "pending")],
           caps=[("id", "ORDER_ID"), ("total_price", "TOTAL"), ("user_id", "ORDER_USER")]),
      verify("Math.abs(Number(TOTAL) - Number(QTY) * Number(PRICE)) < 0.005",
             "Number(ORDER_USER) === Number(USER_ID)"),
      items_capture("GET /orders/{id}", "/orders/${ORDER_ID}", "TOKEN",
                    [("product_id", "L_PID"), ("quantity", "L_QTY"), ("price", "L_PRICE"), ("name", "L_NAME")]),
      verify("[].concat(L_PID).length === 1",
             "Number([].concat(L_PID)[0]) === Number(PRODUCT_ID)",
             "Number([].concat(L_QTY)[0]) === Number(QTY)",
             "Math.abs(Number([].concat(L_PRICE)[0]) - Number(PRICE)) < 0.005",
             "[].concat(L_NAME)[0] === NAME"),
      send("Catalog stock after", "/products/${PRODUCT_ID}", caps=[("stock_quantity", "STOCK_AFTER")]),
      verify("Number(STOCK_BEFORE) - Number(STOCK_AFTER) === Number(QTY)"),
      send("GET /orders lists the new order", "/orders", token="TOKEN", whole="MY_ORDERS"),
      verify("PARSE(MY_ORDERS).some(o => Number(o.id) === Number(ORDER_ID))")],
     extra_vars=[("PRODUCT_ID", "'1'"), ("QTY", "'2'")], parse=True, decl=AUTHVARS)

test(W + "Order Two Products Total.dtx.yaml",
     "Order 1 x product 1 and 2 x product 2: total = sum of catalog prices x quantities = sum of line items",
     [run_module(OUT),
      send("Catalog price product 1", "/products/1", caps=[("price", "P1")]),
      send("Catalog price product 2", "/products/2", caps=[("price", "P2")]),
      send("POST /orders with two lines", "/orders", "POST", token="TOKEN",
           body='{"items":[{"product_id":1,"quantity":1},{"product_id":2,"quantity":2}]}', status="201",
           caps=[("id", "ORDER_ID"), ("total_price", "TOTAL")]),
      verify("Math.abs(Number(TOTAL) - (Number(P1) + 2 * Number(P2))) < 0.005"),
      items_capture("GET /orders/{id}", "/orders/${ORDER_ID}", "TOKEN",
                    [("product_id", "L_PID"), ("quantity", "L_QTY"), ("price", "L_PRICE")]),
      verify("[].concat(L_PID).length === 2",
             "[].concat(L_PID).map(Number).sort().join() === '1,2'",
             "Math.abs(Number(TOTAL) - [].concat(L_PRICE).reduce((s, p, i) => s + Number(p) * Number([].concat(L_QTY)[i]), 0)) < 0.005")],
     decl=AUTHVARS + ("ORDER_ID",))

test(W + "Order Isolation Between Users.dtx.yaml",
     "A user cannot see or fetch another user's order (404 and an empty list for the second user)",
     [run_module(OUT),
      send("User A places an order for product 3", "/orders", "POST", token="TOKEN",
           body='{"items":[{"product_id":3,"quantity":1}]}', status="201", caps=[("id", "ORDER_ID")]),
      run_module({"TOKEN": "TOKEN_B", "USER_ID": "USER_B", "EMAIL": "EMAIL_B", "PASSWORD": "PASSWORD_B"}),
      send("User B fetches user A's order", "/orders/${ORDER_ID}", token="TOKEN_B", status="404",
           checks=[("error", "Order not found")]),
      send("User B lists their orders", "/orders", token="TOKEN_B", whole="B_ORDERS"),
      verify("PARSE(B_ORDERS).length === 0",
             "!PARSE(B_ORDERS).some(o => Number(o.id) === Number(ORDER_ID))")],
     decl=AUTHVARS + ("TOKEN_B", "USER_B", "EMAIL_B", "PASSWORD_B", "ORDER_ID"), parse=True)

test(W + "Order Rejected Insufficient Stock.dtx.yaml",
     "An order larger than stock is rejected with 400 and the stock is unchanged",
     [run_module(OUT),
      send("Stock before", "/products/5", caps=[("stock_quantity", "STOCK_BEFORE")]),
      send("POST /orders far above stock", "/orders", "POST", token="TOKEN",
           body='{"items":[{"product_id":5,"quantity":1000000}]}', status="400",
           checks=[("error", "Insufficient stock for product 5")]),
      send("Stock after", "/products/5", caps=[("stock_quantity", "STOCK_AFTER")]),
      verify("Number(STOCK_BEFORE) === Number(STOCK_AFTER)")],
     decl=AUTHVARS)

test(W + "Order Cart Validation.dtx.yaml",
     "Empty cart is rejected with 400 and an unknown product with 404",
     [run_module(OUT),
      send("POST /orders with no items", "/orders", "POST", token="TOKEN",
           body='{"items":[]}', status="400", checks=[("error", "Cart is empty")]),
      send("POST /orders with an unknown product", "/orders", "POST", token="TOKEN",
           body='{"items":[{"product_id":99999,"quantity":1}]}', status="404",
           checks=[("error", "Product 99999 not found")])],
     decl=AUTHVARS)

# ---------------------------------------------------------------------------- Known Issues
K = "Known Issues/"
test(K + "GET Products By Category.dtx.yaml",
     "KNOWN ISSUE: documented to list a category's products but the host returns 500 (SQL alias bug). Passes once fixed.",
     [send("GET /categories/1/products", "/categories/1/products", whole="BODY"),
      verify("PARSE(BODY).length >= 1", "PARSE(BODY).every(p => Number(p.category_id) === 1)")],
     parse=True)

test(K + "POST Register Duplicate Email.dtx.yaml",
     "KNOWN ISSUE: registering an existing email should return 409 but the host returns 500. Passes once fixed.",
     [assign(EMAIL='${"apitest+" + Date.now() + "-" + Math.floor(Math.random() * 100000) + "@example.com"}',
             PASSWORD='${"Pw" + Date.now() + "x" + Math.floor(Math.random() * 1000000)}'),
      send("First registration", "/auth/register", "POST",
           body='{"email":"${EMAIL}","password":"${PASSWORD}"}', status="201"),
      send("Duplicate registration", "/auth/register", "POST",
           body='{"email":"${EMAIL}","password":"${PASSWORD}"}', status="409",
           checks=[("error", "Email already exists")])],
     extra_vars=[("EMAIL", "unset"), ("PASSWORD", "unset")])

test(K + "POST Login Malformed JSON.dtx.yaml",
     "KNOWN ISSUE: a malformed JSON body should return 400 but the host returns 500. Passes once fixed.",
     [send("POST /auth/login with malformed JSON", "/auth/login", "POST", body='{bad json', status="400")])

# ---------------------------------------------------------------------------- suites
def suite(name, note, tests):
    L = [f"note: {q(note)}", "tests:"] + [f"  - {t}" for t in tests]
    with open(os.path.join(COMP, name), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")


def listdir(sub):
    return sorted(f"{sub}{n}" for n in os.listdir(os.path.join(COMP, sub)) if n.endswith(".dtx.yaml"))


suite("_Atomic Suite.dts.yaml", "Single-call read-only checks (no data written)", listdir(A))
suite("_Auth Suite.dts.yaml", "Registration, login, token and access-control checks (creates throwaway users)", listdir(U))
suite("_Workflow Suite.dts.yaml",
      "Chained flows incl. orders (creates users and orders; reduces stock of products 1, 2, 3)", listdir(W))
suite("_Known Issues Suite.dts.yaml",
      "Tests that currently FAIL on the demo host because of known defects; they pass when the defects are fixed",
      listdir(K))
suite("_All API Tests Suite.dts.yaml", "Atomic, auth and workflow suites (excludes Known Issues)",
      ["_Atomic Suite.dts.yaml", "_Auth Suite.dts.yaml", "_Workflow Suite.dts.yaml"])
print("generated under", COMP)
