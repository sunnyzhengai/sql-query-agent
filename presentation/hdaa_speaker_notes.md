# Speaker Notes
## The Full Circle: From SQL Chaos to Self-Service AI Agent
## HDAA Annual Conference | November 2026

---

## SLIDE 1 — Title Slide

Welcome everyone. I'm Sunny Zheng, and today I want to talk about something that I think every data and analytics team in healthcare struggles with — the tension between governance and getting work done.

The title is "The Full Circle" because what I'm going to show you is not a one-way pipeline. It's a system where the more people use it, the better it gets. And the governance? It happens automatically. Nobody has to stop what they're doing.

---

## SLIDE 2 — About the Speaker

A little about me — I lead BI in healthcare, and I've spent my career in SQL, data warehousing, and trying to make data trustworthy and accessible. We work in the Microsoft Fabric ecosystem — Power BI, Data Agent, Notebooks.

But the thing that keeps me up at night isn't the technology. It's this challenge on the right: we have over a thousand reports and queries, business logic is scattered everywhere, and our users are waiting weeks for answers. And every time we try to govern our way out of it, we just slow everyone down more.

---

## SLIDE 3 — Agenda

Here's what we'll cover today. I'll start with the problem — why governance feels like a tax on your team. Then the big idea: what if usage itself drove governance? I'll walk through how we build the foundation, how the flywheel works, and then I'll share a real case study — First Case On Time Start — that shows how this plays out in practice with surgeons. We'll wrap with ROI and lessons learned.

---

## SLIDE 4 — The Problem

Sound familiar? Raise your hand if you've heard "Can you pull me the readmission rate?" and you know it's going to take six weeks because you've got 40 requests ahead of it.

Or this one — three analysts run the same metric, and the CFO gets three different numbers. Now nobody trusts any of them.

And here's the worst part: governance is supposed to fix this. But in practice, governance is a committee that meets monthly, maintains a spreadsheet, and creates definitions that nobody actually uses in their reports. So governance falls behind, definitions go stale, and trust erodes even further.

Look at the cycle on the right. Governance is slow, so people work around it. That makes definitions stale. Trust declines. So what do we do? Impose MORE governance. And the cycle repeats. We need to break this cycle entirely.

---

## SLIDE 5 — The Big Idea

Here's the idea that changed everything for us.

What if every question a user asks makes your data foundation stronger?

Instead of governance being a gate that people have to pass through — and usually walk around — what if governance was something that grew naturally from people just doing their jobs?

That's what the full circle is about. Every question either reinforces something we already know — which makes it more visible — or it surfaces something we don't know yet — which triggers a review. Both outcomes make the system better. There's no wasted question.

And here's the key: governance becomes invisible to the end user. They're just asking questions. They don't know they're participating in governance. And that's exactly how it should be.

---

## SLIDE 6 — Section Divider: Building the Foundation

Before the flywheel can spin, you need a starting point. You need to seed the knowledge base. The good news? You already have the raw material.

---

## SLIDE 7 — The Foundation

Here's what most people don't realize: your existing reports and queries already contain the business logic. It's just buried in SQL code that nobody reads.

We scan those queries automatically, extract the logic, and AI drafts plain-English definitions. Your team reviews in bulk — not one at a time — and stewards certify the business meaning.

Look at the example on the right. One OR Efficiency Dashboard yields three candidate metrics: First Case On Time Start, Turnover Time, Case Duration Accuracy. Each one linked back to its source tables. Each one sent to a steward for review.

This is how you go from zero to 50+ certified metrics without spending a year in committee meetings.

---

## SLIDE 8 — Knowledge Base Structure

The knowledge base has three layers, and this is important because it's what makes the answers traceable.

At the top: business metrics. Things like "First Case On Time Start." Each one owned by a steward, and weighted by how often people ask about it.

In the middle: the calculation logic. The step-by-step math behind each metric. These are small, reusable pieces — not giant SQL blocks. That's important because it means we can audit each step individually.

At the bottom: the source data. The actual tables and columns, enriched with plain-English descriptions so people understand what they're looking at.

When someone asks a question, the agent traces a path from top to bottom and back. Every answer is traceable to its source. No black boxes.

---

## SLIDE 9 — Section Divider: The Flywheel

