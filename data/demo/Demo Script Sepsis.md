Yes. With sepsis as the demo domain, I’d update the script so **Slides 1–4 tell one continuous sepsis story**, the live demo proves it, and Slides 5–7 deliberately zoom out from sepsis to the enterprise opportunity.

I’d also make the **28 reports** a recurring motif. It gives the audience something concrete to remember.

# AIVIA Demo Script — Sepsis Version

> **Reviewed 2026-08-09 (Claude).** This is the LONG-FORM script (8–10
> min) — perfect for lead calls. The Marketplace listing video targets
> 4–5 min: use Slide 1 (30s) → Slide 3 (30s) → live demo beats 1+2+4
> incl. the report-link click (2.5 min) → Slide 5 flywheel (45s) →
> Slide 7 close (30s).
>
> **Hard rule for anything on camera: only QA-verified questions,
> word-for-word.** Verified set: docs/internal/DEMO_SCRIPT.md. New
> questions must pass a test-pane run (answer + run steps checked)
> BEFORE recording. Count questions ("how many...") stay OFF camera.

## Slide 1 — More Reports. Still No Answers.

### Suggested slide change

Instead of emphasizing generic “thousands of SQL reports,” show:

**28 Sepsis Reports**
*Thousands of lines of SQL. Dozens of definitions. Still hard to find the answer.*

The report piles could include:

**Sepsis Mortality · Sepsis Population · Septic Shock · Bundle Compliance · Time to Antibiotics · Length of Stay**

### Script

> Let me start with a real example from healthcare analytics: sepsis.
>
> For this demo, we have 28 reports covering different aspects of sepsis—mortality, bundle compliance, septic shock, length of stay, time to antibiotics, and many others.
>
> These aren't simple reports. Each one can contain hundreds or even thousands of lines of SQL.
>
> And yet, when someone asks a seemingly simple question—like, “How exactly are we defining our sepsis population?”—finding the answer can still be surprisingly difficult.
>
> The user searches existing reports. They find several that look relevant, but the logic may be slightly different. They aren't sure which one is authoritative.
>
> So they submit another request.
>
> An analyst investigates, writes more SQL, and eventually we create another report.
>
> And now we have 29.
>
> That's the cycle we've created over years of analytics development.
>
> **More reports have not necessarily created more understanding.**
>
> AIVIA was built to break that cycle.

### Transition

> But there's an important insight behind how we approach this problem:
>
> **we don't need to start documenting everything from scratch.**

---

# Slide 2 — Your Business Logic Is Already There.

### Suggested visual change

Replace the 30-day readmission example with a sepsis query containing multiple CTEs:

**28 Sepsis Reports**

→ magnifying glass →

```sql
WITH sepsis_population AS (...)
   , suspected_infection AS (...)
   , organ_dysfunction AS (...)
   , exclusions AS (...)
   , septic_shock AS (...)
   , bundle_compliance AS (...)
...
```

Highlight one CTE:

**sepsis_population → Sepsis Eligible Population**

### Script

> Because the knowledge we're looking for actually already exists.
>
> It's embedded in the SQL our analytics teams have been writing for years.
>
> And sepsis is a great example of why extracting that knowledge is difficult.
>
> These reports aren't just a SELECT statement and a few filters.
>
> A single report may have hundreds or thousands of lines of SQL, with many CTEs representing intermediate steps—patient populations, encounters, suspected infection, organ dysfunction, exclusions, septic shock, bundle compliance, mortality, and so on.
>
> To a business user, all of this looks like code.
>
> But every one of those steps represents something meaningful about how the organization thinks about sepsis.
>
> The filters represent business rules.
>
> The CASE statements represent definitions.
>
> The joins represent relationships.
>
> The CTEs often represent meaningful steps in a calculation.
>
> So across these 28 reports, we're actually sitting on a tremendous amount of institutional knowledge.
>
> **The knowledge exists. It's just trapped in code.**

### Transition

> And that's where AIVIA starts.

---

# Slide 3 — AIVIA Turns SQL Into Business Knowledge.

