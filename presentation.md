# Smart Grocery Price Comparator
## Code Presentation

---

## Slide 1: Project Overview

**What is it?**
A Streamlit web application that compares grocery prices across 5 major South African stores — Checkers, Pick n Pay, Woolworths, Shoprite, and SPAR — and finds the cheapest basket for the user.

**Key Capabilities:**
- Two input modes: browse from catalog or type a free-text list
- Side-by-side price comparison across all 5 stores
- Identifies the cheapest single-store basket AND the cherry-pick strategy (cheapest store per item)
- Suggests money-saving substitute products
- Generates downloadable PDF comparison reports
- Saves lists to session for later reference

---

## Slide 2: Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | **Streamlit** | Web UI framework with reactive widgets |
| Data | **Pandas** | DataFrames for price aggregation, pivoting, grouping |
| AI Pipeline | **LangGraph** (LangChain) | Multi-agent state graph orchestration |
| Agent Tools | **LangChain `@tool`** | Decorated Python functions the agents invoke |
| Fuzzy Matching | **`difflib.get_close_matches`** | Match user input to catalog items even with typos |
| PDF Export | **fpdf2** | Programmatic PDF report generation |
| Styling | **Custom CSS** (Inter font) | Polished, modern UI design |

---

## Slide 3: Architecture Overview

```
┌─────────────────────────────────────────────┐
│              Streamlit Frontend              │
│  (Hero banner, Sidebar, Tabs, KPI cards)    │
├────────────┬────────────────────────────────┤
│ Manual Mode│       Smart Input Mode         │
│ (Dropdown  │    (Free-text grocery list)    │
│  + Qty)    │            │                   │
│     │      │            ▼                   │
│     │      │   ┌─────────────────────┐      │
│     │      │   │  LangGraph Pipeline │      │
│     │      │   │                     │      │
│     │      │   │  Normalizer Node    │      │
│     │      │   │       ▼             │      │
│     │      │   │  Price Fetcher Node │      │
│     │      │   │       ▼             │      │
│     │      │   │  Optimizer Node     │      │
│     │      │   │       ▼             │      │
│     │      │   │  Recommender Node   │      │
│     │      │   └─────────────────────┘      │
│     │      │            │                   │
│     ▼      │            ▼                   │
├────────────┴────────────────────────────────┤
│           Shared Results Dashboard          │
│  (Comparison, Best Prices, Charts, PDF)     │
└─────────────────────────────────────────────┘
```

---

## Slide 4: Data Layer — Store Catalog

```python
# app.py lines 16-77
STORE_CATALOG = {
    "Checkers":   { "Milk (1L)": 18.99, "Bread (White)": 16.49, ... },
    "Pick n Pay": { "Milk (1L)": 17.99, "Bread (White)": 17.49, ... },
    "Woolworths": { "Milk (1L)": 22.99, "Bread (White)": 21.99, ... },
    "Shoprite":   { "Milk (1L)": 16.99, "Bread (White)": 14.99, ... },
    "SPAR":       { "Milk (1L)": 19.49, "Bread (White)": 15.99, ... },
}
```

- **5 stores**, each with **30 products** and realistic ZAR prices
- Products range from staples (milk, bread, eggs) to proteins (chicken, mince) to pantry items
- A separate `SUBSTITUTES` dictionary maps expensive items to cheaper alternatives with reasons

---

## Slide 5: Data Processing Functions

Four core functions power all comparisons:

| Function | What It Does | How |
|----------|-------------|-----|
| `get_prices_for_items()` | Builds a price DataFrame for selected items across all stores | Loops through items × stores, calculates `unit_price × quantity` |
| `find_cheapest_per_item()` | Finds cheapest store for each item | `df.groupby("Item")["Total"].idxmin()` |
| `find_cheapest_basket()` | Finds cheapest single-store basket | `df.groupby("Store")["Total"].sum().idxmin()` |
| `build_comparison_matrix()` | Creates a pivot table for side-by-side view | `df.pivot_table(index="Item", columns="Store")` |

These feed into `generate_savings_report()` which bundles everything into a single `report` dictionary used by the UI and PDF generator.

---

## Slide 6: The AI Multi-Agent Pipeline (LangGraph)

**Why LangGraph?**
LangGraph lets us define a directed graph where each node is an agent with a specific responsibility. Data flows through shared state from one agent to the next.

**Pipeline State** (the shared data contract):
```python
class GroceryAgentState(TypedDict):
    raw_input: str              # User's free-text grocery list
    normalized_items: list      # Matched catalog item names
    quantities: dict            # Item → quantity mapping
    price_data: list            # All prices from all stores
    optimization: dict          # Cheapest basket analysis
    recommendations: list       # Substitute suggestions
    agent_log: Annotated[list, operator.add]  # Accumulated logs
```

