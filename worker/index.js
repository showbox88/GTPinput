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
        "/list": {
            get: {
                operationId: "listExpenses",
                summary: "List recent expense records",
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
- category 必须在：餐饮/日用品/交通/服饰/医疗/娱乐/其他 里选一个（不确定就用 其他）。
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

            return new Response("Not Found", { status: 404 });
        } catch (e) {
            if (e instanceof Response) return e;
            return json({ error: String(e?.message || e) }, 500);
        }
    }
};

export { index_default as default };
//# sourceMappingURL=index.js.map
