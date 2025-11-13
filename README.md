# 🌊 Maersk GenAI E-Commerce Insights Dashboard

**Author:** Keerthan Anumalasetty  
**Duration:** 5–7 minute demo video (link below)  
**Project Goal:** Build an AI-powered data analytics dashboard that converts **natural-language questions** into pandas code using **Google Gemini**, executes them safely, and visualizes the results.

---

## 🎬 Demo Video
📺 [Unlisted YouTube or Google Drive Link Here]

---

## 🚀 Overview

This project demonstrates how **Generative AI can assist in business analytics** by allowing users to ask plain-English questions like:

> “Which product category had the highest sales last quarter?”

The system uses **Gemini 2.5 Flash** to generate the corresponding pandas query, executes it safely, and displays insights through charts — all inside an interactive **Streamlit dashboard**.

---

## 🧠 Features

✅ Natural language → pandas code using Google Gemini  
✅ Safe execution with code sanitization (`safe_execute`)  
✅ Automatic visualizations (bar/grouped charts)  
✅ KPI cards for revenue, orders, and ratings  
✅ Quick Insights (pre-defined analytics buttons)  
✅ Chat history with previous queries  
✅ Full state name mapping for charts  
✅ Dark theme with responsive design  

---

## ⚙️ Tech Stack

| Component | Technology |
|------------|-------------|
| **Frontend** | Streamlit |
| **Language** | Python 3.11 |
| **AI Model** | Google Gemini 2.5 Flash |
| **Data Processing** | pandas, numpy |
| **Visualization** | matplotlib |
| **Environment** | python-dotenv (API key) |
| **Version Control** | Git + GitHub |

---

## 🏗️ Architecture

User Query
↓
Streamlit UI (input + history)
↓
Gemini Model (google-generativeai)
↓
Generated pandas code
↓
safe_execute() → Sanitized execution
↓
pandas → Chart → Streamlit output

yaml
Copy code

---

## 🧩 Key Components

### 🔹 `ask_gemini(question)`
- Sends a structured prompt to Gemini.  
- Interprets *“last quarter”* as the **last 3 months** for stable results.  
- Returns a clean pandas expression (no prints or imports).

### 🔹 `safe_execute(code)`
- Cleans and sanitizes AI-generated code.  
- Prevents arbitrary execution.  
- Handles `.idxmax()` errors, empty data, and syntax issues gracefully.  
- Returns DataFrame, Series, or string result for visualization.

### 🔹 Visual Layer
- Detects if result is single-column or grouped multi-column.  
- Displays a bar or grouped chart automatically.  
- Orders bars by value, not alphabetically.  
- Maps state codes → full names.

---

## 📊 Dataset
**Source:** Brazilian E-Commerce Olist dataset  
**Format:** Merged CSV file (`olist_merged_full.csv`)  
**Size:** ~100K orders, 44+ columns  
**Added Data:** category name translation and customer geolocation

---

## 🧪 How to Run

### 1️⃣ Clone & Setup
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
2️⃣ Add your Gemini API key
Create a .env file in project root:

ini
Copy code
GOOGLE_API_KEY=your_api_key_here
3️⃣ Run the App
bash
Copy code
streamlit run streamlit_app.py
Then open http://localhost:8501.

🧮 Example Queries
Example	Description
“Which product category had the highest sales last quarter?”	Dynamic 3-month filter query
“Average delivery time per state”	Date difference aggregation
“2017 sales vs 2018 sales per state”	Grouped multi-column comparison
“Which state has the most loyal customers?”	Uses average review score

🔒 Design Decisions
Safe sandboxed execution environment for model output

Auto-sorting results numerically (not alphabetically)

Handled missing timestamp conversions gracefully

Dark-themed UI for readability and uniform branding

Local caching of data with @st.cache_data

💡 Future Improvements
Deploy on Streamlit Cloud or Hugging Face Spaces

Persistent user chat history using SQLite

Live database connection instead of CSV

📁 Project Structure
📦 maersk_genai_project
├── data/
│   └── olist_merged_full.csv        # Local dataset (excluded in .gitignore)
├── streamlit_app.py                 # Main application
├── ai_query_engine.py      # Supporting scripts
├── README.md
└── .env (local only)

Cost-optimized Gemini API usage

Role-based dashboards (admin / analyst)
