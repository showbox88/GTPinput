
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// Helper: Standard JSON response
function json(data: any, status = 200) {
    return new Response(JSON.stringify(data), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status,
    });
}

// Helper: Extract text from OpenAI response (ported from Worker)
function extractTextFromResponses(obj: any) {
    if (!obj) return null;
    if (typeof obj.output_text === "string" && obj.output_text.trim()) return obj.output_text.trim();
    const out = obj.output;
    if (!Array.isArray(out)) return null;
    const texts = [];
    for (const msg of out) {
        const content = msg?.content;
        if (!Array.isArray(content)) continue;
        for (const part of content) {
            if (typeof part?.text === "string" && part.text.trim()) { texts.push(part.text.trim()); continue; }
            if (typeof part?.value === "string" && part.value.trim()) { texts.push(part.value.trim()); continue; }
            if (part?.type === "json" && part?.json) { try { texts.push(JSON.stringify(part.json)); } catch { } }
        }
    }
    if (!texts.length) return null;
    return texts.join("\n").trim();
}

serve(async (req) => {
    // Handle CORS
    if (req.method === "OPTIONS") {
        return new Response("ok", { headers: corsHeaders });
    }

    try {
        const url = new URL(req.url);
        const { pathname } = url;

        // Create Supabase Client (Auth context is automatically handled if 'Authorization' header is present)
        const supabaseClient = createClient(
            Deno.env.get("SUPABASE_URL") ?? "",
            Deno.env.get("SUPABASE_ANON_KEY") ?? "",
            { global: { headers: { Authorization: req.headers.get("Authorization")! } } }
        );

        // --- 1. Root Check ---
        if (pathname === "/" || pathname === "/gpt-api") {
            return json({ message: "GTPinput Supabase Edge Function is running!" });
        }

        // --- 2. List Expenses ---
        if (pathname.endsWith("/list")) {
            const { data, error } = await supabaseClient
                .from("expenses")
                .select("*")
                .order("date", { ascending: false })
                .limit(200);

            if (error) throw error;
            return json({ ok: true, rows: data });
        }

        // --- 3. Add Expense (Text Parsing) ---
        if (req.method === "POST" && pathname.endsWith("/add")) {
            const body = await req.json();
            const text = String(body.text || "").trim();
            const source = body.source || "gpt";
            if (!text) return json({ detail: "text is required" }, 422);

            // OpenAI Parsing Logic
            const today = new Date().toISOString().slice(0, 10);
            const apiKey = Deno.env.get("OPENAI_API_KEY");
            if (!apiKey) return json({ error: "Missing OPENAI_API_KEY" }, 500);

            const schema = {
                type: "object",
                additionalProperties: false,
                required: ["items"],
                properties: {
                    items: {
                        type: "array",
                        items: {
                            type: "object",
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

            const aiBody = {
                model: "gpt-4o-mini",
                input: [
                    {
                        role: "system",
                        content: `Reference date: ${today}. Parse expense text to JSON {"items":[...]}. Rules: item is name (not number), amount is number. category one of: 餐饮/日用品/交通/服饰/医疗/娱乐/居住/其他 (use 其他 if unsure). note is null if missing.`
                    },
                    { role: "user", content: text }
                ],
                text: { format: { type: "json_schema", name: "expense_rows", schema, strict: true } },
                store: false
            };

            const aiRes = await fetch("https://api.openai.com/v1/responses", {
                method: "POST",
                headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
                body: JSON.stringify(aiBody)
            });

            if (!aiRes.ok) throw new Error(`OpenAI Error: ${aiRes.status}`);
            const aiJson = await aiRes.json();
            const outText = extractTextFromResponses(aiJson);
            if (!outText) throw new Error("No text from OpenAI");

            const parsed = JSON.parse(outText);
            const rows = parsed?.items || [];

            // Insert DB
            const inserts = rows.map((r: any) => ({
                date: r.date || today,
                item: r.item,
                amount: r.amount,
                category: r.category || "其他",
                note: r.note || null,
                source: source
                // user_id is automatically handled by RLS + Supabase Auth Header
            }));

            if (inserts.length > 0) {
                const { error: insError } = await supabaseClient.from("expenses").insert(inserts);
                if (insError) throw insError;
            }

            return json({ ok: true, inserted: inserts.length, rows: inserts });
        }

        // --- 4. Update Expense ---
        if (req.method === "POST" && pathname.endsWith("/update")) {
            const body = await req.json();
            const { id, ...updates } = body;
            if (!id) return json({ detail: "id is required" }, 422);

            const { error } = await supabaseClient
                .from("expenses")
                .update(updates)
                .eq("id", id);

            if (error) throw error;
            return json({ ok: true });
        }

        // --- 5. Delete Expense ---
        if (req.method === "POST" && pathname.endsWith("/delete")) {
            const body = await req.json();
            if (!body.id) return json({ detail: "id is required" }, 422);

            const { error } = await supabaseClient
                .from("expenses")
                .delete()
                .eq("id", body.id);

            if (error) throw error;
            return json({ ok: true });
        }

        // --- 6. Budget & Recurring (Simple CRUD) ---
        // Budget
        if (pathname.endsWith("/budget/list")) {
            const { data, error } = await supabaseClient.from("budgets").select("*");
            if (error) throw error;
            return json({ ok: true, rows: data });
        }
        if (req.method === "POST" && pathname.endsWith("/budget/add")) {
            const body = await req.json();
            const { error } = await supabaseClient.from("budgets").insert(body);
            if (error) throw error;
            return json({ ok: true });
        }
        if (req.method === "POST" && pathname.endsWith("/budget/delete")) {
            const body = await req.json();
            const { error } = await supabaseClient.from("budgets").delete().eq("id", body.id);
            if (error) throw error;
            return json({ ok: true });
        }

        // Recurring
        if (pathname.endsWith("/recurring/list")) {
            const { data, error } = await supabaseClient.from("recurring_rules").select("*").eq("active", true);
            if (error) throw error;
            return json({ ok: true, rows: data });
        }
        // ... Implement other recurring routes similarly if needed for full parity

        return json({ error: "Not Found" }, 404);

    } catch (error) {
        return json({ error: error.message }, 500);
    }
});
