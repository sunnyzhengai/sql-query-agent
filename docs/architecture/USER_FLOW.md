# User Flow

How questions move through the system — from user input to answer delivery.

## The Flywheel

Every question makes the system better. There are no wasted questions.

```
                    ┌──────────────┐
                    │  USER ASKS   │
                    │  A QUESTION  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ DOES CERTIFIED│
                    │ PATH EXIST?  │
                    └──┬───────┬───┘
                       │       │
                  YES  │       │  NO
                       │       │
              ┌────────▼──┐  ┌─▼──────────┐
              │  PATH A   │  │  PATH B    │
              │  Answer   │  │  "I don't  │
              │  from     │  │  have that │
              │  graph    │  │  yet"      │
              └────┬──────┘  └─┬──────────┘
                   │           │
                   │           ▼
                   │     Steward notified
                   │           │
                   │           ▼
                   │     Steward certifies
                   │           │
                   │           ▼
                   │     New node added
                   │     to graph
                   │           │
                   ▼           ▼
              ┌────────────────────┐
              │  GRAPH GROWS       │
              │  (more coverage,   │
              │   better answers)  │
              └────────────────────┘
```

## Path A: Known Logic (Certified Path Exists)

The knowledge graph has a certified answer for this question.

### Step-by-step

1. **User asks a question**
   - "What is the average ER length of stay this quarter?"

2. **Agent searches the knowledge graph**
   - Finds canonical node: `ER_LOS` (ER Length of Stay)
   - Certified by steward: Dr. Smith
   - Certified by developer: jane.doe

3. **Agent traverses the transformation chain**
   - CTE step 1: `er_visits` — filter encounters to Emergency department
   - CTE step 2: `los_calc` — compute hours between admit and discharge
   - Each step stored as a minimal sql_fragment

4. **Agent assembles and executes the query**
   - Combines sql_fragments into a complete query
   - Applies dimension filters (e.g., date_range = this quarter)
   - Executes against source tables: `encounter`, `department`

5. **Agent checks Purview for existing reports**
   - Searches Purview catalog for reports covering ER_LOS
   - If found: "The Monthly ED Dashboard already tracks this — [link]"
   - If not found: noted as a candidate for future dashboard

6. **Agent returns the answer**
   - Answer: 4.2 hours (with full lineage showing source tables, logic steps, and certifier)
   - Optional: link to existing dashboard

7. **Usage weight incremented**
   - ER_LOS canonical node gains +1 query count
   - Over time, most-asked metrics float to the top
   - High-demand metrics get promoted to formal dashboards

### What usage weight reveals

| Pattern | Signal | Action |
|---------|--------|--------|
| High weight | Org priority | Build a dashboard |
| Trending up | Emerging concern | Investigate why |
| Seasonal spikes | Predictable demand | Pre-build reports |
| Cross-department | Shared definition needed | Align with stewards |
| Declining weight | May be stale | Flag for review |

## Path B: Unknown Logic (No Certified Path)

The knowledge graph does not have a certified answer. The agent refuses to guess.

### Step-by-step

1. **User asks a question**
   - "What is the average surgical turnover time?"

2. **Agent searches the knowledge graph**
   - No canonical node found for "surgical turnover time"

3. **Agent responds honestly**
   - "I don't have a certified definition for surgical turnover time yet."
   - "I've sent a request to the data steward to review this."

4. **Agent still checks Purview**
   - Even without a certified graph path, Purview may have an existing report
   - If found: "I can't calculate this from certified logic, but the OR Efficiency Dashboard may have what you need — [link]"

5. **Steward notification triggered**
   - The question is logged with context:
     - What was asked
     - Who asked it
     - When it was asked
     - How many times similar questions have been asked

6. **Two-stage certification**
   - **Developer review:** Is the proposed SQL logic technically correct?
   - **Steward review:** Is this the right business definition? Approved for enterprise use?

7. **Graph updated**
   - New canonical node added (e.g., `SURG_TURNOVER`)
   - Transformation nodes wired to source tables
   - Next time anyone asks about surgical turnover time, Path A handles it

## Path A + Security: Personalized Access

Some metrics require row-level security — the same question returns different data depending on who asks.

### Example: FCOTS (First Case On Time Start)

```
Dr. Smith asks: "What's my FCOTS rate?"
  → Agent filters to Dr. Smith's cases only
  → Answer: 78% (your cases)

Dr. Jones asks: "What's my FCOTS rate?"
  → Agent filters to Dr. Jones's cases only
  → Answer: 62% (your cases)

Medical Director asks: "Show me department FCOTS"
  → Agent returns department aggregate
  → Answer: 68% overall + individual trends
```

**How it works:**
- Same certified metric (FCOTS) in the knowledge graph
- Same sql_fragments and transformation chain
- Dimension filter applies user identity to scope the result
- Each user only sees data they are authorized to see

**Why it matters:**
- Individual surgical performance is sensitive data
- Medical Director needs 1:1 coaching conversations with surgeons
- Can't put a dashboard on the wall with everyone's numbers
- Self-service access eliminates IT as a bottleneck while maintaining privacy

## The Flywheel Effect Over Time

```
Month 1:    [████░░░░░░░░░░░░░░░░]  50 metrics (seeded from existing SQL)
Month 3:    [████████░░░░░░░░░░░░]  80 metrics (user questions add 30)
Month 6:    [██████████████░░░░░░]  140 metrics (steward queue drives 60 more)
Month 12:   [████████████████████]  250+ metrics (flywheel mature)
```

- **Week 1:** Most questions hit Path B ("I don't have that yet")
- **Month 3:** 80% of questions hit Path A (instant answers)
- **Month 12:** 95% hit Path A (comprehensive knowledge base)
- **Steward workload decreases** as coverage grows — fewer new questions over time

## Dual Delivery: Agent + Dashboards

The agent and Power BI dashboards serve different needs from the same foundation.

```
                ┌───────────────────────┐
                │  Certified Knowledge  │
                │  Graph (Delta Tables) │
                └───────────┬───────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
       ┌────────▼────────┐    ┌─────────▼────────┐
       │  Data Agent     │    │  Power BI        │
       │                 │    │  Dashboards      │
       │  Ad-hoc Qs      │    │  Recurring KPIs  │
       │  Seconds         │    │  Exec views     │
       │  Personalized   │    │  Shared          │
       │  Exploration    │    │  Scheduled       │
       └─────────────────┘    └──────────────────┘
```

| | Data Agent | Dashboards |
|---|---|---|
| **Best for** | Ad-hoc questions, exploration | Recurring KPIs, executive views |
| **Speed** | Seconds | Scheduled refresh |
| **Access** | Personalized (row-level) | Shared views |
| **Signal** | When asked 100+ times → build a dashboard | Built from highest-weight metrics |

**The promotion signal:** When a metric gets asked 100+ times through the agent, that's the signal to build a formal dashboard. Usage drives prioritization — no more guessing which reports to build.
