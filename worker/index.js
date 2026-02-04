var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// =========================
// OpenAPI Spec (for GPT Action import)
// NOTE: Do NOT include /openapi.json inside paths to avoid GPT Builder schema validation issues.
// =========================
const OPENAPI_SPEC = {
    openapi: "3.1.0",
    info: {
        title: "Expense GPT API",
        description:
            "API for adding and querying personal expense records. Authentication via X-API-Key header.",
        version: "1.0.1"
    },
    servers: [{ url: "https://expense-api.showbox88.workers.dev" }],
    paths: {
        "/add": {
            post: {
                operationId: "addExpense",
                summary: "Add expense records from natural language text",
                security: [{ ApiKeyAuth: [] }],
                requestBody: {
                    required: true,
                    content: {
                        "application/json": {
                            schema: {
                                type: "object",
                                additionalProperties: false,
                                properties: {
                                    text: {
                                        type: "string",
                                        description: "Original user input containing expense information"
                                    },
                                    source: {
                                        type: "string",
                                        description: "Source of the record, e.g. gpt, api, manual"
                                    }
                                },
                                required: ["text", "source"]
                            }
                        }
                    }
                },
                responses: {
                    "200": {
                        description: "Expenses successfully inserted",
                        content: {
                            "application/json": {
                                schema: {
                                    type: "object",
                                    additionalProperties: false,
                                    properties: {
                                        ok: { type: "boolean" },
                                        inserted: { type: "integer" },
                                        rows: {
                                            type: "array",
                                            items: {
                                                type: "object",
                                                additionalProperties: false,
                                                properties: {
                                                    date: { type: "string", description: "YYYY-MM-DD" },
                                                    item: { type: "string" },
                                                    amount: { type: "number" },
                                                    category: { type: "string" },
                                                    note: { type: ["string", "null"] }
                                                },
                                                required: ["date", "item", "amount", "category", "note"]
                                            }
                                        }
                                    },
                                    required: ["ok", "inserted", "rows"]
                                }
                            }
                        }
                    },
                    "401": {
                        description: "Unauthorized (invalid API key)",
                        content: {
                            "application/json": {
                                schema: {
                                    type: "object",
                                    additionalProperties: true,
                                    properties: {
                                        detail: { type: "string" }
                                    },
                                    required: ["detail"]
                                }
                            }
                        }
                    },
                    "422": {
                        description: "Validation error",
                        content: {
                            "application/json": {
                                schema: {
                                    type: "object",
                                    additionalProperties: true,
                                    properties: {
                                        detail: { type: "string" }
                                    },
                                    required: ["detail"]
                                }
                            }
                        }
                    }
                }
            }
        },
        "/delete": {
            post: {
                operationId: "deleteExpense",
                summary: "Delete an expense record by ID",
                description: "Use this to delete a record. FIRST call /list to find the ID of the record to delete.",
                security: [{ ApiKeyAuth: [] }],
                requestBody: {
                    required: true,
                    content: {
                        "application/json": {
                            schema: {
                                type: "object",
                                properties: {
                                    id: { type: "integer", description: "The ID of the record to delete" }
                                },
                                required: ["id"]
                            }
                        }
                    }
                },
                responses: {
                    "200": {
                        description: "Record deleted",
                        content: { "application/json": { schema: { type: "object", properties: { ok: { type: "boolean" } } } } }
                    }
                }
            }
        },
        "/update": {
            post: {
                operationId: "updateExpense",
                summary: "Update an existing expense record",
                description: "Use this to correct extended details. FIRST call /list to find the ID.",
                security: [{ ApiKeyAuth: [] }],
                requestBody: {
                    required: true,
                    content: {
                        "application/json": {
                            schema: {
                                type: "object",
                                properties: {
                                    id: { type: "integer" },
                                    date: { type: "string", description: "YYYY-MM-DD" },
                                    item: { type: "string" },
                                    amount: { type: "number" },
                                    category: { type: "string" },
                                    note: { type: "string" }
                                },
                                required: ["id"]
                            }
                        }
                    }
                },
                responses: {
                    "200": {
                        description: "Record updated",
                        content: { "application/json": { schema: { type: "object", properties: { ok: { type: "boolean" } } } } }
                    }
                }
            }
        },
        "/list": {
            get: {
                operationId: "listExpenses",
                summary: "List recent expense records (Use this to find IDs for delete/update)",
                description: "Returns the last 200 records. Always call this BEFORE deleting or updating to ensure you have the correct ID.",
                security: [{ ApiKeyAuth: [] }],
                responses: {
                    "200": {
                        description: "List of expense records",
                        content: {
                            "application/json": {
                                schema: {
                                    type: "object",
                                    additionalProperties: false,
                                    properties: {
                                        ok: { type: "boolean" },
                                        rows: {
                                            type: "array",
                                            items: {
                                                type: "object",
                                                additionalProperties: true,
                                                properties: {
                                                    id: { type: "integer" },
                                                    date: { type: "string" },
                                                    item: { type: "string" },
                                                    amount: { type: "number" },
                                                    category: { type: "string" },
                                                    note: { type: ["string", "null"] },
                                                    source: { type: "string" },
                                                    created_at: { type: "string" }
                                                },
                                                required: [
                                                    "id",
                                                    "date",
                                                    "item",
                                                    "amount",
                                                    "category",
                                                    "source",
                                                    "created_at"
                                                ]
                                            }
                                        }
                                    },
                                    required: ["ok", "rows"]
                                }
                            }
                        }
                    },
                    "401": {
                        description: "Unauthorized (invalid API key)",
                        content: {
                            "application/json": {
                                schema: {
                                    type: "object",
                                    additionalProperties: true,
                                    properties: {
                                        detail: { type: "string" }
                                    },
                                    required: ["detail"]
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    components: {
        // GPT Builder complains if schemas isn't an object; keep it as empty object.
        schemas: {},
        securitySchemes: {
            ApiKeyAuth: { type: "apiKey", in: "header", name: "X-API-Key" }
        }
    }
};

// =========================
// Helpers
// =========================
function json(data, status = 200) {
    return new Response(JSON.stringify(data, null, 2), {
        status,
        headers: { "content-type": "application/json; charset=utf-8" }
    });
}
__name(json, "json");

function auth(req, env) {
    const got = (req.headers.get("X-API-Key") || "").trim();
    const expected = (env.APP_API_KEY || "").trim();
    if (!expected || got !== expected) {
        throw new Response(JSON.stringify({ detail: "Invalid API key" }), {
            status: 401,
            headers: { "content-type": "application/json; charset=utf-8" }
        });
    }
}
__name(auth, "auth");

function extractTextFromResponses(obj) {
    if (!obj) return null;

    if (typeof obj.output_text === "string" && obj.output_text.trim()) {
        return obj.output_text.trim();
    }

    const out = obj.output;
    if (!Array.isArray(out)) return null;

    const texts = [];
    for (const msg of out) {
        const content = msg?.content;
        if (!Array.isArray(content)) continue;

        for (const part of content) {
            if (typeof part?.text === "string" && part.text.trim()) {
                texts.push(part.text.trim());
                continue;
            }
            if (typeof part?.value === "string" && part.value.trim()) {
                texts.push(part.value.trim());
                continue;
            }
            if (part?.type === "json" && part?.json) {
                try {
                    texts.push(JSON.stringify(part.json));
                } catch {
                    // ignore
                }
            }
        }
    }

    if (!texts.length) return null;
    return texts.join("\n").trim();
}
__name(extractTextFromResponses, "extractTextFromResponses");

async function parseWithOpenAI(env, text, refDate) {
    const schema = {
        type: "object",
        additionalProperties: false,
        required: ["items"],
        properties: {
            items: {
                type: "array",
                items: {
                    type: "object",
                    additionalProperties: false,
                    required: ["date", "item", "amount", "category", "note"],
                    properties: {
                        date: { type: "string", description: "YYYY-MM-DD" },
                        item: { type: "string" },
                        amount: { type: "number" },
                        category: { type: "string" },
                        note: { type: ["string", "null"] }
                    }
                }
            }
        }
    };

    const body = {
        model: "gpt-4o-mini",
        input: [
            {
                role: "system",
                content: `参考日期是 ${refDate}。
任务：把中文记账文本解析成 JSON：{"items":[...]}。
支持 今天/昨天/前天，并转换为 YYYY-MM-DD。
强规则：
- item 必须是“商品/事项名称”，绝对不能是纯数字。
- amount 必须是数字金额。
- 若出现“外套100”这种粘连写法：item="外套", amount=100。
- 若出现“前天打车30”：item="打车", amount=30, date=前天日期。
- category 必须在：餐饮/日用品/交通/服饰/医疗/娱乐/居住/其他 里选一个（不确定就用 其他）。
- note 没有就填 null。
输出必须严格符合 schema，且 items 数组中每条都必须包含：date,item,amount,category,note。
`
            },
            { role: "user", content: text }
        ],
        text: {
            format: {
                type: "json_schema",
                name: "expense_rows",
                schema,
                strict: true
            }
        },
        store: false
    };

    const r = await fetch("https://api.openai.com/v1/responses", {
        method: "POST",
        headers: {
            Authorization: `Bearer ${env.OPENAI_API_KEY}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });

    const raw = await r.text();
    if (!r.ok) {
        throw new Error(`OpenAI HTTP ${r.status}: ${raw.slice(0, 800)}`);
    }

    const obj = JSON.parse(raw);
    const outText = extractTextFromResponses(obj);
    if (!outText) {
        throw new Error(
            `OpenAI returned no extractable text. keys=${Object.keys(obj || {}).join(",")}`
        );
    }

    const parsed = JSON.parse(outText);
    const rows = parsed?.items;
    if (!Array.isArray(rows)) throw new Error("Model output missing items[]");
    return rows;
}
__name(parseWithOpenAI, "parseWithOpenAI");

async function processRecurringExpenses(env) {
    const todayDate = new Date();
    const todayStr = todayDate.toISOString().slice(0, 10); // YYYY-MM-DD
    const dayOfWeek = todayDate.getDay() || 7; // 1 (Mon) - 7 (Sun)
    const dayOfMonth = todayDate.getDate(); // 1-31
    const month = todayDate.getMonth() + 1; // 1-12
    const dayOfYear = Math.floor((todayDate - new Date(todayDate.getFullYear(), 0, 0)) / 1000 / 60 / 60 / 24);

    // Get all active rules
    const rules = await env.expense_db.prepare("SELECT * FROM recurring_rules WHERE active = 1").all();
    const results = rules.results || [];

    let processed = 0;

    for (const rule of results) {
        // Check if already run today
        if (rule.last_run_date === todayStr) continue;

        let shouldRun = false;

        if (rule.frequency === 'weekly' && rule.day === dayOfWeek) shouldRun = true;
        if (rule.frequency === 'monthly' && rule.day === dayOfMonth) shouldRun = true;
        if (rule.frequency === 'yearly') {
            // Simple yearly check (day field could store DayOfYear or we parse specific logic, 
            // but for simplicity in this MVP let's assume day field stores MMDD integer e.g. 101 for Jan 1st? 
            // Or better, let's keep it simple: Yearly not fully supported in this simple logic without more complex schema.
            // Let's stick to Weekly/Monthly for MVP as requested "weekly or monthly" in prompt.
            // User prompt said: "weekly or monthly ... or yearly".
            // Let's support Yearly by assuming 'day' is encoded or just relying on month/day check if we had correct columns.
            // Current schema only has 'day'. Let's skip yearly for a moment or treat 'day' as DayOfYear.
            if (rule.day === dayOfYear) shouldRun = true;
        }

        if (shouldRun) {
            // Insert Expense
            await env.expense_db.prepare(
                "INSERT INTO expenses (date, item, amount, category, note, source) VALUES (?, ?, ?, ?, ?, ?)"
            ).bind(todayStr, rule.name, rule.amount, rule.category, "Auto-Recurring", "system").run();

            // Update Rule last_run_date
            await env.expense_db.prepare(
                "UPDATE recurring_rules SET last_run_date = ? WHERE id = ?"
            ).bind(todayStr, rule.id).run();

            processed++;
        }
    }
    return processed;
}
__name(processRecurringExpenses, "processRecurringExpenses");

// =========================
// Worker fetch
// =========================
var index_default = {
    async fetch(req, env) {
        try {
            const url = new URL(req.url);

            // ✅ OpenAPI JSON endpoint (no auth)
            if (req.method === "GET" && url.pathname === "/openapi.json") {
                return json(OPENAPI_SPEC);
            }

            // Root health check
            if (req.method === "GET" && url.pathname === "/") {
                return new Response("ok", { status: 200 });
            }

            // Debug auth (no auth)
            if (req.method === "GET" && url.pathname === "/debug-auth") {
                const got = (req.headers.get("X-API-Key") || "").trim();
                const expected = (env.APP_API_KEY || "").trim();
                return json({
                    has_expected: expected.length > 0,
                    expected_len: expected.length,
                    got_len: got.length,
                    equal: expected.length > 0 && got === expected
                });
            }

            // Debug keys (auth)
            if (req.method === "GET" && url.pathname === "/debug-keys") {
                auth(req, env);
                const app = (env.APP_API_KEY || "").trim();
                const oai = (env.OPENAI_API_KEY || "").trim();
                return json({
                    app_len: app.length,
                    openai_len: oai.length,
                    openai_prefix: oai.slice(0, 7)
                });
            }

            // ✅ List (auth) — return { ok:true, rows:[...] }
            if (req.method === "GET" && url.pathname === "/list") {
                auth(req, env);
                const res = await env.expense_db
                    .prepare(
                        "SELECT id, date, item, amount, category, note, source, created_at FROM expenses ORDER BY id DESC LIMIT 200"
                    )
                    .all();
                return json({ ok: true, rows: res.results || [] });
            }

            // Add (auth)
            if (req.method === "POST" && url.pathname === "/add") {
                auth(req, env);
                const body = await req.json();

                const text = String(body.text || "").trim();
                if (!text) return json({ detail: "text is required" }, 422);

                const today = new Date().toISOString().slice(0, 10);
                const source = body.source || "gpt";

                const rows = await parseWithOpenAI(env, text, today);

                for (const r of rows) {
                    await env.expense_db
                        .prepare(
                            "INSERT INTO expenses (date,item,amount,category,note,source) VALUES (?,?,?,?,?,?)"
                        )
                        .bind(
                            r.date || today,
                            r.item,
                            r.amount,
                            r.category || "其他",
                            r.note ?? null,
                            source
                        )
                        .run();
                }

                return json({ ok: true, inserted: rows.length, rows });
            }

            // Update (auth)
            if (req.method === "POST" && url.pathname === "/update") {
                auth(req, env);
                const body = await req.json();

                if (!body.id) return json({ detail: "id is required" }, 422);

                const res = await env.expense_db
                    .prepare(`UPDATE expenses 
                              SET date = ?, item = ?, amount = ?, category = ?, note = ?
                              WHERE id = ?`)
                    .bind(
                        body.date,
                        body.item,
                        body.amount,
                        body.category,
                        body.note,
                        body.id
                    )
                    .run();

                return json({ ok: res.success, meta: res.meta });
            }

            // Delete (auth)
            if (req.method === "POST" && url.pathname === "/delete") {
                auth(req, env);
                const body = await req.json();

                if (!body.id) return json({ detail: "id is required" }, 422);

                const res = await env.expense_db
                    .prepare("DELETE FROM expenses WHERE id = ?")
                    .bind(body.id)
                    .run();

                return json({ ok: res.success, meta: res.meta });
            }

            // Clear All (auth)
            if (req.method === "POST" && url.pathname === "/clear") {
                auth(req, env);
                const res = await env.expense_db.prepare("DELETE FROM expenses").run();
                return json({ ok: res.success, meta: res.meta });
            }

            // ====== V3.0 Features ======

            // Budget: list
            if (req.method === "GET" && url.pathname === "/budget/list") {
                auth(req, env);
                // Careful: table might not exist if user didn't run migration.
                try {
                    const res = await env.expense_db.prepare("SELECT * FROM budgets ORDER BY id DESC").all();
                    return json({ ok: true, rows: res.results || [] });
                } catch (e) {
                    return json({ ok: false, error: "Table 'budgets' likely missing. Please create it." }, 500);
                }
            }

            // Budget: add
            if (req.method === "POST" && url.pathname === "/budget/add") {
                auth(req, env);
                const body = await req.json();
                const res = await env.expense_db
                    .prepare("INSERT INTO budgets (name, category, amount, color, icon) VALUES (?, ?, ?, ?, ?)")
                    .bind(body.name, body.category, body.amount, body.color || '#FF4B4B', body.icon || '💰')
                    .run();
                return json({ ok: res.success, meta: res.meta });
            }

            // Budget: delete
            if (req.method === "POST" && url.pathname === "/budget/delete") {
                auth(req, env);
                const body = await req.json();
                const res = await env.expense_db.prepare("DELETE FROM budgets WHERE id = ?").bind(body.id).run();
                return json({ ok: res.success, meta: res.meta });
            }

            // Recurring: list
            if (req.method === "GET" && url.pathname === "/recurring/list") {
                auth(req, env);
                try {
                    const res = await env.expense_db.prepare("SELECT * FROM recurring_rules WHERE active = 1 ORDER BY id DESC").all();
                    return json({ ok: true, rows: res.results || [] });
                } catch (e) {
                    return json({ ok: false, error: "Table 'recurring_rules' likely missing." }, 500);
                }
            }

            // Recurring: add
            if (req.method === "POST" && url.pathname === "/recurring/add") {
                auth(req, env);
                const body = await req.json();
                const res = await env.expense_db
                    .prepare("INSERT INTO recurring_rules (name, amount, category, frequency, day) VALUES (?, ?, ?, ?, ?)")
                    .bind(body.name, body.amount, body.category, body.frequency, body.day)
                    .run();
                return json({ ok: res.success, meta: res.meta });
            }

            // Recurring: delete
            if (req.method === "POST" && url.pathname === "/recurring/delete") {
                auth(req, env);
                const body = await req.json();
                const res = await env.expense_db.prepare("DELETE FROM recurring_rules WHERE id = ?").bind(body.id).run();
                return json({ ok: res.success, meta: res.meta });
            }

            // Recurring: update
            if (req.method === "POST" && url.pathname === "/recurring/update") {
                auth(req, env);
                const body = await req.json();
                if (!body.id) return json({ detail: "id is required" }, 422);

                const res = await env.expense_db
                    .prepare(`UPDATE recurring_rules 
                              SET name = ?, amount = ?, category = ?, frequency = ?, day = ?, active = ?
                              WHERE id = ?`)
                    .bind(
                        body.name,
                        body.amount,
                        body.category,
                        body.frequency,
                        body.day,
                        body.active === undefined ? 1 : (body.active ? 1 : 0),
                        body.id
                    )
                    .run();
                return json({ ok: res.success, meta: res.meta });
            }

            // Recurring: check (Manual Trigger)
            if (req.method === "GET" && url.pathname === "/recurring/check") {
                auth(req, env);
                const processed = await processRecurringExpenses(env);
                return json({ ok: true, processed });
            }

            return new Response("Not Found", { status: 404 });
        } catch (e) {
            if (e instanceof Response) return e;
            return json({ error: String(e?.message || e) }, 500);
        }
    },

    // Cron Trigger Handler
    async scheduled(event, env, ctx) {
        ctx.waitUntil(processRecurringExpenses(env));
    }
};

export { index_default as default };
//# sourceMappingURL=index.js.map