The `Annotated[list, operator.add]` on `agent_log` means each node's log entries are **appended** to the list rather than overwriting it.

---

## Slide 7: Agent 1 — Item Normalizer

**Job:** Convert messy user input into exact catalog item names.

```
User types: "2 milk, bread, chiken, 3x rice"
                    ▼
Normalizer outputs: ["Milk (1L)", "Bread (White)",
                     "Chicken Breast (1kg)", "Rice (2kg)"]
```

**Three-tier matching strategy:**
1. **Exact match** — `"milk"` → `"Milk (1L)"` (case-insensitive)
2. **Keyword match** — `"peanut butter"` → `"Peanut Butter (400g)"` (substring + best-fit ranking)
3. **Fuzzy match** — `"chiken"` → `"Chicken Breast (1kg)"` (using `difflib` with 0.35 cutoff)

The `_parse_raw_input()` helper handles quantity extraction:
- `"2 milk"` → `("milk", 2)`
- `"bread x3"` → `("bread", 3)`
- `"eggs"` → `("eggs", 1)`

---

## Slide 8: Agent 2 — Price Fetcher

**Job:** Look up prices for each normalized item across all 5 stores.

```python
def price_fetcher_node(state):
    for item in items:
        result = fetch_store_prices.invoke({"item_name": item, "quantity": qty})
        # Returns: { "item": "Milk (1L)", "prices": [
        #   {"store": "Checkers",  "unit_price": 18.99, "total": 37.98},
        #   {"store": "Shoprite",  "unit_price": 16.99, "total": 33.98},
        #   ... (all 5 stores)
        # ]}
```

For a 5-item list, this produces **25 price points** (5 items × 5 stores) stored as a flat list of dicts in `state["price_data"]`.

---

## Slide 9: Agent 3 — Optimizer

**Job:** Analyze all price data to find the cheapest strategy.

Two strategies compared:
1. **Single-store basket** — Best store if you shop at only one place
2. **Cherry-pick** — Buy each item from whichever store is cheapest for that item

```python
result = optimize_basket.invoke({"price_data_json": json.dumps(flat)})
# Returns: {
#   "cheapest_store": "Shoprite",
#   "cheapest_store_total": 245.94,
#   "cherry_pick_total": 228.91,
#   "extra_cherry_savings": 17.03,
#   "cherry_pick_items": [{"item": "Milk", "store": "Shoprite"}, ...]
# }
```

---

## Slide 10: Agent 4 — Recommender

**Job:** Suggest cheaper substitute products.

Uses the `SUBSTITUTES` database to find alternatives:
```
Chicken Breast (1kg) R84.99 → Mince (500g) R49.99  | Save R35.00
Cheese (400g) R57.99       → Peanut Butter R34.99  | Save R23.00
Coffee (250g) R47.99       → Tea (100 bags) R36.99 | Save R11.00
```

Each substitute includes a human-readable reason explaining why it's a good swap.

---

## Slide 11: LangGraph Wiring

```python
@st.cache_resource
def build_agent_graph():
    graph = StateGraph(GroceryAgentState)
    graph.add_node("normalizer", normalizer_node)
    graph.add_node("price_fetcher", price_fetcher_node)
    graph.add_node("optimizer", optimizer_node)
    graph.add_node("recommender", recommender_node)

    graph.set_entry_point("normalizer")
    graph.add_edge("normalizer", "price_fetcher")
    graph.add_edge("price_fetcher", "optimizer")
    graph.add_edge("optimizer", "recommender")
    graph.add_edge("recommender", END)
    return graph.compile()
```

- **Linear pipeline**: Normalizer → Price Fetcher → Optimizer → Recommender → END
- `@st.cache_resource` ensures the graph is compiled only once
- `graph.invoke(initial_state)` runs the entire pipeline and returns the final state

---

## Slide 12: PDF Report Generation

The `generate_pdf()` function uses **fpdf2** to create professional reports:

**Report sections:**
1. **Header** — Green banner with title and generation date
2. **Summary** — Cheapest store, cherry-pick total, max savings, item count
3. **Store totals table** — All 5 stores ranked with a "CHEAPEST" badge
4. **Content** (based on user selection):
   - *Full comparison report*: price matrix + cherry-pick list
   - *Cherry-pick list only*: items with their cheapest store
   - *Single store basket*: shopping list for the cheapest store
5. **Footer** — Disclaimer about simulated prices

Output: `bytes(pdf.output())` → served via `st.download_button()`

---

## Slide 13: UI Design System

**Custom CSS** with the Inter font family provides a polished look:

| Component | CSS Class | Purpose |
|-----------|-----------|---------|
| Hero banner | `.hero-banner` | Green gradient header with title |
| KPI cards | `.kpi-card` | 4 summary metrics with hover lift effect |
| Store bars | Inline styles | Color-coded progress bars per store |
| Savings card | `.savings-card` | Green highlight for cherry-pick savings |
| Item pills | `.store-pill` | Color-coded store name badges |
| Swap cards | `.swap-card` | Yellow cards for substitute suggestions |
| Feature tiles | `.feature-tile` | Landing page feature highlights |

---

## Slide 14: Two Input Modes

### Browse & Select (Manual)
- Multiselect dropdown with all 30 catalog items
- Number input for each item's quantity
- Direct `get_prices_for_items()` call — no agent pipeline needed

### Type Your List (Smart Input)
- Free-text area accepting natural language
- Triggers the full LangGraph agent pipeline
- Handles typos, quantities, abbreviations
- Also produces substitute recommendations (Smart Savings tab)

Both modes feed into the **same results dashboard** — same KPI cards, same tabs, same charts, same PDF export.

---

## Slide 15: Results Dashboard Tabs

| Tab | Content |
|-----|---------|
| **Store Comparison** | Color-coded store bars + full price matrix with highlighted cheapest cells |
| **Best Prices** | Per-item breakdown showing cheapest store, with store pill badges |
| **Charts** | Bar charts: basket totals, price distribution, per-item comparison |
| **Smart Savings** | *(Smart Input mode only)* Substitute recommendations with savings amounts |
| **Save & Export** | Save to session (reusable in sidebar) or generate/download PDF report |

---

## Slide 16: Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Tools do the work, not LLMs** | Each agent has one tool containing all the logic. Tools run in milliseconds. No API latency. |
| **LangGraph for orchestration** | Even without LLM calls, LangGraph provides clean state management, logging, and a clear pipeline structure |
| **`@tool` decorator retained** | Keeps the code compatible with LLM-based agents if we want to add reasoning later |
| **Agents hidden from UI** | Users see "Comparing prices..." spinner, not technical agent names. Clean UX. |
| **`Annotated[list, operator.add]`** | Each agent appends to `agent_log` without overwriting previous agents' entries |
| **`@st.cache_resource`** | Graph compilation and expensive resources cached across Streamlit reruns |

---

## Slide 17: Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| "peanut butter" matched "Butter (500g)" instead of "Peanut Butter (400g)" | Implemented best-fit ranking: prioritize items whose base name starts with the input, then by smallest length difference |
| `min()` crashed on empty sequence in `find_substitutes` | Added `if not valid_orig or not valid_sub: continue` guard |
| Streamlit displayed "None" 5 times after PDF generation | Ternary expressions (`x if cond else y`) triggered Streamlit's "magic commands" AST transform. Fixed by converting to `if/else` blocks |
| Sidebar collapse icon showed "keyboard_double_arrow" text | Overly broad CSS selector `[class*="st-"]` overrode Material Symbols icon font. Scoped to specific widget classes |
| Pipeline took 60+ seconds | Replaced LLM round-trips with direct tool invocation. Pipeline now completes in under 1 second |

---

## Slide 18: Project Structure

```
DAY9/
├── app.py              # Main application (1432 lines)
│   ├── Lines 1-11      # Imports
│   ├── Lines 14-127    # Data (STORE_CATALOG, SUBSTITUTES)
│   ├── Lines 130-358   # CSS design system
│   ├── Lines 361-420   # Data processing functions
│   ├── Lines 424-592   # PDF generation (generate_pdf + helpers)
│   ├── Lines 595-870   # AI pipeline (state, tools, agent nodes, graph)
│   ├── Lines 873-910   # Pipeline runner + session state
│   └── Lines 912-1432  # UI (sidebar, landing, results, tabs, main)
├── .env                # Azure API keys (no longer needed at runtime)
├── streamlitapp.py     # Reference file
└── example.py          # Reference file
```

---

## Slide 19: How to Run

```bash
pip install streamlit pandas fpdf2 langgraph langchain-core
streamlit run app.py
```

Open `http://localhost:8501` in browser.

**No API keys required** — the agent pipeline uses direct tool invocation, so it works entirely offline with the simulated store data.

---

## Slide 20: Future Enhancements

- **Live price data** — Integrate with store APIs or web scraping for real-time prices
- **User accounts** — Persist saved lists across sessions with a database
- **Shopping list sharing** — Generate shareable links or WhatsApp messages
- **Location-based pricing** — Factor in store proximity and transport costs
- **LLM reasoning layer** — Re-enable LLM calls for conversational shopping advice ("What should I cook this week for under R200?")
- **Price history tracking** — Show price trends over time, alert on price drops