Now here's where it gets interesting. The foundation is just the seed. What makes it a full circle is the flywheel.

---

## SLIDE 10 — Flywheel Overview

Here's the flywheel. A user asks a question. The agent answers. The knowledge base grows. Which means better answers. Which means more users ask questions. And the cycle continues.

Notice what's NOT in this diagram: governance committees, spreadsheets, project proposals, monthly review meetings. The knowledge base grows because people use it. That's it.

This is the "full circle" in the title. It's not a one-time project. It's a self-reinforcing loop that gets stronger over time.

---

## SLIDE 11 — Two Paths

When someone asks a question, one of two things happens, and both are good.

Path A: we already know this. The answer exists in our certified knowledge base. The user gets an instant, accurate answer. And the metric gains weight — we now know it's important. The most-asked metrics become visible to leadership, and eventually get promoted to dashboards.

Path B: we don't know this yet. The agent says "I don't have that yet." Now, in most systems, that's a dead end. In our system, it's a trigger. A request goes to the steward. The steward reviews and certifies. The new metric gets added. And next time anyone asks, Path A handles it.

Both paths make the system better. There is no wasted question. That's the key insight.

---

## SLIDE 12 — Section Divider: Case Study

Let me show you what this looks like in practice with a real example.

---

## SLIDE 13 — FCOTS: The Story

First Case On Time Start — FCOTS. It's a straightforward metric: what percentage of first surgical cases start on time?

Three years ago, our rate was just over 20%. That's painful. Four out of five first cases starting late, cascading delays through the rest of the day.

Today we're at 60%. And our goal is 90%+. We've been working closely with the Surgery Medical Director to drive this improvement.

And here's the thing — this improvement was only possible because everyone trusted the same number. One certified definition, one source of truth, consistent tracking over time. No one could argue "well, that depends on how you define on time." The definition was certified. Period.

---

## SLIDE 14 — FCOTS: Self-Service + Security

But here's where it gets interesting, and this is why self-service matters.

The Medical Director has a challenge. He needs to have 1:1 conversations with individual surgeons about their FCOTS performance. But this is sensitive data. You can't just put a dashboard on the wall showing everyone's on-time percentage. Surgeons would revolt.

So here's our solution: surgeons ask the Data Agent "What's my FCOTS rate?" And they only see their own data. Built-in security. Dr. Smith sees 78%. Dr. Jones sees 62%. The Medical Director asks for the department view and gets 68% overall with trends.

Same certified metric. Same source of truth. But personalized, private access. No IT ticket required. No privacy concerns. The surgeon doesn't need to ask anyone for permission or wait for someone to pull the data. They just ask.

---

## SLIDE 15 — FCOTS: Full Circle in Action

Now watch the flywheel spin with FCOTS.

Surgeons start asking about their FCOTS. Great — Path A. The metric gains weight.

But then some surgeons ask new questions. "What's my average delay time?" "Which rooms start late most?" "Is it worse on Mondays?" These are Path B — the agent doesn't know yet. So it triggers steward review.

The steward certifies "average delay time." Then "room-level start time." Then "day-of-week pattern." Within months, what started as one metric — FCOTS — has grown into a full OR efficiency suite. And it happened because surgeons asked questions. Not because we ran a governance project.

On the right you can see the growth: start with 1 metric, by month 6 you have a comprehensive OR efficiency knowledge base. All demand-driven.

---

## SLIDE 16 — Section Divider: The Growing Knowledge Base

The FCOTS example is one department. Now imagine this happening across your entire organization.

---

## SLIDE 17 — Growth Over Time

Here's what the growth looks like over time.

Month 1: you seed the knowledge base from your existing reports. Maybe 50 certified metrics.

Month 3: users are asking questions. Some are Path A — the knowledge base already knows. Some are Path B — new certifications. You're at 80.

Month 6: the steward queue is processing demand-driven requests. You're at 140.

Month 12: the flywheel is mature. 250+ certified metrics and still growing.

Compare that to traditional governance. Committees, spreadsheets, quarterly reviews — you're lucky to certify 50 definitions a year. The flywheel does 250+ and it's accelerating.

---

## SLIDE 18 — Why It Accelerates

Why does it accelerate? Network effects.

