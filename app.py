import streamlit as st
import pandas as pd
import json
import re
import operator
from typing import TypedDict, Annotated
from datetime import datetime
from difflib import get_close_matches
from fpdf import FPDF
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool


# ── Store price database (simulated realistic SA grocery prices in ZAR) ──────

STORE_CATALOG = {
    "Checkers": {
        "Milk (1L)": 18.99, "Bread (White)": 16.49, "Eggs (6 pack)": 29.99,
        "Rice (2kg)": 34.99, "Chicken Breast (1kg)": 89.99, "Bananas (1kg)": 14.99,
        "Tomatoes (1kg)": 24.99, "Onions (1kg)": 19.99, "Potatoes (2kg)": 29.99,
        "Cheese (400g)": 64.99, "Butter (500g)": 59.99, "Sugar (2.5kg)": 44.99,
        "Flour (2.5kg)": 29.99, "Cooking Oil (750ml)": 34.99, "Tea (100 bags)": 39.99,
        "Coffee (250g)": 54.99, "Pasta (500g)": 19.99, "Tinned Tomatoes (400g)": 14.99,
        "Cereal (500g)": 49.99, "Yoghurt (1kg)": 34.99, "Mince (500g)": 54.99,
        "Apples (1kg)": 29.99, "Carrots (1kg)": 14.99, "Spinach (bunch)": 12.99,
        "Peanut Butter (400g)": 39.99, "Jam (450g)": 29.99, "Margarine (500g)": 24.99,
        "Samp (2.5kg)": 29.99, "Maize Meal (5kg)": 59.99, "Baked Beans (410g)": 16.99,
    },
    "Pick n Pay": {
        "Milk (1L)": 17.99, "Bread (White)": 17.49, "Eggs (6 pack)": 27.99,
        "Rice (2kg)": 36.99, "Chicken Breast (1kg)": 94.99, "Bananas (1kg)": 12.99,
        "Tomatoes (1kg)": 22.99, "Onions (1kg)": 17.99, "Potatoes (2kg)": 32.99,
        "Cheese (400g)": 59.99, "Butter (500g)": 62.99, "Sugar (2.5kg)": 42.99,
        "Flour (2.5kg)": 27.99, "Cooking Oil (750ml)": 32.99, "Tea (100 bags)": 42.99,
        "Coffee (250g)": 49.99, "Pasta (500g)": 17.99, "Tinned Tomatoes (400g)": 15.99,
        "Cereal (500g)": 46.99, "Yoghurt (1kg)": 32.99, "Mince (500g)": 59.99,
        "Apples (1kg)": 27.99, "Carrots (1kg)": 16.99, "Spinach (bunch)": 10.99,
        "Peanut Butter (400g)": 37.99, "Jam (450g)": 27.99, "Margarine (500g)": 22.99,
        "Samp (2.5kg)": 27.99, "Maize Meal (5kg)": 54.99, "Baked Beans (410g)": 15.99,
    },
    "Woolworths": {
        "Milk (1L)": 22.99, "Bread (White)": 21.99, "Eggs (6 pack)": 34.99,
        "Rice (2kg)": 42.99, "Chicken Breast (1kg)": 109.99, "Bananas (1kg)": 17.99,
        "Tomatoes (1kg)": 29.99, "Onions (1kg)": 22.99, "Potatoes (2kg)": 34.99,
        "Cheese (400g)": 74.99, "Butter (500g)": 69.99, "Sugar (2.5kg)": 49.99,
        "Flour (2.5kg)": 34.99, "Cooking Oil (750ml)": 39.99, "Tea (100 bags)": 49.99,
        "Coffee (250g)": 64.99, "Pasta (500g)": 24.99, "Tinned Tomatoes (400g)": 19.99,
        "Cereal (500g)": 59.99, "Yoghurt (1kg)": 39.99, "Mince (500g)": 69.99,
        "Apples (1kg)": 34.99, "Carrots (1kg)": 19.99, "Spinach (bunch)": 16.99,
        "Peanut Butter (400g)": 44.99, "Jam (450g)": 34.99, "Margarine (500g)": 29.99,
        "Samp (2.5kg)": 34.99, "Maize Meal (5kg)": 69.99, "Baked Beans (410g)": 19.99,
    },
    "Shoprite": {
        "Milk (1L)": 16.99, "Bread (White)": 14.99, "Eggs (6 pack)": 26.99,
        "Rice (2kg)": 32.99, "Chicken Breast (1kg)": 84.99, "Bananas (1kg)": 13.99,
        "Tomatoes (1kg)": 21.99, "Onions (1kg)": 16.99, "Potatoes (2kg)": 27.99,
        "Cheese (400g)": 57.99, "Butter (500g)": 56.99, "Sugar (2.5kg)": 39.99,
        "Flour (2.5kg)": 24.99, "Cooking Oil (750ml)": 29.99, "Tea (100 bags)": 36.99,
        "Coffee (250g)": 47.99, "Pasta (500g)": 15.99, "Tinned Tomatoes (400g)": 12.99,
        "Cereal (500g)": 44.99, "Yoghurt (1kg)": 29.99, "Mince (500g)": 49.99,
        "Apples (1kg)": 24.99, "Carrots (1kg)": 12.99, "Spinach (bunch)": 9.99,
        "Peanut Butter (400g)": 34.99, "Jam (450g)": 24.99, "Margarine (500g)": 19.99,
        "Samp (2.5kg)": 24.99, "Maize Meal (5kg)": 49.99, "Baked Beans (410g)": 13.99,
    },
    "SPAR": {
        "Milk (1L)": 19.49, "Bread (White)": 15.99, "Eggs (6 pack)": 28.99,
        "Rice (2kg)": 35.99, "Chicken Breast (1kg)": 92.99, "Bananas (1kg)": 15.49,
        "Tomatoes (1kg)": 23.99, "Onions (1kg)": 18.99, "Potatoes (2kg)": 31.99,
        "Cheese (400g)": 62.99, "Butter (500g)": 58.99, "Sugar (2.5kg)": 43.99,
        "Flour (2.5kg)": 28.99, "Cooking Oil (750ml)": 33.99, "Tea (100 bags)": 41.99,
        "Coffee (250g)": 52.99, "Pasta (500g)": 18.99, "Tinned Tomatoes (400g)": 14.49,
        "Cereal (500g)": 47.99, "Yoghurt (1kg)": 33.99, "Mince (500g)": 56.99,
        "Apples (1kg)": 28.99, "Carrots (1kg)": 15.49, "Spinach (bunch)": 11.99,
        "Peanut Butter (400g)": 38.99, "Jam (450g)": 28.99, "Margarine (500g)": 23.99,
        "Samp (2.5kg)": 28.99, "Maize Meal (5kg)": 57.99, "Baked Beans (410g)": 15.49,
    },
}

