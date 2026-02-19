
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

        // Create Supabase Client (Service Role - Bypass RLS)
        // Note: We do NOT pass the user's Authorization header here because GPT sends a non-Supabase token.
        const supabaseClient = createClient(
            Deno.env.get("SUPABASE_URL") ?? "",
            Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
        );

        // Helper to get the primary user ID (since we are in Service Role mode)
        // We assume this is a single-user app for now. 
        // Improvement: Pick the user who signed in most recently.
        const { data: { users }, error: userError } = await supabaseClient.auth.admin.listUsers();
        if (userError || !users || users.length === 0) {
            return json({ error: "No users found in Supabase Auth. Please sign up at least one user." }, 500);
        }

        // Sort by last_sign_in_at desc
        users.sort((a: any, b: any) => {
            const tA = new Date(a.last_sign_in_at || 0).getTime();
            const tB = new Date(b.last_sign_in_at || 0).getTime();
            return tB - tA;
        });

        const ownerId = users[0].id; // Use the most active user
        console.log(`Using user: ${users[0].email} (Last seen: ${users[0].last_sign_in_at})`);

        // --- 1. Root Check ---
        if (pathname === "/" || pathname === "/gpt-api") {
            return json({ message: "GTPinput Supabase Edge Function is running!" });
        }

        // --- 2. List Expenses ---
        // --- 2. List Expenses ---
        // Fix: Ensure we don't accidentally catch /budget/list or /recurring/list
        if (pathname.endsWith("/list") && !pathname.includes("/budget") && !pathname.includes("/recurring")) {
            const { data, error } = await supabaseClient
                .from("expenses")
                .select("*")
                .eq("user_id", ownerId) // Explicitly filter by ownerId
                .order("date", { ascending: false })
                .limit(200);

            if (error) throw error;
            return json({ ok: true, rows: data });
        }

        // --- 3. Add Expense (Text Parsing) ---
        // Fix: Ensure we don't accidentally catch /budget/add or /recurring/add
        if (req.method === "POST" && pathname.endsWith("/add") && !pathname.includes("/budget") && !pathname.includes("/recurring")) {
            const body = await req.json();
            const text = String(body.text || "").trim();
            const source = body.source || "gpt";
            // Use user-provided date or fallback to server time (UTC)
            const today = body.date ? String(body.date).slice(0, 10) : new Date().toISOString().slice(0, 10);

            if (!text) return json({ detail: "text is required" }, 422);

            // OpenAI Parsing Logic
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
            const items = parsed?.items || [];

            // Insert DB
            const inserts = items.map((r: any) => ({
                date: r.date || today,
                item: r.item,
                amount: r.amount,
                category: r.category || "其他",
                note: r.note ? `🤖 ${r.note}` : "🤖 定制GPT记录",
                source: source,
                user_id: ownerId // Explicitly set user_id
            }));

            if (inserts.length > 0) {
                const { error: insError } = await supabaseClient.from("expenses").insert(inserts);
                if (insError) throw insError;
            }

            return json({ ok: true, inserted: inserts.length, rows: inserts });
        }

        // --- 4. Update Expense ---
        if (req.method === "POST" && pathname.endsWith("/update") && !pathname.includes("/budget") && !pathname.includes("/recurring")) {
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
        if (req.method === "POST" && pathname.endsWith("/delete") && !pathname.includes("/budget") && !pathname.includes("/recurring")) {
            const body = await req.json();
            if (!body.id) return json({ detail: "id is required" }, 422);

            const { error } = await supabaseClient
                .from("expenses")
                .delete()
                .eq("id", body.id);

            if (error) throw error;
            return json({ ok: true });
        }

        // --- 6. Budget (Upsert) ---
        if (pathname.endsWith("/budget/list")) {
            const { data, error } = await supabaseClient.from("budgets").select("*").eq("user_id", ownerId);
            if (error) throw error;
            return json({
                ok: true,
                rows: data,
                _debug_user_email: users[0].email,
                _debug_user_id: ownerId,
                _debug_candidates: users.slice(0, 3).map((u: any) => ({ email: u.email, last_seen: u.last_sign_in_at }))
            });
        }
        if (req.method === "POST" && pathname.endsWith("/budget/add")) {
            const body = await req.json();
            const { category, amount, name, icon } = body;

            // Check existing
            const { data: existing } = await supabaseClient
                .from("budgets")
                .select("id")
                .eq("user_id", ownerId)
                .eq("category", category)
                .maybeSingle();

            if (existing) {
                // Update
                const { error } = await supabaseClient
                    .from("budgets")
                    .update({ amount, name, icon })
                    .eq("id", existing.id);
                if (error) throw error;
            } else {
                // Insert
                const { error } = await supabaseClient
                    .from("budgets")
                    .insert({ ...body, user_id: ownerId }); // Ensure user_id
                if (error) throw error;
            }
            return json({ ok: true });
        }
        if (req.method === "POST" && pathname.endsWith("/budget/delete")) {
            const body = await req.json();
            const { error } = await supabaseClient.from("budgets").delete().eq("id", body.id);
            if (error) throw error;
            return json({ ok: true });
        }

        // --- 7. Recurring (Subscriptions) ---
        if (pathname.endsWith("/recurring/list")) {
            const { data, error } = await supabaseClient
                .from("recurring_rules")
                .select("*")
                .eq("user_id", ownerId)
                .eq("active", true);
            if (error) throw error;
            return json({ ok: true, rows: data });
        }
        if (req.method === "POST" && pathname.endsWith("/recurring/add")) {
            const body = await req.json();
            // Expected body: { name, amount, category, frequency, start_date }
            // Derived: day (from start_date)
            // Default frequency: Monthly
            const freq = body.frequency || "Monthly";
            let day = 1;

            if (body.start_date) {
                const d = new Date(body.start_date);
                if (!isNaN(d.getTime())) {
                    if (freq === "Weekly") {
                        // 0=Mon, 6=Sun in Python version? Javascript getDay() 0=Sun. 
                        // Let's match Python version standard if possible or just use day of month
                        // Python weekday(): Mon=0. JS getDay(): Sun=0, Mon=1.
                        // Let's store JS getDay() for simplicity in Edge Function or convert?
                        // The internal app uses: day_val = start_date.weekday() (0=Mon).
                        // Let's try to align.
                        const jsDay = d.getDay(); // 0=Sun, 1=Mon...
                        day = (jsDay + 6) % 7; // Convert to 0=Mon, 6=Sun
                    } else {
                        day = d.getDate();
                    }
                }
            }

            const payload = {
                user_id: ownerId,
                name: body.name,
                amount: body.amount,
                category: body.category || "其他",
                frequency: freq,
                day: day,
                active: true,
                // created_at auto handled
            };

            const { error } = await supabaseClient.from("recurring_rules").insert(payload);
            if (error) throw error;
            return json({ ok: true });
        }
        if (req.method === "POST" && pathname.endsWith("/recurring/delete")) {
            const body = await req.json();
            const { error } = await supabaseClient.from("recurring_rules").delete().eq("id", body.id);
            if (error) throw error;
            return json({ ok: true });
        }

        return json({ error: "Not Found" }, 404);

    } catch (error) {
        return json({ error: error.message }, 500);
    }
});
