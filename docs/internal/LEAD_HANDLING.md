# Lead Handling — Contact Me Listing

**Purpose:** when a Marketplace lead arrives, this is the process and
the words. Target: first response within **2 business days** (that's
also the expectation we state publicly on the listing).

## The flow

1. Lead arrives (Partner Center → Referrals workspace; email
   notification to founder@). 
2. Send the **first-response email** (template below) within 2 business
   days — it carries the qualification questionnaire.
3. Answers come back → grade with the **qualification rubric** →
   qualified leads get the scheduling link for a 30-minute intro call.
4. After the call, qualified + committed → send the deployment package
   (`scripts/build_deployment_package.py` output) + INSTALLATION_GUIDE;
   book the guided install session.
5. Log every lead and outcome (spreadsheet is fine until volume says
   otherwise): date, org, source, stage, next action.

Escalation: support@ forwards to founder; anything ambiguous gets a
human reply the same day it's read — never silence.

---

## First-response email (template)

> Subject: AIVIA SQL Intelligence Agent — next steps
>
> Hi <name>,
>
> Thanks for your interest in the SQL Intelligence Agent. To make our
> first conversation useful, could you share quick answers to five
> questions?
>
> 1. Do you run Microsoft Fabric today, and on what capacity (F2, F64,
>    trial)? If not yet, is Fabric on your roadmap?
> 2. Roughly how many SQL stored procedures/views power your reporting
>    (dozens / hundreds / thousands), and are they T-SQL (SQL Server /
>    Azure SQL / Fabric warehouse)?
> 3. Do you have a data dictionary (table and column descriptions) in
>    any form — spreadsheet, catalog tool, wiki?
> 4. Do you have (or can you create) an Azure OpenAI resource in your
>    tenant? The product uses YOUR endpoint — your SQL never leaves
>    your environment.
> 5. What outcome matters most: documenting existing logic, a
>    plain-English Q&A agent for the business, governance/catalog
>    publishing, or all three?
>
> Based on your answers I'll send tailored materials and, if it looks
> like a fit, a link to book a 30-minute walkthrough with a live
> environment.
>
> Sunny Zheng — AIVIA · aiviaapp.com

## Qualification rubric

| Signal | Qualified | Nurture (not yet) |
|---|---|---|
| Fabric | Running, any capacity — or trial active | "Evaluating Fabric" with no timeline |
| SQL estate | T-SQL, ≥50 objects | Non-T-SQL only (Oracle/Snowflake → roadmap list, tell them honestly) |
| Dictionary | Exists in any form | None and unwilling — set expectations (mandatory, ADR 0014) |
| Azure OpenAI | Can provision | Blocked by policy → note the blocker, offer whitepaper |
| Outcome | Named a concrete pain | "Just browsing" |

3+ qualified signals → scheduling link. Fewer → send whitepaper +
installation guide, check back in 30 days.

## Scheduling link

- [ ] Create a Microsoft Bookings page (included in the M365 tenant;
      alternative: Calendly free) — 30-minute slot, "AIVIA product
      walkthrough", buffer 15 min, next-3-weeks window.
- [ ] Paste the URL here when created: ______

## Listing support statement (goes in the offer's support section)

> Support: support@aiviaapp.com — responses within 2 business days.
> Documentation, security whitepaper, and installation guide at
> aiviaapp.com.