More certified metrics means the agent can answer more questions. Which means more people trust it and start using it. Which means more questions — both known and new. More new questions means more certifications. More certifications means even more the agent knows.

Look at the coverage numbers on the right. Week 1, most questions are new — the agent says "I don't have that yet" a lot. By month 3, 80% of questions get instant answers. By month 12, 95%.

And here's the beautiful part: steward workload actually decreases over time. Early on, they're certifying a lot of new metrics. But as coverage grows, fewer and fewer questions are new. The flywheel is self-stabilizing.

---

## SLIDE 19 — Section Divider: Delivering Value

So how do users actually experience this? Through two channels that work together.

---

## SLIDE 20 — Self-Service + Dashboards

This is not either/or. The Data Agent and Power BI dashboards complement each other.

The agent handles ad-hoc questions. "What's my FCOTS?" "What was the readmission rate last quarter?" No ticket, no wait, answers in seconds. And each user only sees what they're authorized to see.

Dashboards handle the recurring stuff. Executive views, monthly KPI reports, department scorecards. But here's the difference: dashboards are now built from the same certified knowledge base. The numbers always match what the agent says. No more "the dashboard says 4.2 but I was told 3.8."

And here's my favorite part: usage data from the agent tells you which dashboards to build. When FCOTS gets asked 100 times in a month, that's your signal — build a dashboard. No more guessing. No more building reports nobody looks at. Usage drives prioritization.

---

## SLIDE 21 — Section Divider: Measuring the Impact

Let's talk about the numbers.

---

## SLIDE 22 — Quantitative ROI

Four metrics that matter.

Knowledge base coverage: from 50 seed metrics to 250+ in a year. All driven by actual demand.

Instant answer rate: from 40% in week 1 to 95% at month 12. That's 95% of questions answered on the spot, no waiting.

Time to answer: from weeks — submitting a ticket, waiting in the queue — to seconds. For the user, this is the most visible change.

Steward efficiency: 10x. Not because stewards work harder, but because they're reviewing demand-driven requests with full context, not processing a backlog of committee submissions.

And every one of these numbers improves with time. The flywheel compounds.

---

## SLIDE 23 — Before & After

Let me paint the picture.

Before: "Which LOS number is right?" Three analysts, three answers. Six-week backlog. Governance is a committee that meets monthly. New metrics require a project proposal. Nobody knows what's been asked before.

After: "Here's the certified ER LOS — asked 347 times this quarter." One metric, one definition, traceable to source. Ad-hoc answers in seconds. Dashboards for the top metrics. Governance happens automatically. New metrics certified in days. And usage data shows exactly what the organization cares about.

That's the transformation. Not a technology upgrade — a fundamentally different relationship between governance and getting work done.

---

## SLIDE 24 — Lessons Learned

Six lessons, quickly.

One: start with what you have. Don't build a governance catalog from scratch. Your existing reports already contain the business logic — extract it.

Two: "I don't know" is a feature, not a failure. In healthcare especially, a wrong answer is dangerous. But "I don't know" triggers the process that fills the gap. It's the most productive answer the agent can give.

Three: let usage drive prioritization. Stop guessing which metrics matter. Let the question volume tell you. Build dashboards for what people actually ask about.

Four: make governance invisible. If people have to stop working to do governance, they won't do it. When asking a question IS the governance process, everyone participates without knowing it.

Five: security enables trust. When surgeons can only see their own data, they trust the system and use it more. More usage means faster flywheel growth.

Six: the flywheel compounds. Month 1 is hard. Month 12 is transformative. The early investment pays exponential returns.

---

## SLIDE 25 — Key Takeaways

Four things I want you to walk away with.

One: your existing reports are an untapped asset. The business logic is already there. Extract it at scale.

Two: usage is the best governance signal you have. Every question either reinforces a known metric or surfaces a new one. Both make the system better.

Three: self-service and governance can be the same thing. When asking a question IS the governance process, everyone participates without even knowing it.

Four: the full circle compounds. From one FCOTS metric to a full OR efficiency suite — demand-driven growth that accelerates itself.

---

## SLIDE 26 — Thank You / Q&A

Thank you. I'd love to hear your questions — especially if you're dealing with similar challenges in your organization. I'm happy to go deeper on any part of this, whether it's the technical architecture, the steward workflow, or how to get started with a pilot.
