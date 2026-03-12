# AI Visibility Analyzer — Prototype Specification
**Project:** HBCU Battle of the Brains 2026 — "The New Front Door: Trustworthy AI Product Discovery"  
**Purpose:** This document is a prompt/spec for an AI coding agent to build a working prototype.

---

## What This App Does

This prototype helps small/medium businesses understand why their products are invisible or misrepresented in AI-generated search results. It:

1. Accepts a product (name, description, key specs, price) as input
2. Queries multiple LLMs with generalized consumer-style prompts (e.g. "What are the best gaming keyboards under $100?")
3. Compares LLM responses against the actual product data using NLP
4. Scores visibility (did the product appear?) and accuracy (is the data correct?)
5. Outputs a dashboard with gap analysis, recommendations, and a visibility score

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ |
| LLM querying | Anthropic Claude API (`claude-sonnet-4-20250514`) |
| NLP / text comparison | `spaCy`, `sentence-transformers` (cosine similarity) |
| Data parsing | `pydantic` for product schema validation |
| Frontend dashboard | Streamlit |
| Storage | JSON flat files (prototype scope) |
| Package manager | pip |

---

## Project Structure

```
2026-HBCU-BOTB/
├── run.sh                     # single command to install + launch
├── README.md
├── requirements.txt
├── config.py                  # model name + reusable prompt templates
├── data/
│   └── sample_products.json   # seed data for demo
├── core/
│   ├── __init__.py
│   ├── product_schema.py      # Pydantic product model
│   ├── query_engine.py        # sends prompts to Claude API
│   ├── nlp_analyzer.py        # NLP comparison + gap detection
│   └── recommender.py         # generates fix recommendations
├── dashboard/
│   └── app.py                 # Streamlit UI
└── tests/
    └── test_analyzer.py
```

---

## Step-by-Step Build Instructions

### Step 1 — Product Schema (`core/product_schema.py`)

Define a `Product` dataclass using Pydantic:

```python
from pydantic import BaseModel
from typing import Optional, List

class Product(BaseModel):
    name: str
    category: str                  # e.g. "gaming keyboard"
    brand: str
    price: float
    key_features: List[str]        # e.g. ["mechanical switches", "RGB", "TKL layout"]
    description: str
    availability: str              # "in stock" | "out of stock"
    url: Optional[str] = None
```

### Step 2 — Query Engine (`core/query_engine.py`)

Generate consumer-style queries from the product's category and price, then hit the Claude API.

```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

QUERY_TEMPLATES = [
    "What are the best {category} under ${price_ceiling}?",
    "Recommend a good {category} for someone on a budget.",
    "What {category} do most people buy online?",
    "Is {brand} {product_name} a good choice for {category}?",  # direct query
    "How does {brand} {product_name} compare to {brand} {product_name}?",
]

def build_queries(product: Product) -> list[str]:
    """Generate 5 queries: 3 generalized, 1 direct brand mention, 1 comparison query."""
    price_ceiling = round(product.price * 1.25 / 10) * 10  # nearest $10 above price
    return [
        QUERY_TEMPLATES[0].format(category=product.category, price_ceiling=price_ceiling),
        QUERY_TEMPLATES[1].format(category=product.category),
        QUERY_TEMPLATES[2].format(category=product.category),
        QUERY_TEMPLATES[3].format(
            brand=product.brand,
            product_name=product.name,
            category=product.category
        ),
        QUERY_TEMPLATES[4].format(
            brand=product.brand,
            product_name=product.name
        ),
    ]

def query_llm(prompt: str) -> str:
    """Send a single query to Claude and return the text response."""
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def run_all_queries(product: Product) -> dict:
    """Returns dict of {query_string: llm_response} for all templates."""
    queries = build_queries(product)
    return {q: query_llm(q) for q in queries}
```

### Step 3 — NLP Analyzer (`core/nlp_analyzer.py`)

Use `sentence-transformers` for semantic similarity and keyword matching to detect gaps.

