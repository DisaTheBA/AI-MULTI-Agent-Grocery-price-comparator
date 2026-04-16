Smart Grocery Price Comparator
The Smart Grocery Price Comparator is a professional-grade Streamlit web application designed to optimize consumer grocery spending across five major South African retailers: Checkers, Pick n Pay, Woolworths, Shoprite, and SPAR. The application utilizes a multi-agent orchestration pipeline to normalize natural language input, fetch pricing data, identify optimal shopping strategies, and suggest cost-saving product substitutions.

Key Features
Dual-Mode Input: Seamlessly switch between a structured catalog browser and a Smart Input mode that parses free-text shopping lists.

Intelligent Optimization: Beyond simple total comparisons, the engine calculates "cherry-pick" strategies by identifying the cheapest store for each individual item in a basket.

AI-Driven Substitutions: Identifies expensive items and suggests high-value alternatives based on a curated substitution database.

Professional Reporting: Generates downloadable PDF reports with comprehensive price matrices and store-by-store breakdowns.

Performance-First Design: Implemented with efficient state management and caching; the entire AI pipeline executes in under one second.

Technical Architecture
This application separates business logic from UI representation to ensure scalability and maintainability.

The Agentic Pipeline
Built using LangGraph, the backend utilizes a directed graph to orchestrate specialized nodes:

Node	Responsibility
Normalizer	Converts raw user text into canonical catalog item names using fuzzy matching (difflib).
Price Fetcher	Aggregates price data across retailers for the defined basket.
Optimizer	Executes analytical operations to determine the most cost-effective shopping strategy.
Recommender	Queries the substitution engine to provide actionable money-saving advice.

Tech Stack
Frontend: Streamlit with custom CSS/Theming.

Orchestration: LangGraph (Graph-based state management).

Data Processing: Pandas (Pivot tables, vectorized price calculations).

PDF Generation: fpdf2 for dynamic, programmatic report creation.

Matching: difflib for typo-tolerant natural language processing.

Engineering Decisions
Choice	Rationale
LangGraph vs. Raw Scripts	Provides a modular state contract (GroceryAgentState) and clear logging for traceability.
Tools vs. LLM Latency	By using functional tools instead of LLM inference for price lookups, the system avoids API latency and runs offline.
@st.cache_resource	Ensures high performance by caching graph compilation and data structures across sessions.
Annotated State	Utilizes operator.add to maintain an immutable audit log of all agent actions.

Project Structure:

Plaintex
/
├── app.py              # Main application entry point & orchestration
├── .env                # Configuration management
└── requirements.txt    # Project dependencies

Quick Start
Clone the repository:

Bash
git clone [https://github.com/DisaTheBA/AI-MULTI-Agent-Grocery-price-comparator/]
cd [AI-MULTI-Agent-Grocery-price-comparator]
Install dependencies:

Bash
pip install -r requirements.txt
Run the application:

Bash
streamlit run app.py
Future Roadmap
Real-time Integration: Transition from simulated pricing to live store API integration.

User Persistence: Implement account systems for saved shopping lists.

Conversational Layer: Introduce LLM reasoning for context-aware shopping advice.

Price Trending: Visualize historical price fluctuations to alert users to price drops.