STORE_COLORS = {
    "Checkers": "#1E3A5F",
    "Pick n Pay": "#0057A0",
    "Woolworths": "#5C2D91",
    "Shoprite": "#E31837",
    "SPAR": "#D4212C",
}

ALL_ITEMS = sorted(list(STORE_CATALOG["Checkers"].keys()))


# ── Substitutes database (for Recommendation Agent) ─────────────────────────

SUBSTITUTES = {
    "Chicken Breast (1kg)": [
        {"substitute": "Mince (500g)", "reason": "More affordable protein, versatile for curries, pasta, and stews"},
    ],
    "Butter (500g)": [
        {"substitute": "Margarine (500g)", "reason": "Budget-friendly spread with similar cooking properties"},
    ],
    "Cheese (400g)": [
        {"substitute": "Peanut Butter (400g)", "reason": "High-protein alternative, more filling per rand"},
    ],
    "Coffee (250g)": [
        {"substitute": "Tea (100 bags)", "reason": "Significantly lower cost per serving"},
    ],
    "Cereal (500g)": [
        {"substitute": "Maize Meal (5kg)", "reason": "Traditional breakfast staple, 10x more food per rand"},
    ],
    "Yoghurt (1kg)": [
        {"substitute": "Milk (1L)", "reason": "Can be used in smoothies at a fraction of the cost"},
    ],
    "Apples (1kg)": [
        {"substitute": "Bananas (1kg)", "reason": "Consistently cheaper fruit with high nutrition"},
    ],
    "Pasta (500g)": [
        {"substitute": "Rice (2kg)", "reason": "More affordable starch, larger portion per rand"},
        {"substitute": "Samp (2.5kg)", "reason": "Traditional SA staple, very affordable"},
    ],
    "Cooking Oil (750ml)": [
        {"substitute": "Margarine (500g)", "reason": "Can substitute for oil in many baking recipes"},
    ],
    "Jam (450g)": [
        {"substitute": "Peanut Butter (400g)", "reason": "More nutritious spread at a similar price"},
    ],
    "Mince (500g)": [
        {"substitute": "Baked Beans (410g)", "reason": "Affordable plant protein, great on bread or with pap"},
    ],
}