```python
from sentence_transformers import SentenceTransformer, util
from core.product_schema import Product
import re

model = SentenceTransformer("all-MiniLM-L6-v2")

def check_visibility(product: Product, llm_response: str) -> dict:
    """
    Returns:
        mentioned (bool): product name or brand appears in response
        similarity_score (float): 0.0–1.0 semantic similarity
        missing_features (list[str]): features present in product but absent from LLM response
        hallucinated_claims (list[str]): sentences in LLM response with low similarity to product description
    """
    response_lower = llm_response.lower()
    
    # 1. Visibility check
    mentioned = (product.name.lower() in response_lower or 
                 product.brand.lower() in response_lower)
    
    # 2. Semantic similarity between product description and LLM response
    prod_embedding = model.encode(product.description, convert_to_tensor=True)
    resp_embedding = model.encode(llm_response, convert_to_tensor=True)
    similarity = float(util.cos_sim(prod_embedding, resp_embedding))
    
    # 3. Missing features — check if each key feature keyword appears in response
    missing_features = [
        feat for feat in product.key_features
        if feat.lower() not in response_lower
    ]
    
    # 4. Hallucination detection — find sentences with very low similarity to product facts
    sentences = re.split(r'(?<=[.!?])\s+', llm_response)
    hallucinated = []
    for sent in sentences:
        if product.brand.lower() in sent.lower() or product.name.lower() in sent.lower():
            sent_emb = model.encode(sent, convert_to_tensor=True)
            score = float(util.cos_sim(prod_embedding, sent_emb))
            if score < 0.25:  # threshold — tune as needed
                hallucinated.append(sent)
    
    return {
        "mentioned": mentioned,
        "similarity_score": round(similarity, 3),
        "missing_features": missing_features,
        "hallucinated_claims": hallucinated,
    }

def aggregate_results(product: Product, query_results: dict) -> dict:
    """Run visibility check across all queries and compute overall scores."""
    analyses = {}
    for query, response in query_results.items():
        analyses[query] = check_visibility(product, response)
    
    visibility_rate = sum(1 for a in analyses.values() if a["mentioned"]) / len(analyses)
    avg_similarity = sum(a["similarity_score"] for a in analyses.values()) / len(analyses)
    all_missing = list(set(
        feat for a in analyses.values() for feat in a["missing_features"]
    ))
    all_hallucinations = [
        h for a in analyses.values() for h in a["hallucinated_claims"]
    ]
    
    return {
        "product_name": product.name,
        "visibility_rate": round(visibility_rate, 2),       # 0.0–1.0
        "avg_accuracy_score": round(avg_similarity, 3),
        "missing_features": all_missing,
        "hallucinated_claims": all_hallucinations,
        "per_query": analyses,
    }
```

### Step 4 — Recommender (`core/recommender.py`)

Use Claude to generate actionable content fixes based on the gap analysis.

```python
import anthropic
from core.product_schema import Product

client = anthropic.Anthropic()

def generate_recommendations(product: Product, analysis: dict) -> str:
    """
    Sends the gap analysis to Claude and asks for specific content improvements
    the business can make to improve AI visibility.
    """
    missing = ", ".join(analysis["missing_features"]) or "none detected"
    hallucinations = "\n".join(analysis["hallucinated_claims"]) or "none detected"
    
    prompt = f"""
You are an AI visibility consultant helping a small business improve how their product 
appears in AI assistant responses.

Product: {product.name} by {product.brand}
Category: {product.category}
Price: ${product.price}
Description: {product.description}
Key Features: {", ".join(product.key_features)}

Analysis Results:
- Visibility Rate (how often AI mentioned the product): {analysis["visibility_rate"] * 100:.0f}%
- Accuracy Score (semantic similarity to real product data): {analysis["avg_accuracy_score"]}
- Features missing from AI responses: {missing}
- Potentially hallucinated claims about this product: {hallucinations}

Please provide:
1. Three specific changes the business can make to their product page or description to improve AI visibility
2. Two changes to address the missing features above
3. One action to correct any hallucinated claims
4. A plain-language explanation of WHY this product is not showing up in AI results

Be specific and actionable. Format as numbered lists under clear headers.
"""
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
```