### Suggested visual change

Instead of generic SQL reports, I'd make the pipeline explicitly say:

**28 Sepsis Reports**

→ **Parse SQL**

→ **CTEs · Joins · Filters · Calculations · Dependencies**

→ **AI Translation**

→

**Sepsis Population**
**Septic Shock**
**Bundle Compliance**
**Time to Antibiotics**
**Sepsis Mortality**

### Script

> AIVIA starts by connecting to the analytics assets the organization already has.
>
> Our SQL parser then takes these complex reports and decomposes them into their logical components.
>
> It understands the structure of the query—the CTEs, joins, filters, calculations, dependencies, and how those pieces relate to one another.
>
> We then use AI to translate those technical components into plain-English business meaning.
>
> So something like a complex CTE buried hundreds of lines into a sepsis report can become an understandable business concept with its definition and underlying logic.
>
> And when we do this across all 28 reports, we begin reconstructing a knowledge layer around sepsis.
>
> We can identify concepts like sepsis population, septic shock, mortality, bundle compliance, time to antibiotics, and the logic associated with each of them.
>
> That's an important distinction in what AIVIA does.
>
> **We're not simply putting a chatbot on top of SQL.**
>
> We're first extracting and structuring the business knowledge that's buried inside it.

### Transition

> Once that knowledge has been extracted, we can completely change the way users interact with analytics.

---

# Slide 4 — Ask Your Data What It Means.

I would change this slide to match the **exact question you're going to type during the live demo**.

For example:

> **How is our sepsis population defined?**

If you have an even better first demo question, use that instead. The slide and demo should match word-for-word.

**Slide fixes (2026-08-09):**
1. **Remove the "Confidence ★★★★★ (High)" element** — the product
   deliberately never presents confidence as a rating (relative
   similarity is not a probability), and no stars exist in the UI.
2. **Redraw the answer card to mirror a real agent answer** (the live
   demo shows Fabric chat seconds later — the mock must match):
   business name + metric id header, description, Key Logic bullets,
   "Used in: ED Sepsis Screening Dashboard (link)", and the Basis
   line. Drop the "Related Reports (12)" / "Show lineage →" buttons —
   they don't exist.
3. **QA-GATE THE QUESTION**: "How is our sepsis population defined?"
   has NOT been test-pane verified yet. Before recording: ask it, check
   the answer is grounded and the run steps are clean. If it wobbles,
   fall back to the verified "How is ED Sepsis Screening calculated?"
   and adjust this slide + narration to match.

### Script

> Now let's look at this from the perspective of a healthcare business user.
>
> I don't want to understand 28 reports.
>
> I definitely don't want to read thousands of lines of SQL.
>
> I just have a question:
>
> **“How is our sepsis population defined?”**
>
> Today, answering that might mean searching through Power BI, finding several reports, asking an analyst which one is correct, or submitting a request.
>
> With AIVIA, I can simply ask the question in plain English.
>
> But what's important is that AIVIA doesn't just generate an answer.
>
> It can connect that answer back to the business logic we extracted, the SQL it came from, the reports where that logic is being used, and the surrounding metadata.
>
> So we're moving from **searching for reports** to **understanding what the organization actually means**.
>
> Let me show you.

## → SWITCH TO LIVE AIVIA DEMO

This transition should be immediate. Don't explain more.

---

# Live Demo — Sepsis Story

I would resist the temptation to show everything AIVIA can do.

Tell **one investigation from beginning to end.**

### 1. Start with the business question

Type the same question from Slide 4:

> **How is our sepsis population defined?**

Then say:

> I'm starting exactly where a business user would start—with the question, not with a report.

Let AIVIA answer.

---

### 2. Examine the definition

> Here AIVIA is giving me a plain-English explanation based on the business logic it discovered in our analytics environment.
>
> So I can understand the concept without knowing SQL.

Then point at the REAL evidence in the answer: the metric id beside
the business name, the "Used in: ED Sepsis Screening Dashboard" link
(click it — the report opens), and the Basis line stating what was
actually queried. Do NOT mention confidence scores — there are none.