# ── Styling ──────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, .stMarkdown, .stButton, .stRadio, .stSelectbox,
    .stMultiSelect, .stTextInput, .stTextArea, .stNumberInput,
    .stTabs, .stExpander, .stDataFrame, .stAlert {
        font-family: 'Inter', sans-serif;
    }
    .main .block-container { padding-top: 1rem; max-width: 1200px; }

    .hero-banner {
        background: linear-gradient(135deg, #065f46 0%, #0f9b58 60%, #34d399 100%);
        padding: 2.2rem 2.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 1.8rem;
        color: white;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -40%; right: -10%;
        width: 300px; height: 300px;
        background: rgba(255,255,255,0.06);
        border-radius: 50%;
    }
    .hero-banner h1 {
        font-size: 1.9rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.8px;
        line-height: 1.2;
    }
    .hero-banner p {
        font-size: 0.9rem;
        opacity: 0.8;
        margin: 0.5rem auto 0;
        max-width: 520px;
        line-height: 1.4;
    }

    .kpi-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1.3rem 1rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    }
    .kpi-card .kpi-label {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #9ca3af;
        margin-bottom: 0.4rem;
    }
    .kpi-card .kpi-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: #111827;
        line-height: 1.2;
    }
    .kpi-card .kpi-sub {
        font-size: 0.72rem;
        color: #6b7280;
        margin-top: 0.25rem;
    }

    .cheapest-badge {
        display: inline-block;
        background: linear-gradient(135deg, #0f9b58, #34d399);
        color: white;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        letter-spacing: 0.4px;
        text-transform: uppercase;
    }

    .store-pill {
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 3px 11px;
        border-radius: 20px;
        color: white;
    }

    .savings-card {
        background: linear-gradient(135deg, #ecfdf5, #d1fae5);
        border: 1px solid #6ee7b7;
        border-radius: 14px;
        padding: 1.2rem 1.5rem;
        margin: 1.2rem 0;
        text-align: center;
    }
    .savings-card .savings-amount {
        font-size: 2rem;
        font-weight: 800;
        color: #065f46;
        line-height: 1.1;
    }
    .savings-card .savings-label {
        font-size: 0.82rem;
        color: #047857;
        margin-top: 0.2rem;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }

    .sec-heading {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1f2937;
        margin: 1.2rem 0 0.6rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .item-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.65rem 0.9rem;
        border-bottom: 1px solid #f3f4f6;
        font-size: 0.88rem;
        transition: background 0.15s;
    }
    .item-row:hover { background: #f9fafb; }
    .item-row:last-child { border-bottom: none; }
    .item-row .name { color: #374151; font-weight: 500; }
    .item-row .price { font-weight: 700; color: #111827; }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafb 0%, #eef2f7 100%);
    }
    div[data-testid="stSidebar"] [data-testid="stMarkdown"] p { font-size: 0.88rem; }

    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        font-weight: 600;
        font-size: 0.82rem;
    }

    .swap-card {
        background: linear-gradient(135deg, #fffbeb, #fef3c7);
        border: 1px solid #fcd34d;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        margin: 0.6rem 0;
    }
    .swap-card .swap-heading {
        font-weight: 700;
        font-size: 0.9rem;
        color: #78350f;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .swap-card .swap-reason {
        font-size: 0.8rem;
        color: #92400e;
        margin-top: 0.3rem;
        line-height: 1.4;
    }
    .swap-card .swap-prices {
        font-size: 0.78rem;
        color: #a16207;
        margin-top: 0.35rem;
    }
    .swap-badge {
        display: inline-block;
        background: #065f46;
        color: white;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 9px;
        border-radius: 12px;
        margin-top: 0.5rem;
        letter-spacing: 0.3px;
    }

    .feature-tile {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 1.5rem 1rem;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        transition: transform 0.2s;
    }
    .feature-tile:hover { transform: translateY(-2px); }
    .feature-tile .ft-icon { font-size: 2rem; margin-bottom: 0.4rem; }
    .feature-tile .ft-title {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #6b7280;
    }
    .feature-tile .ft-desc {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-top: 0.2rem;
    }
    </style>
    """, unsafe_allow_html=True)


# ── Data helpers ─────────────────────────────────────────────────────────────

def get_prices_for_items(selected_items: list[str], quantities: dict[str, int]) -> pd.DataFrame:
    rows = []
    for item in selected_items:
        qty = quantities.get(item, 1)
        for store, catalog in STORE_CATALOG.items():
            if item in catalog:
                unit_price = catalog[item]
                total = round(unit_price * qty, 2)
                rows.append({
                    "Item": item, "Store": store,
                    "Unit Price (R)": unit_price, "Qty": qty, "Total (R)": total,
                })
    return pd.DataFrame(rows)


def find_cheapest_per_item(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df.groupby("Item")["Total (R)"].idxmin()].reset_index(drop=True)


def find_cheapest_basket(df: pd.DataFrame) -> tuple[str, float]:
    basket = df.groupby("Store")["Total (R)"].sum().reset_index()
    basket.columns = ["Store", "Basket Total (R)"]
    cheapest_row = basket.loc[basket["Basket Total (R)"].idxmin()]
    return cheapest_row["Store"], cheapest_row["Basket Total (R)"]


def get_store_totals(df: pd.DataFrame) -> pd.DataFrame:
    totals = df.groupby("Store")["Total (R)"].sum().reset_index()
    totals.columns = ["Store", "Basket Total (R)"]
    return totals.sort_values("Basket Total (R)").reset_index(drop=True)


def build_comparison_matrix(df: pd.DataFrame) -> pd.DataFrame:
    pivot = df.pivot_table(index="Item", columns="Store", values="Total (R)", aggfunc="sum")
    pivot["Cheapest Store"] = pivot.idxmin(axis=1)
    pivot["Best Price (R)"] = pivot.drop(columns=["Cheapest Store"]).min(axis=1)
    return pivot.reset_index()


def generate_savings_report(df: pd.DataFrame) -> dict:
    store_totals = get_store_totals(df)
    cheapest_store, cheapest_total = find_cheapest_basket(df)
    most_expensive = store_totals["Basket Total (R)"].max()
    savings = round(most_expensive - cheapest_total, 2)
    pct = round((savings / most_expensive) * 100, 1) if most_expensive > 0 else 0
    cherry_pick = find_cheapest_per_item(df)
    cherry_total = round(cherry_pick["Total (R)"].sum(), 2)
    cherry_savings = round(cheapest_total - cherry_total, 2)
    return {
        "cheapest_store": cheapest_store,
        "cheapest_total": cheapest_total,
        "most_expensive_total": most_expensive,
        "max_savings": savings,
        "savings_pct": pct,
        "cherry_pick_total": cherry_total,
        "cherry_pick_extra_savings": cherry_savings,
        "store_totals": store_totals,
        "cherry_pick_items": cherry_pick,
    }


# ── PDF generation ───────────────────────────────────────────────────────────

def generate_pdf(report: dict, df: pd.DataFrame, option: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_fill_color(15, 155, 88)
    pdf.rect(0, 0, 210, 35, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_y(8)
    pdf.cell(0, 10, "Smart Grocery Price Comparator", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(12)
    pdf.set_text_color(30, 30, 30)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(15, 155, 88)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 10)
    for label, value in [
        ("Cheapest Single Store", f"{report['cheapest_store']}  -  R{report['cheapest_total']:.2f}"),
        ("Cherry-Pick Total", f"R{report['cherry_pick_total']:.2f}"),
        ("Maximum Savings", f"R{report['max_savings']:.2f}  ({report['savings_pct']}% vs most expensive)"),
        ("Items in Basket", str(len(df["Item"].unique()))),
    ]:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 7, label + ":", new_x="RIGHT")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Basket Total by Store", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(15, 155, 88)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    col_w = [90, 50, 50]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(240, 253, 244)
    pdf.cell(col_w[0], 7, "Store", border=1, fill=True, new_x="RIGHT")
    pdf.cell(col_w[1], 7, "Total (R)", border=1, fill=True, align="R", new_x="RIGHT")
    pdf.cell(col_w[2], 7, "Status", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for _, row in report["store_totals"].iterrows():
        is_best = row["Store"] == report["cheapest_store"]
        if is_best:
            pdf.set_fill_color(209, 250, 229)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_w[0], 7, row["Store"], border=1, fill=True, new_x="RIGHT")
        pdf.cell(col_w[1], 7, f"R{row['Basket Total (R)']:.2f}", border=1, fill=True, align="R", new_x="RIGHT")
        pdf.set_font("Helvetica", "B" if is_best else "", 9)
        pdf.cell(col_w[2], 7, "CHEAPEST" if is_best else "", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
    pdf.ln(6)

    if option == "Full comparison report":
        _pdf_full_matrix(pdf, df)
        _pdf_cherry_pick(pdf, report)
    elif option == "Cherry-pick list only":
        _pdf_cherry_pick(pdf, report)
    else:
        _pdf_single_store(pdf, df, report)

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "Smart Grocery Price Comparator  |  Prices are simulated for demonstration purposes", align="C")
    return bytes(pdf.output())


def _pdf_full_matrix(pdf: FPDF, df: pd.DataFrame):
    matrix = build_comparison_matrix(df)
    stores = [c for c in matrix.columns if c not in ("Item", "Cheapest Store", "Best Price (R)")]
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Full Price Comparison Matrix", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(15, 155, 88)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    item_w, best_w = 40, 28
    store_w = min(28, int((190 - item_w - best_w) / len(stores)))
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(240, 253, 244)
    pdf.cell(item_w, 6, "Item", border=1, fill=True, new_x="RIGHT")
    for s in stores:
        pdf.cell(store_w, 6, s, border=1, fill=True, align="C", new_x="RIGHT")
    pdf.cell(best_w, 6, "Best (R)", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 7)
    for _, row in matrix.iterrows():
        cheapest = row.get("Cheapest Store", "")
        pdf.cell(item_w, 6, str(row["Item"])[:25], border=1, new_x="RIGHT")
        for s in stores:
            val = row.get(s)
            is_cheapest = (s == cheapest)
            if is_cheapest:
                pdf.set_fill_color(209, 250, 229)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Helvetica", "B" if is_cheapest else "", 7)
            pdf.cell(store_w, 6, f"R{val:.2f}" if pd.notna(val) else "-", border=1, fill=True, align="R", new_x="RIGHT")
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_fill_color(255, 255, 255)
        best_val = row.get("Best Price (R)")
        pdf.cell(best_w, 6, f"R{best_val:.2f}" if pd.notna(best_val) else "-", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)


def _pdf_cherry_pick(pdf: FPDF, report: dict):
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Cheapest Per Item (Cherry-Pick)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(15, 155, 88)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    col_w = [55, 40, 25, 35, 35]
    headers = ["Item", "Store", "Qty", "Unit Price (R)", "Total (R)"]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(240, 253, 244)
    for i, h in enumerate(headers):
        nx = "RIGHT" if i < len(headers) - 1 else "LMARGIN"
        ny = "LAST" if i < len(headers) - 1 else "NEXT"
        pdf.cell(col_w[i], 7, h, border=1, fill=True, align="R" if i >= 2 else "L", new_x=nx, new_y=ny)
    pdf.set_font("Helvetica", "", 9)
    for _, row in report["cherry_pick_items"].iterrows():
        pdf.cell(col_w[0], 7, str(row["Item"]), border=1, new_x="RIGHT")
        pdf.cell(col_w[1], 7, str(row["Store"]), border=1, new_x="RIGHT")
        pdf.cell(col_w[2], 7, str(int(row["Qty"])), border=1, align="R", new_x="RIGHT")
        pdf.cell(col_w[3], 7, f"R{row['Unit Price (R)']:.2f}", border=1, align="R", new_x="RIGHT")
        pdf.cell(col_w[4], 7, f"R{row['Total (R)']:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(209, 250, 229)
    pdf.cell(sum(col_w[:4]), 8, "Cherry-Pick Total", border=1, fill=True, align="R", new_x="RIGHT")
    pdf.cell(col_w[4], 8, f"R{report['cherry_pick_total']:.2f}", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)


def _pdf_single_store(pdf: FPDF, df: pd.DataFrame, report: dict):
    store = report["cheapest_store"]
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, f"Shopping List - {store}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(15, 155, 88)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    store_df = df[df["Store"] == store]
    col_w = [70, 30, 40, 50]
    headers = ["Item", "Qty", "Unit Price (R)", "Total (R)"]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(240, 253, 244)
    for i, h in enumerate(headers):
        nx = "RIGHT" if i < len(headers) - 1 else "LMARGIN"
        ny = "LAST" if i < len(headers) - 1 else "NEXT"
        pdf.cell(col_w[i], 7, h, border=1, fill=True, align="R" if i >= 1 else "L", new_x=nx, new_y=ny)
    pdf.set_font("Helvetica", "", 9)
    for _, row in store_df.iterrows():
        pdf.cell(col_w[0], 7, str(row["Item"]), border=1, new_x="RIGHT")
        pdf.cell(col_w[1], 7, str(int(row["Qty"])), border=1, align="R", new_x="RIGHT")
        pdf.cell(col_w[2], 7, f"R{row['Unit Price (R)']:.2f}", border=1, align="R", new_x="RIGHT")
        pdf.cell(col_w[3], 7, f"R{row['Total (R)']:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(209, 250, 229)
    pdf.cell(sum(col_w[:3]), 8, "Basket Total", border=1, fill=True, align="R", new_x="RIGHT")
    pdf.cell(col_w[3], 8, f"R{report['cheapest_total']:.2f}", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)


# ══════════════════════════════════════════════════════════════════════════════
# ██  AI AGENT PIPELINE  (LangGraph)
# ══════════════════════════════════════════════════════════════════════════════

AGENT_META = {
    "Item Normalizer":  {"icon": "🔤", "color": "#4A90D9"},
    "Price Fetcher":    {"icon": "💰", "color": "#E67E22"},
    "Optimizer":        {"icon": "📊", "color": "#27AE60"},
    "Recommender":      {"icon": "💡", "color": "#8E44AD"},
}


# ── Agent State ──────────────────────────────────────────────────────────────

class GroceryAgentState(TypedDict):
    raw_input: str
    normalized_items: list
    quantities: dict
    price_data: list
    optimization: dict
    recommendations: list
    agent_log: Annotated[list, operator.add]


# ── LLM ──────────────────────────────────────────────────────────────────────

# ── Agent Tools ──────────────────────────────────────────────────────────────

@tool
def normalize_item(raw_name: str, quantity: int = 1) -> dict:
    """Match a raw grocery item name to the nearest item in the store catalog.
    Include the quantity the user wants. Returns the best matching catalog item."""
    raw_lower = raw_name.lower().strip()

    for item in ALL_ITEMS:
        if raw_lower == item.lower():
            return {"matched": True, "catalog_item": item, "quantity": quantity, "confidence": "exact"}

    keyword_matches = []
    for item in ALL_ITEMS:
        item_lower = item.lower()
        item_base = item_lower.split("(")[0].strip()
        if raw_lower in item_lower or item_base in raw_lower:
            keyword_matches.append(item)

    if keyword_matches:
        best = min(keyword_matches, key=lambda x: (
            0 if x.lower().split("(")[0].strip().startswith(raw_lower) else 1,
            abs(len(x.lower().split("(")[0].strip()) - len(raw_lower)),
        ))
        return {"matched": True, "catalog_item": best, "quantity": quantity, "confidence": "high"}

    item_lowers = {i.lower(): i for i in ALL_ITEMS}
    matches = get_close_matches(raw_lower, list(item_lowers.keys()), n=1, cutoff=0.35)
    if matches:
        return {"matched": True, "catalog_item": item_lowers[matches[0]], "quantity": quantity, "confidence": "fuzzy"}

    return {"matched": False, "catalog_item": None, "quantity": quantity, "confidence": "none",
            "available_items": ALL_ITEMS}


@tool
def fetch_store_prices(item_name: str, quantity: int = 1) -> dict:
    """Fetch prices for a specific grocery item from all available stores.
    Returns prices from Checkers, Pick n Pay, Woolworths, Shoprite, and SPAR."""
    prices = []
    for store, catalog in STORE_CATALOG.items():
        if item_name in catalog:
            unit_price = catalog[item_name]
            prices.append({
                "store": store, "unit_price": unit_price,
                "quantity": quantity, "total": round(unit_price * quantity, 2),
            })
    if prices:
        cheapest = min(prices, key=lambda x: x["total"])
        return {"item": item_name, "found": True, "prices": prices,
                "cheapest_store": cheapest["store"], "cheapest_total": cheapest["total"]}
    return {"item": item_name, "found": False, "prices": []}


@tool
def optimize_basket(price_data_json: str) -> dict:
    """Find the optimal shopping strategy from collected price data.
    Takes a JSON string of all item prices and returns cheapest store basket
    and cherry-pick analysis."""
    data = json.loads(price_data_json)
    df = pd.DataFrame(data)
    if df.empty:
        return {"error": "No price data provided"}

    store_totals = df.groupby("store")["total"].sum()
    cheapest_store = store_totals.idxmin()
    cheapest_total = round(store_totals.min(), 2)

    cherry = df.loc[df.groupby("item")["total"].idxmin()]
    cherry_total = round(cherry["total"].sum(), 2)
    most_expensive = round(store_totals.max(), 2)

    return {
        "cheapest_store": cheapest_store,
        "cheapest_store_total": cheapest_total,
        "cherry_pick_total": cherry_total,
        "most_expensive_total": most_expensive,
        "potential_savings": round(most_expensive - cheapest_total, 2),
        "extra_cherry_savings": round(cheapest_total - cherry_total, 2),
        "store_ranking": {s: round(t, 2) for s, t in store_totals.sort_values().items()},
        "cherry_pick_items": cherry[["item", "store", "total"]].to_dict("records"),
    }


@tool
def find_substitutes(item_name: str) -> dict:
    """Find cheaper substitute products for a given grocery item.
    Returns available substitutes with reasons and price comparisons."""
    subs = SUBSTITUTES.get(item_name, [])
    if not subs:
        return {"item": item_name, "has_substitutes": False, "substitutes": []}

    enriched = []
    for sub in subs:
        sub_name = sub["substitute"]
        valid_orig = [STORE_CATALOG[s][item_name] for s in STORE_CATALOG if item_name in STORE_CATALOG[s]]
        valid_sub = [STORE_CATALOG[s][sub_name] for s in STORE_CATALOG if sub_name in STORE_CATALOG[s]]
        if not valid_orig or not valid_sub:
            continue
        orig_cheapest = min(valid_orig)
        sub_cheapest = min(valid_sub)
        enriched.append({
            "substitute": sub_name,
            "reason": sub["reason"],
            "original_cheapest": orig_cheapest,
            "substitute_cheapest": sub_cheapest,
            "savings_per_unit": round(max(orig_cheapest - sub_cheapest, 0), 2),
        })
    return {"item": item_name, "has_substitutes": len(enriched) > 0, "substitutes": enriched}


# ── Agent Nodes ──────────────────────────────────────────────────────────────

def _parse_raw_input(raw_input: str) -> list[tuple[str, int]]:
    """Parse free-text grocery input into (item_name, quantity) pairs."""
    lines = [ln.strip().strip("-•*").strip() for ln in raw_input.splitlines() if ln.strip()]
    parsed = []
    for line in lines:
        m = re.match(r'^(\d+)\s*[xX]?\s+(.+)$', line)
        if m:
            parsed.append((m.group(2).strip(), int(m.group(1))))
        else:
            m2 = re.match(r'^(.+?)\s*[xX]\s*(\d+)$', line)
            if m2:
                parsed.append((m2.group(1).strip(), int(m2.group(2))))
            else:
                parsed.append((line, 1))
    return parsed


def normalizer_node(state: GroceryAgentState) -> dict:
    raw_items = _parse_raw_input(state["raw_input"])

    normalized = []
    quantities = {}
    tool_calls = []
    for raw_name, qty in raw_items:
        result = normalize_item.invoke({"raw_name": raw_name, "quantity": qty})
        tool_calls.append({"tool": "normalize_item", "args": {"raw_name": raw_name, "quantity": qty}, "result": json.dumps(result)})
        if result.get("matched") and result.get("catalog_item"):
            item = result["catalog_item"]
            if item not in normalized:
                normalized.append(item)
                quantities[item] = result.get("quantity", qty)

    return {
        "normalized_items": normalized,
        "quantities": quantities,
        "agent_log": [{
            "agent": "Item Normalizer", "icon": "🔤", "color": "#4A90D9",
            "summary": f"Matched {len(normalized)} of {len(raw_items)} items to catalog",
            "response": "", "tool_calls": tool_calls, "items_matched": normalized,
        }],
    }


def price_fetcher_node(state: GroceryAgentState) -> dict:
    items = state.get("normalized_items", [])
    quantities = state.get("quantities", {})
    if not items:
        return {
            "price_data": [],
            "agent_log": [{"agent": "Price Fetcher", "icon": "💰", "color": "#E67E22",
                           "summary": "No items to price", "response": "", "tool_calls": []}],
        }

    price_data = []
    tool_calls = []
    for item in items:
        qty = quantities.get(item, 1)
        result = fetch_store_prices.invoke({"item_name": item, "quantity": qty})
        tool_calls.append({"tool": "fetch_store_prices", "args": {"item_name": item, "quantity": qty}, "result": json.dumps(result)})
        if result.get("found"):
            for p in result["prices"]:
                price_data.append({
                    "Item": result["item"], "Store": p["store"],
                    "Unit Price (R)": p["unit_price"], "Qty": p["quantity"], "Total (R)": p["total"],
                })

    return {
        "price_data": price_data,
        "agent_log": [{"agent": "Price Fetcher", "icon": "💰", "color": "#E67E22",
                       "summary": f"Retrieved {len(price_data)} price points across 5 stores",
                       "response": "", "tool_calls": tool_calls}],
    }


def optimizer_node(state: GroceryAgentState) -> dict:
    price_data = state.get("price_data", [])
    if not price_data:
        return {
            "optimization": {},
            "agent_log": [{"agent": "Optimizer", "icon": "📊", "color": "#27AE60",
                           "summary": "No price data to optimize", "response": "", "tool_calls": []}],
        }

    flat = [{"item": r["Item"], "store": r["Store"], "total": r["Total (R)"]} for r in price_data]
    result = optimize_basket.invoke({"price_data_json": json.dumps(flat)})
    optimization = result if isinstance(result, dict) else {}
    tool_calls = [{"tool": "optimize_basket", "args": {"price_data_json": "..."}, "result": json.dumps(optimization)}]

    return {
        "optimization": optimization,
        "agent_log": [{"agent": "Optimizer", "icon": "📊", "color": "#27AE60",
                       "summary": f"Best store: {optimization.get('cheapest_store', '?')} at R{optimization.get('cheapest_store_total', 0):.2f}",
                       "response": "", "tool_calls": tool_calls}],
    }


def recommender_node(state: GroceryAgentState) -> dict:
    items = state.get("normalized_items", [])
    if not items:
        return {
            "recommendations": [],
            "agent_log": [{"agent": "Recommender", "icon": "💡", "color": "#8E44AD",
                           "summary": "No items to analyze", "response": "", "tool_calls": []}],
        }

    tool_calls = []
    recommendations = []
    for item in items:
        result = find_substitutes.invoke({"item_name": item})
        tool_calls.append({"tool": "find_substitutes", "args": {"item_name": item}, "result": json.dumps(result)})
        if result.get("has_substitutes"):
            for sub in result["substitutes"]:
                recommendations.append({
                    "original": result["item"],
                    "substitute": sub["substitute"],
                    "reason": sub["reason"],
                    "original_price": sub["original_cheapest"],
                    "substitute_price": sub["substitute_cheapest"],
                    "savings": sub["savings_per_unit"],
                })

    return {
        "recommendations": recommendations,
        "agent_log": [{"agent": "Recommender", "icon": "💡", "color": "#8E44AD",
                       "summary": f"Found {len(recommendations)} substitute suggestions",
                       "response": "", "tool_calls": tool_calls}],
    }


# ── Build LangGraph ──────────────────────────────────────────────────────────

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


# ── Pipeline runner ──────────────────────────────────────────────────────────

def run_ai_pipeline(raw_input: str):
    graph = build_agent_graph()
    initial_state: GroceryAgentState = {
        "raw_input": raw_input,
        "normalized_items": [],
        "quantities": {},
        "price_data": [],
        "optimization": {},
        "recommendations": [],
        "agent_log": [],
    }

    with st.spinner("Comparing prices across 5 stores..."):
        try:
            result = graph.invoke(initial_state)

            if result and result.get("price_data"):
                df = pd.DataFrame(result["price_data"])
                st.session_state.price_df = df
                st.session_state.grocery_list = result["normalized_items"]
                st.session_state.quantities = result["quantities"]
                st.session_state.comparison_done = True
                st.session_state.agent_log = result["agent_log"]
                st.session_state.ai_recommendations = result["recommendations"]
                st.session_state.ai_mode_used = True
            else:
                st.warning(
                    "We couldn't match any items from your list. "
                    "Try common names like: milk, bread, eggs, chicken, rice"
                )

        except Exception as e:
            st.error(f"Something went wrong while comparing prices. Please try again. ({e})")


# ── Session state ────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "grocery_list": [],
        "quantities": {},
        "comparison_done": False,
        "price_df": pd.DataFrame(),
        "saved_lists": [],
        "input_mode": "Browse & Select",
        "ai_mode_used": False,
        "agent_log": [],
        "ai_recommendations": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Sidebar ──────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown(
            "<div style='text-align:center;padding:0.6rem 0 0.3rem 0'>"
            "<span style='font-size:2.4rem'>🛒</span>"
            "<h2 style='margin:0.2rem 0 0 0;font-weight:800;"
            "font-size:1.15rem;color:#1f2937;letter-spacing:-0.3px'>My Grocery List</h2>"
            "<p style='color:#9ca3af;font-size:0.72rem;margin:0.15rem 0 0 0'>Build your list, compare prices instantly</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.divider()

        mode = st.radio(
            "How would you like to add items?",
            ["Browse & Select", "Type Your List"],
            index=0 if st.session_state.input_mode == "Browse & Select" else 1,
            horizontal=True,
            key="mode_radio",
            label_visibility="collapsed",
        )
        st.session_state.input_mode = mode

        if mode == "Browse & Select":
            _render_manual_sidebar()
        else:
            _render_ai_sidebar()

        if st.session_state.saved_lists:
            st.divider()
            st.markdown("<p class='sec-heading'>💾 Saved Lists</p>", unsafe_allow_html=True)
            for i, saved in enumerate(st.session_state.saved_lists):
                with st.expander(f"📋 {saved['name']}  —  R{saved['total']:.2f}"):
                    st.caption(f"Saved: {saved['date']}")
                    st.caption(f"Strategy: {saved['strategy']}")
                    for it in saved["items"]:
                        st.markdown(f"- {it['item']}  x{it['qty']}  —  **R{it['price']:.2f}** ({it['store']})")

        st.divider()
        st.markdown(
            "<div style='text-align:center;padding:0.3rem 0'>"
            "<p style='font-size:0.65rem;color:#c0c5cc;margin:0'>"
            "Smart Grocery Comparator v2.0</p></div>",
            unsafe_allow_html=True,
        )


def _render_manual_sidebar():
    selected = st.multiselect(
        "Choose grocery items", options=ALL_ITEMS,
        default=st.session_state.grocery_list,
        placeholder="Search for items...",
        label_visibility="collapsed",
    )
    st.session_state.grocery_list = selected

    if selected:
        st.divider()
        st.markdown(f"<p style='font-size:0.78rem;font-weight:600;color:#6b7280;"
                    f"margin:0 0 0.3rem 0'>Quantities ({len(selected)} items)</p>",
                    unsafe_allow_html=True)
        for item in selected:
            current_qty = st.session_state.quantities.get(item, 1)
            st.session_state.quantities[item] = st.number_input(
                item, min_value=1, max_value=50, value=current_qty, key=f"qty_{item}",
            )

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        compare_btn = st.button("🔍 Compare Prices", use_container_width=True, type="primary", disabled=len(selected) == 0)
    with col2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)

    if compare_btn and selected:
        df = get_prices_for_items(selected, st.session_state.quantities)
        st.session_state.price_df = df
        st.session_state.comparison_done = True
        st.session_state.ai_mode_used = False

    if clear_btn:
        _clear_state()
        st.rerun()


def _render_ai_sidebar():
    st.markdown(
        "<p style='font-size:0.78rem;color:#6b7280;margin:0 0 0.5rem 0'>"
        "Type your items naturally — we'll find the best prices for you.</p>",
        unsafe_allow_html=True,
    )

    ai_input = st.text_area(
        "Type your grocery list",
        placeholder="e.g.\nmilk\n2 bread\neggs\nchicken breast\n3 rice\nbananas\nbutter",
        height=200,
        key="ai_text_input",
        label_visibility="collapsed",
    )

    st.markdown("")
    col1, col2 = st.columns(2)
    with col1:
        run_btn = st.button(
            "🔍 Compare Prices", use_container_width=True, type="primary",
            disabled=not ai_input or len(ai_input.strip()) == 0,
        )
    with col2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)

    if run_btn and ai_input and ai_input.strip():
        _clear_state()
        st.session_state.input_mode = "Type Your List"
        st.session_state.pending_pipeline = ai_input.strip()
        st.rerun()

    if clear_btn:
        _clear_state()
        st.rerun()


def _clear_state():
    st.session_state.grocery_list = []
    st.session_state.quantities = {}
    st.session_state.comparison_done = False
    st.session_state.price_df = pd.DataFrame()
    st.session_state.ai_mode_used = False
    st.session_state.agent_log = []
    st.session_state.ai_recommendations = []
    st.session_state.pop("pdf_bytes", None)
    st.session_state.pop("pdf_option", None)
    st.session_state.pop("pending_pipeline", None)
    for key in list(st.session_state.keys()):
        if key.startswith("qty_"):
            del st.session_state[key]


# ── Landing view ─────────────────────────────────────────────────────────────

def render_landing():
    st.markdown(
        "<div style='text-align:center;padding:2.5rem 1rem 1.5rem'>"
        "<h2 style='font-weight:800;color:#1f2937;margin:0;font-size:1.6rem;"
        "letter-spacing:-0.5px'>Start by adding items to your list</h2>"
        "<p style='color:#9ca3af;font-size:0.92rem;max-width:480px;margin:0.5rem auto 0;"
        "line-height:1.5'>Use the sidebar to build your grocery list, then we'll instantly "
        "compare prices across all 5 major stores.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("")
    cols = st.columns(4)
    features = [
        ("🏪", "5 Stores", "Checkers, PnP, Woolworths, Shoprite, SPAR"),
        ("📊", "Smart Compare", "Side-by-side price breakdown"),
        ("💰", "Max Savings", "Cherry-pick the cheapest per item"),
        ("📄", "PDF Export", "Download your comparison report"),
    ]
    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(
                f"<div class='feature-tile'>"
                f"<div class='ft-icon'>{icon}</div>"
                f"<div class='ft-title'>{title}</div>"
                f"<div class='ft-desc'>{desc}</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            "<div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;"
            "padding:1rem 1.2rem'>"
            "<p style='font-weight:700;font-size:0.85rem;color:#166534;margin:0 0 0.3rem 0'>"
            "🔍 Browse & Select</p>"
            "<p style='font-size:0.78rem;color:#15803d;margin:0;line-height:1.4'>"
            "Choose items from a dropdown and set quantities. Great for precise lists.</p></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            "<div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;"
            "padding:1rem 1.2rem'>"
            "<p style='font-weight:700;font-size:0.85rem;color:#1e40af;margin:0 0 0.3rem 0'>"
            "✏️ Type Your List</p>"
            "<p style='font-size:0.78rem;color:#1d4ed8;margin:0;line-height:1.4'>"
            "Just type items naturally — like <em>milk, 2 bread, eggs, chicken</em>. "
            "We'll figure out the rest.</p></div>",
            unsafe_allow_html=True,
        )


# ── Results view ─────────────────────────────────────────────────────────────

def render_results():
    df = st.session_state.price_df
    if df.empty:
        render_landing()
        return

    report = generate_savings_report(df)

    cols = st.columns(4)
    with cols[0]:
        st.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>Cheapest Store</div>"
            f"<div class='kpi-value' style='color:#0f9b58'>🏆 {report['cheapest_store']}</div>"
            f"<div class='kpi-sub'>Best single-store basket</div></div>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>Best Basket Price</div>"
            f"<div class='kpi-value'>R{report['cheapest_total']:.2f}</div>"
            f"<div class='kpi-sub'>Everything at {report['cheapest_store']}</div></div>",
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>Cherry-Pick Total</div>"
            f"<div class='kpi-value' style='color:#0f9b58'>R{report['cherry_pick_total']:.2f}</div>"
            f"<div class='kpi-sub'>Cheapest per item across stores</div></div>",
            unsafe_allow_html=True,
        )
    with cols[3]:
        st.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>You Could Save</div>"
            f"<div class='kpi-value' style='color:#dc2626'>R{report['max_savings']:.2f}</div>"
            f"<div class='kpi-sub'>{report['savings_pct']}% vs most expensive store</div></div>",
            unsafe_allow_html=True,
        )

    if report["cherry_pick_extra_savings"] > 0:
        st.markdown(
            f"<div class='savings-card'>"
            f"<div class='savings-label'>By picking the cheapest store for each item, you save an extra</div>"
            f"<div class='savings-amount'>R{report['cherry_pick_extra_savings']:.2f}</div>"
            f"<div class='savings-label'>compared to shopping only at {report['cheapest_store']}</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("")

    has_recs = st.session_state.ai_mode_used and st.session_state.get("ai_recommendations")
    if has_recs:
        tab1, tab2, tab3, tab_rec, tab_save = st.tabs([
            "📊 Store Comparison", "🏷️ Best Prices", "📈 Charts",
            "💡 Smart Savings", "💾 Save & Export",
        ])
    else:
        tab1, tab2, tab3, tab_save = st.tabs([
            "📊 Store Comparison", "🏷️ Best Prices", "📈 Charts", "💾 Save & Export",
        ])
        tab_rec = None

    with tab1:
        _render_store_comparison(report, df)
    with tab2:
        _render_best_per_item(report)
    with tab3:
        _render_charts(report, df)
    if tab_rec is not None:
        with tab_rec:
            _render_recommendations()
    with tab_save:
        _render_save_export(report, df)


def _render_store_comparison(report, df):
    st.markdown("<p class='sec-heading'>🏪 Basket Total by Store</p>", unsafe_allow_html=True)
    store_totals = report["store_totals"]

    for _, row in store_totals.iterrows():
        store = row["Store"]
        total = row["Basket Total (R)"]
        is_cheapest = store == report["cheapest_store"]
        color = STORE_COLORS.get(store, "#555")
        max_total = store_totals["Basket Total (R)"].max()
        bar_width = int((total / max_total) * 100)
        badge = " <span class='cheapest-badge'>Best Price</span>" if is_cheapest else ""
        border = f"border-left: 4px solid {color};" if is_cheapest else f"border-left: 4px solid {color}30;"

        st.markdown(
            f"<div style='{border} padding:0.85rem 1rem;margin:0.35rem 0;"
            f"border-radius:10px;background:{'#f0fdf4' if is_cheapest else '#fafafa'}'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center'>"
            f"<span style='font-weight:600;font-size:0.95rem;"
            f"color:{color}'>{store}{badge}</span>"
            f"<span style='font-weight:800;font-size:1.1rem'>"
            f"R{total:.2f}</span></div>"
            f"<div style='margin-top:7px;background:#e5e7eb;border-radius:4px;height:5px;overflow:hidden'>"
            f"<div style='width:{bar_width}%;height:100%;background:{color};border-radius:4px;"
            f"transition:width 0.4s ease'></div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.markdown("<p class='sec-heading'>📋 Full Price Matrix</p>", unsafe_allow_html=True)
    matrix = build_comparison_matrix(df)
    store_cols = [c for c in matrix.columns if c not in ("Item", "Cheapest Store", "Best Price (R)")]

    def highlight_cheapest(row):
        styles = [""] * len(row)
        for i, col in enumerate(row.index):
            if col in store_cols and col == row.get("Cheapest Store"):
                styles[i] = "background-color: #d1fae5; font-weight: 700"
        return styles

    styled = matrix.style.apply(highlight_cheapest, axis=1).format(
        {col: "R{:.2f}" for col in store_cols + ["Best Price (R)"]}, na_rep="—",
    )
    st.dataframe(styled, use_container_width=True, hide_index=True, height=min(400, 40 + 35 * len(matrix)))


def _render_best_per_item(report):
    st.markdown("<p class='sec-heading'>🏷️ Cheapest Store for Each Item</p>", unsafe_allow_html=True)
    cherry = report["cherry_pick_items"]
    for _, row in cherry.iterrows():
        color = STORE_COLORS.get(row["Store"], "#555")
        st.markdown(
            f"<div class='item-row'>"
            f"<div><span class='name'>{row['Item']}</span>"
            f"  <span style='color:#d1d5db;font-size:0.75rem'>x{row['Qty']}</span></div>"
            f"<div style='display:flex;align-items:center;gap:10px'>"
            f"<span class='store-pill' style='background:{color}'>{row['Store']}</span>"
            f"<span class='price'>R{row['Total (R)']:.2f}</span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        f"<div style='margin-top:0.8rem;padding:0.9rem 1.2rem;background:#f0fdf4;"
        f"border-radius:12px;border:1px solid #86efac;text-align:right'>"
        f"<span style='font-size:0.85rem;color:#065f46'>"
        f"Cherry-Pick Total: </span>"
        f"<span style='font-size:1.35rem;font-weight:800;"
        f"color:#065f46'>R{report['cherry_pick_total']:.2f}</span></div>",
        unsafe_allow_html=True,
    )
    st.markdown("")
    stores_needed = cherry["Store"].nunique()
    store_list = ", ".join(cherry["Store"].unique())
    st.info(f"You'd visit **{stores_needed} store(s)** for maximum savings: {store_list}")


def _render_charts(report, df):
    st.markdown("<p class='sec-heading'>📈 Price Comparison Charts</p>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Basket Total by Store**")
        st.bar_chart(report["store_totals"].set_index("Store"), color="#0f9b58", horizontal=True)
    with c2:
        st.markdown("**Price Distribution by Store**")
        st.bar_chart(df.pivot_table(index="Item", columns="Store", values="Unit Price (R)"))
    st.markdown("")
    st.markdown("**Per-Item Price Across Stores**")
    st.bar_chart(df.pivot_table(index="Item", columns="Store", values="Total (R)", aggfunc="sum"))


def _render_recommendations():
    st.markdown("<p class='sec-heading'>💡 Money-Saving Swaps</p>", unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.82rem;color:#6b7280;margin:-0.3rem 0 1rem 0'>"
        "These are cheaper alternatives you could consider without compromising on your meal plan.</p>",
        unsafe_allow_html=True,
    )
    recs = st.session_state.get("ai_recommendations", [])

    if not recs:
        st.info("No swap suggestions for your current items.")
        return

    total_potential_savings = sum(r["savings"] for r in recs)
    st.markdown(
        f"<div class='savings-card'>"
        f"<div class='savings-label'>Total potential savings with swaps</div>"
        f"<div class='savings-amount'>R{total_potential_savings:.2f}</div>"
        f"<div class='savings-label'>across {len(recs)} suggested swap{'s' if len(recs) != 1 else ''}</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("")

    for rec in recs:
        savings_badge = (
            f"<span class='swap-badge'>Save R{rec['savings']:.2f}</span>"
            if rec["savings"] > 0 else ""
        )
        st.markdown(
            f"<div class='swap-card'>"
            f"<div class='swap-heading'>🔄 {rec['original']}  →  {rec['substitute']}</div>"
            f"<div class='swap-reason'>{rec['reason']}</div>"
            f"<div class='swap-prices'>"
            f"Currently <b>R{rec['original_price']:.2f}</b> &nbsp;→&nbsp; "
            f"Swap for <b>R{rec['substitute_price']:.2f}</b></div>"
            f"{savings_badge}</div>",
            unsafe_allow_html=True,
        )


def _render_save_export(report, df):
    st.markdown("<p class='sec-heading'>💾 Save Your Cheapest List</p>", unsafe_allow_html=True)
    save_col1, save_col2 = st.columns(2)

    with save_col1:
        st.markdown("**Option 1: Save to Session**")
        strategy = st.radio(
            "Choose savings strategy",
            ["Single Store (cheapest basket)", "Cherry-Pick (cheapest per item)"],
            key="save_strategy",
        )
        list_name = st.text_input("Name your list", value=f"Grocery List {datetime.now().strftime('%d %b %Y')}")

        if st.button("💾 Save List", use_container_width=True, type="primary"):
            if strategy.startswith("Single"):
                items_to_save = df[df["Store"] == report["cheapest_store"]]
                total = report["cheapest_total"]
                strat_label = f"Single Store: {report['cheapest_store']}"
            else:
                items_to_save = report["cherry_pick_items"]
                total = report["cherry_pick_total"]
                strat_label = "Cherry-Pick"
            st.session_state.saved_lists.append({
                "name": list_name,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "strategy": strat_label,
                "total": total,
                "items": [
                    {"item": r["Item"], "store": r["Store"], "qty": r["Qty"], "price": r["Total (R)"]}
                    for _, r in items_to_save.iterrows()
                ],
            })
            st.success(f"Saved **{list_name}** — R{total:.2f}")

    with save_col2:
        st.markdown("**Option 2: Download as PDF**")
        dl_option = st.radio(
            "What to include in PDF",
            ["Full comparison report", "Cherry-pick list only", "Single store basket"],
            key="dl_option",
        )
        if st.button("📥 Generate PDF", use_container_width=True, type="secondary"):
            try:
                st.session_state["pdf_bytes"] = generate_pdf(report, df, dl_option)
            except Exception as e:
                st.session_state.pop("pdf_bytes", None)
                st.error(f"Could not generate PDF: {e}")
        if st.session_state.get("pdf_bytes"):
            st.download_button(
                "📄 Download PDF",
                data=st.session_state["pdf_bytes"],
                file_name=f"grocery_comparison_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.success("PDF ready for download!")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Smart Grocery Comparator",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_css()
    init_state()

    st.markdown(
        "<div class='hero-banner'>"
        "<h1>🛒 Smart Grocery Comparator</h1>"
        "<p>Compare prices across Checkers, Pick n Pay, Woolworths, Shoprite & SPAR "
        "— find the cheapest basket in seconds</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    render_sidebar()

    if st.session_state.get("pending_pipeline"):
        raw_input = st.session_state.pop("pending_pipeline")
        run_ai_pipeline(raw_input)

    if st.session_state.comparison_done:
        render_results()
    else:
        render_landing()


if __name__ == "__main__":
    main()