### Step 5 — Streamlit Dashboard (`dashboard/app.py`)

```python
import streamlit as st
import json
from core.product_schema import Product
from core.query_engine import run_all_queries
from core.nlp_analyzer import aggregate_results
from core.recommender import generate_recommendations

st.set_page_config(page_title="AI Visibility Analyzer", layout="wide")
st.title("🔍 AI Visibility Analyzer")
st.caption("Understand why your product isn't showing up in AI-assisted shopping results.")

# --- Sidebar: Product Input ---
with st.sidebar:
    st.header("Enter Your Product")
    name = st.text_input("Product Name", "MechPro K75 Keyboard")
    brand = st.text_input("Brand", "MechPro")
    category = st.text_input("Category", "gaming keyboard")
    price = st.number_input("Price ($)", value=89.99)
    features_raw = st.text_area("Key Features (one per line)", "mechanical switches\nRGB backlight\nTKL layout\nUSB-C")
    description = st.text_area("Product Description", "The MechPro K75 is a tenkeyless mechanical keyboard with Cherry MX Red switches, per-key RGB lighting, and a detachable USB-C cable. Built for gamers who want a compact, fast, and reliable typing experience.")
    availability = st.selectbox("Availability", ["in stock", "out of stock"])
    run = st.button("Analyze Visibility", type="primary")

# --- Main Panel: Results ---
if run:
    product = Product(
        name=name, brand=brand, category=category, price=price,
        key_features=[f.strip() for f in features_raw.splitlines() if f.strip()],
        description=description, availability=availability
    )
    
    with st.spinner("Querying AI models..."):
        query_results = run_all_queries(product)
    
    with st.spinner("Running NLP analysis..."):
        analysis = aggregate_results(product, query_results)
    
    with st.spinner("Generating recommendations..."):
        recommendations = generate_recommendations(product, analysis)
    
    # --- Score Cards ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Visibility Rate", f"{analysis['visibility_rate']*100:.0f}%", 
                help="How often the AI mentioned your product across all queries")
    col2.metric("Accuracy Score", f"{analysis['avg_accuracy_score']:.2f}/1.0",
                help="Semantic similarity between AI descriptions and your actual product data")
    col3.metric("Missing Features", len(analysis["missing_features"]),
                help="Key features the AI failed to mention")
    
    st.divider()
    
    # --- Per-Query Breakdown ---
    st.subheader("Query-by-Query Breakdown")
    for query, result in analysis["per_query"].items():
        with st.expander(f"{'✅' if result['mentioned'] else '❌'} Query: {query}"):
            st.write(f"**Mentioned:** {'Yes' if result['mentioned'] else 'No'}")
            st.write(f"**Similarity Score:** {result['similarity_score']}")
            if result["missing_features"]:
                st.write(f"**Missing Features:** {', '.join(result['missing_features'])}")
            if result["hallucinated_claims"]:
                st.warning("Potential hallucinations detected:")
                for h in result["hallucinated_claims"]:
                    st.write(f"- {h}")
            # Show raw LLM response
            st.write("**AI Response:**")
            st.write(query_results[query])
    
    st.divider()
    
    # --- Recommendations ---
    st.subheader("💡 Recommendations to Improve Visibility")
    st.markdown(recommendations)
    
    # --- Export ---
    st.divider()
    export_data = {
        "product": product.model_dump(),
        "analysis": analysis,
        "recommendations": recommendations
    }
    st.download_button(
        "Download Full Report (JSON)",
        data=json.dumps(export_data, indent=2),
        file_name=f"{brand}_{name}_visibility_report.json",
        mime="application/json"
    )
```

### Step 6 — Sample Data (`data/sample_products.json`)