> But in healthcare, an answer alone isn't enough.
>
> I need to understand why I should trust it.

---

### 3. Trace it back to SQL

Type exactly: **"show me the technical details as a developer"** —
the agent switches persona and returns calculation_logic (the SQL
steps), source tables, and dictionary descriptions.

> So I can trace this definition back to the actual reports and SQL that produced it.
>
> And remember, these queries can be hundreds or thousands of lines long.
>
> AIVIA has already decomposed that SQL into meaningful steps.

Show the CTE/parser view if possible.

> Here we can see those steps individually.
>
> Instead of treating this as one enormous SQL file, AIVIA understands the pieces of logic inside it and the relationships between them.

This is where your **parser becomes tangible**, rather than something you claimed on Slide 3.

---

### 4. Show that the same concept exists across reports

This could be one of your strongest demo moments if your product supports it.

> Now here's where this becomes especially interesting.
>
> We don't have one sepsis report. We have 28.
>
> So AIVIA can help us understand where the same—or similar—business concepts appear across those reports.

Type exactly (QA-verified wording, expected answer: 14 metrics):
**"What other metrics share source tables with reports.USP_ED_Sepsis?"**

> Now we're beginning to see something that was almost impossible to see when the knowledge was scattered across individual SQL files:
>
> **how the organization is actually defining and using a concept across its analytics estate.**

---

### 5. Governance integration