```json
[
  {
    "name": "MechPro K75 Keyboard",
    "category": "gaming keyboard",
    "brand": "MechPro",
    "price": 89.99,
    "key_features": ["mechanical switches", "RGB backlight", "TKL layout", "USB-C"],
    "description": "The MechPro K75 is a tenkeyless mechanical keyboard with Cherry MX Red switches, per-key RGB lighting, and a detachable USB-C cable.",
    "availability": "in stock"
  },
  {
    "name": "ClearView UV Protection Window Tint Kit",
    "category": "car window tint",
    "brand": "ClearView",
    "price": 34.99,
    "key_features": ["UV protection", "DIY install", "bubble-free film", "legal tint levels"],
    "description": "ClearView's window tint kit offers 35% VLT UV-blocking film for a clean, professional finish. Pre-cut for most sedan models.",
    "availability": "in stock"
  }
]
```

### Step 7 — Requirements (`requirements.txt`)

```
anthropic>=0.25.0
streamlit>=1.35.0
pydantic>=2.0.0
sentence-transformers>=2.7.0
spacy>=3.7.0
torch>=2.0.0
```

### Step 8 — Run Script (`run.sh`)

```bash
#!/bin/bash
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
python3 -m spacy download en_core_web_sm --quiet

echo "Checking API key..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ERROR: ANTHROPIC_API_KEY environment variable not set."
  echo "Run: export ANTHROPIC_API_KEY=your_key_here"
  exit 1
fi

echo "Starting AI Visibility Analyzer..."
streamlit run dashboard/app.py --server.port 8501

echo "App running at http://localhost:8501"
```

---

## Environment Setup

```bash
# Clone and enter the repo
git clone <your-repo-url>
cd 2026-HBCU-BOTB

# Set your API key
export ANTHROPIC_API_KEY=your_key_here

# Launch everything
chmod +x run.sh
./run.sh
```

### Debug Mode

If you want to demo the app without a Claude key, run:

```bash
DEBUG_MODE=1 ./run.sh
```

In debug mode, the app uses deterministic mock AI responses and mock recommendations instead of live Claude API calls.

---

## Demo Flow (for judges)

1. Launch the app with `./run.sh`
2. In the sidebar, the sample product (MechPro K75) is pre-filled
3. Click **Analyze Visibility**
4. Dashboard shows:
   - Visibility Rate (% of AI queries that mentioned the product)
   - Accuracy Score (how well the AI described it vs. real specs)
   - Per-query breakdown with hallucination flags
   - Actionable recommendations generated by Claude
5. Download the JSON report

---

## Scoring Criteria Alignment

| Rubric Category | How This Prototype Addresses It |
|---|---|
| **Functionality** | Live LLM querying, NLP similarity scoring, hallucination detection, recommendations — all working end-to-end |
| **Feasibility** | Shopify API integration is the natural next step (swap `sample_products.json` for API calls); no scraping required |
| **Innovation** | Combines AEO (AI Engine Optimization) monitoring + NLP gap analysis + LLM-generated fix recommendations in a single pipeline |
| **Ethics Monitoring** | Hallucination detection flags inaccurate AI claims about product features, pricing, or availability |

---

## What's Simulated vs. Real in This Demo

| Component | Status |
|---|---|
| Claude API queries | ✅ Real — live API calls |
| NLP similarity scoring | ✅ Real — sentence-transformers |
| Hallucination detection | ✅ Real — cosine similarity threshold |
| Product data source | 🟡 Simulated — JSON file stands in for Shopify API |
| Multi-LLM comparison | 🟡 Simulated — Claude only; extend with OpenAI/Gemini keys |
| Historical trend tracking | 🔜 Roadmap — add a SQLite layer to store results over time |

---

## Roadmap (Mention in Pitch)

- **Shopify Plugin:** Replace JSON input with live Shopify product API — no scraping needed
- **Multi-LLM Panel:** Query ChatGPT, Gemini, and Perplexity in parallel for cross-model comparison
- **Ranking Score:** Track how often a business moves up in AI results week-over-week
- **Tiered Newsletter Output:** Auto-generate industry reports from aggregated data across all clients
- **Webhook Alerts:** Notify business owners when hallucinations or sudden visibility drops are detected