**For the recorded video: use the Purview screenshot** (from checklist
D.4's short-lived provision) rather than a live push — keeps the video
tight and avoids provisioning Purview on recording day. Live push is a
lead-call option.

If this is part of the live demo:

> And once we've identified a useful definition, we don't want that knowledge trapped inside AIVIA either.
>
> We can push these definitions into the organization's existing data governance ecosystem.
>
> So AIVIA isn't another isolated metadata repository.
>
> It's helping enrich the governance investments the organization already has.

Then switch back to slides.

### Transition back

> And there's one more important part of this model.
>
> What happens after people start using these definitions?

---

# Slide 5 — Every Question Makes Governance Better.

At this point, start with sepsis and then begin zooming out.

### Script

> Let's stay with our sepsis example for a moment.
>
> Suppose AIVIA discovered several candidate definitions related to the sepsis population across those 28 reports.
>
> Initially, simply extracting them doesn't necessarily tell us which definition is the most useful or most trusted.
>
> But then people begin interacting with them.
>
> Users search for a definition.
>
> They select one.
>
> They use it.
>
> They validate it or provide feedback.
>
> Each of those interactions becomes a signal.
>
> In AIVIA, when a definition is repeatedly used and validated, its weight can increase.
>
> Over time, trusted definitions can rise to the top. Search improves. Duplicates become easier to identify. And the knowledge base reflects how the organization is actually using its data.
>
> So now compare this to where we started.
>
> In the old cycle, **every unanswered question created another report.**
>
> With AIVIA, **every question can make the organization's shared knowledge better.**
>
> That's the flywheel.

That callback is worth emphasizing.

**Accuracy note (keep as written):** the "can increase" / "can rise"
modal phrasing is load-bearing — the flywheel is the product's designed
governance model (ADRs 0023/0031, contracts in the codebase); live
weight capture ships post-listing. Present the model, never simulate
weights on camera.

### Transition

> And once you have that flywheel, this becomes much bigger than sepsis.

---

# Slide 6 — Governance That Scales With Your Organization.

This is where you explicitly zoom out.

### Script

> So far I've shown you one domain: sepsis.
>
> But imagine applying the same approach across quality, finance, operations, population health, claims, clinical outcomes, and the rest of the enterprise.
>
> That's where we start addressing another fundamental problem with traditional data governance: scale.
>
> Most organizations have a relatively small number of dedicated data stewards.
>
> We're asking that small team to document and maintain the meaning behind an analytics estate being changed by hundreds or thousands of people.
>
> It's very difficult for a manual process to keep up.
>
> AIVIA changes that model.
>
> The governance team still provides oversight. They still establish standards and make important governance decisions.
>
> But the people who actually consume the data can now contribute signals through their normal work.
>
> Analysts, clinicians, operational leaders, and business users can help validate and improve the knowledge they use.
>
> We think of these users as **Citizen Data Stewards**.
>
> So instead of a handful of people trying to manually govern everything…
>
> **we can harness the collective usage of the organization while keeping centralized governance oversight.**
>
> That's how governance begins to scale with the business.

### Transition

> And to do this in a healthcare enterprise, the deployment model is critical.

---

# Slide 7 — Enterprise Governance Inside Your Azure Estate.

One caution: your generated Slide 7 contains specific security/compliance claims. Only verbally claim things such as **HIPAA, SOC 2, ISO 27001, CMK, private endpoints, row-level security, etc. if they accurately describe your current product/deployment**.

**REBUILD SLIDE 7 on the true story — it is stronger (2026-08-09):**
Remove: VNet/Private Endpoints/Managed Identity (not our deployment
model), SOC 2 / ISO 27001 / HIPAA badges (AIVIA holds no such
certifications), CMK/HA/DR presented as product claims. Replace with
five true bullets:
1. Runs entirely inside YOUR Microsoft Fabric workspace, on YOUR
   capacity — shipped as a library, not a vendor service.
2. Your data never reaches AIVIA: no vendor service, no vendor keys,
   nothing to breach on our side.
3. The only AI egress is YOUR OWN Azure OpenAI endpoint — with
   deterministic PHI redaction before any prompt is built.
4. Identity, RBAC, and row-level security inherited from YOUR Entra ID
   and Fabric.
5. Compliance posture inherited from YOUR Microsoft cloud boundary
   (your tenant's certifications govern — we never take data outside
   them).
Keep the "Available on Microsoft Marketplace" footer.

### Script

> Everything I've shown you today was designed with enterprise deployment in mind.
>
> A core principle of AIVIA's architecture is that **the customer's data remains inside the customer's Azure environment.**
>
> AIVIA runs inside your Microsoft Fabric workspace and works with the analytics infrastructure enterprises already use—SQL Server, Power BI, and Microsoft Fabric today, with dbt, semantic models, and Databricks on our roadmap.
>
> We also don't believe customers should have to replace their existing governance investments.
>
> AIVIA can enrich those systems by pushing the definitions and knowledge we've discovered into platforms such as Microsoft Purview and other enterprise governance tools.
>
> So you can think of AIVIA as an intelligence layer connecting three things that have historically been disconnected:
>
> **the analytics code your organization has already written,**
>
> **the business meaning hidden inside that code,**
>
> **and the governance ecosystem responsible for managing that meaning.**
>
> And our goal in bringing AIVIA to Microsoft Marketplace is to make that capability straightforward for enterprise Microsoft customers to procure and deploy.

---

# Closing — bring the audience back to the 28 reports

I would **not finish with “Any questions?” immediately after Slide 7**.

Take another 30–45 seconds and complete the story.

> Let me bring this back to where we started.
>
> We started with 28 sepsis reports.
>
> Thousands of lines of SQL.
>
> Years of work by analysts.
>
> And yet a business user could still struggle to answer a simple question:
>
> **“How do we define our sepsis population?”**
>
> The traditional answer to that problem has often been to build report number 29.
>
> AIVIA takes a different approach.
>
> We use the work you've already done.
>
> We extract the business logic already embedded in your SQL.
>
> We translate it into language people can understand.
>
> We make it searchable, traceable, and reusable.
>
> And then we allow the people who use that knowledge to continuously make it better.
>
> **So instead of creating more reports, we're creating shared understanding.**
>
> That's AIVIA.

I think that last sentence should be your closing line. It resolves the exact problem introduced on Slide 1 without drifting into generic “AI-powered enterprise data governance” language.

One other change I'd make to the actual slides now: **Slides 1–4 should visually use sepsis, but Slides 5–7 should remain mostly as they are.** That gives the presentation a deliberate camera movement: **one concrete problem → proof in the live demo → enterprise-scale implication.**
