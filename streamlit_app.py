import os, time
import pandas as pd
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np

# ====== CONFIGURATION ======
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash")

# ====== STATE NAME MAPPING ======
state_mapping = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins"
}

# ====== DATA LOADING ======
@st.cache_data
def load_data():
    path = "data/olist_merged_full.csv"
    if not os.path.exists(path):
        raise FileNotFoundError("Place merged file as data/olist_merged_full.csv")
    df = pd.read_csv(path)
    for col in ["order_purchase_timestamp", "order_delivered_customer_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

df = load_data()

# ====== PAGE CONFIG ======
st.set_page_config(page_title="Maersk GenAI Insights", page_icon="🌊", layout="wide")

# ====== SESSION STATE ======
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "question" not in st.session_state:
    st.session_state["question"] = ""

# ====== DARK THEME CSS ======
st.markdown("""
    <style>
        .stApp {
            background-color: #0a192f;
            color: #f0f6fc;
            font-family: "Segoe UI", sans-serif;
        }
        div[data-testid="metric-container"] {
            background-color: #112240;
            border: 1px solid #64ffda;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.4);
            color: #f0f6fc !important;
        }
        h1, h2, h3, h4 {
            color: #64ffda !important;
        }
        .stMetricLabel {
            color: #f0f6fc !important;
        }
        .stMetricValue {
            color: #ffffff !important;
        }
        .sidebar .sidebar-content {
            background-color: #112240;
        }
    </style>
""", unsafe_allow_html=True)

# ====== HEADER ======
st.markdown("""
    <div style='text-align:center; padding:15px; background-color:#112240; border-radius:10px;'>
        <h1 style='color:#64ffda;'>🌊 Maersk GenAI E-Commerce Insights Dashboard</h1>
        <h4 style='color:#ccd6f6;'>AI-powered analytics assistant using Gemini 2.5 Flash</h4>
    </div>
""", unsafe_allow_html=True)

# ====== KPI SECTION ======
st.markdown("### 📈 Key Performance Indicators (KPIs)")
col1, col2, col3 = st.columns(3)
try:
    with col1:
        total_orders = df["order_id"].nunique()
        st.metric("📦 Total Orders", f"{total_orders:,}")
    with col2:
        total_revenue = df["payment_value"].sum()
        st.metric("💰 Total Revenue (R$)", f"{total_revenue:,.0f}")
    with col3:
        avg_review = df["review_score"].mean()
        st.metric("⭐ Avg Review Score", f"{avg_review:.2f}")
except Exception as e:
    st.warning(f"⚠️ Could not calculate KPIs: {e}")

st.markdown("<hr style='border:1px solid #64ffda;'>", unsafe_allow_html=True)

# ====== SIDEBAR CHAT HISTORY ======
st.sidebar.header("💬 Query History")
if st.session_state["chat_history"]:
    for chat in reversed(st.session_state["chat_history"][-5:]):
        st.sidebar.markdown(f"**🧠 Q:** {chat.get('question', '')}")
        r = chat.get("result", "")
        if isinstance(r, str):
            st.sidebar.markdown(f"**✅ A:** {r}")
        elif isinstance(r, (int, float)):
            st.sidebar.markdown(f"**✅ A:** {r:,}")
        else:
            st.sidebar.markdown("**📊 A:** (See chart in main view)")
        st.sidebar.markdown("---")
else:
    st.sidebar.info("No queries yet. Ask a question to start.")

if st.sidebar.button("🗑️ Clear History"):
    st.session_state["chat_history"] = []

# ====== SIDEBAR QUICK INSIGHTS ======
st.sidebar.header("⚡ Quick Insights")
questions = [
    "Which product category had the highest sales last quarter?",
    "Top 5 cities by total revenue",
    "Average delivery time per state",
    "Which state has the most loyal customers?",
    "2017 sales vs 2018 sales per state",
    "Bottom 5 states in sales"
]
for q in questions:
    if st.sidebar.button(q):
        st.session_state["question"] = q

# ====== QUESTION INPUT ======
st.markdown("### 💬 Ask your own question")
user_question = st.text_input(
    "Type your question here:",
    st.session_state.get("question", ""),
    placeholder="e.g., Show top 5 categories by sales"
)

# ====== SAFE EXECUTION ======

def safe_execute(code):
    """
    Robust executor for Gemini-generated pandas expressions.
    - Cleans code (removes fences, line-continuations).
    - Tries to exec the expression normally.
    - If exec fails due to idxmax/argmax on empty, attempts a safe fallback:
        * evaluate the same expression but without .idxmax() and pick .nlargest(1)
    - Returns friendly messages for empty results.
    """
    try:
        # 1) sanitize Gemini output
        raw = code or ""
        raw = raw.replace("```python", "").replace("```", "").replace("`", "").strip()
        raw = raw.replace("\\\n", " ")            # remove backslash line-continuations
        raw = " ".join(raw.splitlines())          # flatten multiline code to one line
        raw = raw.replace(".to_period('Q') - 1", ".to_period('Q')")  # sanitize quarter math

        local = {"pd": pd, "df": df.copy(), "np": np}

        # 2) Try normal execution
        try:
            exec(f"result = {raw}", local)
            result = local.get("result", None)
        except Exception as exec_err:
            # 3) If it's an idxmax/argmax type error and code uses .idxmax(), try fallback
            err_text = str(exec_err).lower()
            if (".idxmax()" in raw) or ("argmax" in err_text) or ("idxmax" in err_text):
                try:
                    # attempt to compute the underlying aggregation/series without .idxmax()
                    # strategy: replace ".idxmax()" with "" to get the Series/DataFrame, then choose largest
                    series_expr = raw.replace(".idxmax()", "")
                    # also if code contains ".nlargest(" keep as is (avoid infinite loop)
                    exec(f"tmp = {series_expr}", local)
                    tmp = local.get("tmp", None)

                    # If tmp is a Series or DataFrame with numeric columns, try to pick the top index safely
                    if isinstance(tmp, pd.Series):
                        if tmp.dropna().empty:
                            return "⚠️ No data found for that period — the filtered series is empty."
                        else:
                            top_idx = tmp.dropna().nlargest(1).index[0]
                            result = top_idx
                    elif isinstance(tmp, pd.DataFrame):
                        # If DataFrame, attempt to sum numeric cols into a Series and pick top
                        numeric = tmp.select_dtypes(include="number")
                        if numeric.shape[1] == 0 or numeric.sum(axis=1).dropna().empty:
                            return "⚠️ No numeric data found in the result to determine the top category."
                        summed = numeric.sum(axis=1)
                        top_idx = summed.nlargest(1).index[0]
                        result = top_idx
                    else:
                        return f"⚠️ Fallback failed: expression produced type {type(tmp)}"
                except Exception as fallback_err:
                    return f"⚠️ Error in fallback idxmax handling: {fallback_err}"
            else:
                # not an idxmax-specific problem, return the original execution error
                return f"⚠️ Error executing code: {exec_err}"
        # 4) Post-process successful result
        # Map state codes (if single string)
        if isinstance(result, str) and result in state_mapping:
            result = state_mapping[result]

        # If result is empty Series/DataFrame -> friendly message
        if isinstance(result, (pd.Series, pd.DataFrame)) and len(result) == 0:
            return "⚠️ Query returned no rows (empty result). Try a wider time window."

        # If DataFrame has index name (groupby unstack cases), reset index to help plotting
        if isinstance(result, pd.DataFrame) and result.index.name:
            result = result.reset_index()

        return result

    except Exception as e:
        # Last-resort catch-all
        return f"⚠️ Unexpected error in safe_execute: {e}"


# ====== GEMINI QUERY FUNCTION ======
def ask_gemini(question):
    prompt = f"""
You are a pandas data analyst.

Dataset (df) has columns:
category_name_en, payment_value, order_purchase_timestamp,
order_delivered_customer_date, review_score, customer_city, customer_state.

Task:
Write ONE valid pandas expression using df to answer the question below.

Question:
\"\"\"{question}\"\"\"

Guidelines:
1. Always convert 'order_purchase_timestamp' to datetime when needed.
2. If the question mentions "last quarter", interpret it as the **last 3 months**
   from the most recent date in the dataset:
      cutoff = df['order_purchase_timestamp'].max() - pd.DateOffset(months=3)
3. Use vectorized pandas syntax, no prints or imports.
4. Prefer nlargest(1).index[0] instead of idxmax() for stability.
5. Return only the pandas expression (no explanation text).
"""
    response = model.generate_content(prompt)
    return response.text.strip()


# ====== MAIN ======
# ====== MAIN ======
if user_question:
    thinking_msg = st.empty()
    thinking_msg.markdown("### 🤖 Thinking with Gemini... Please wait ⏳")

    with st.spinner("Analyzing your question and generating insights..."):
        time.sleep(1.0)
        code = ask_gemini(user_question)

        typed = ""
        code_display = st.empty()
        for ch in code:
            typed += ch
            code_display.code(typed, language="python")
            time.sleep(0.002)

        result = safe_execute(code)

    thinking_msg.empty()  # remove the "Thinking" message

    st.session_state["chat_history"].append(
        {"question": user_question, "code": code, "result": result}
    )
    st.markdown("### 📊 Result")

    # ---- Display result (unchanged plotting logic) ----
    if isinstance(result, pd.DataFrame):
        st.dataframe(result)
        try:
            cols = list(result.columns)
            if len(cols) >= 3:  # e.g., 2017 vs 2018 comparison
                x = cols[0]
                groups = cols[1:]
                fig, ax = plt.subplots(figsize=(8, 4.5))
                xvals = np.arange(len(result))
                width = 0.8 / len(groups)
                for i, g in enumerate(groups):
                    ax.bar(xvals + i * width, result[g], width, label=str(g))
                ax.set_xticks(xvals + width * len(groups) / 2)
                ax.set_xticklabels(result[x], rotation=45, ha="right")
                ax.legend(facecolor="#112240", labelcolor="#64ffda")
                ax.set_facecolor("#0a192f")
                ax.set_title("Grouped Comparison", color="#64ffda")
                plt.xticks(color="#ccd6f6")
                plt.yticks(color="#ccd6f6")
                st.pyplot(fig)
            elif len(cols) == 2:
                result.columns = ["Label", "Value"]
                if result["Label"].iloc[0] in state_mapping.keys():
                    result["Label"] = result["Label"].map(state_mapping)
                result = result.sort_values("Value", ascending=False)
                fig, ax = plt.subplots(figsize=(8, 4.5))
                ax.bar(result["Label"], result["Value"], color="#64ffda")
                ax.set_facecolor("#0a192f")
                ax.set_title("Result Visualization", color="#64ffda")
                plt.xticks(rotation=45, color="#ccd6f6")
                plt.yticks(color="#ccd6f6")
                st.pyplot(fig)
        except Exception as e:
            st.write(f"⚠️ Plotting error: {e}")

    elif isinstance(result, pd.Series):
        try:
            result = result.sort_values(ascending=False)
            result.index = [state_mapping.get(x, x) for x in result.index]
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.bar(result.index, result.values, color="#64ffda")
            ax.set_facecolor("#0a192f")
            ax.set_title("Result Visualization", color="#64ffda")
            plt.xticks(rotation=45, color="#ccd6f6")
            plt.yticks(color="#ccd6f6")
            st.pyplot(fig)
        except Exception as e:
            st.write(f"⚠️ Plotting error: {e}")
    else:
        st.success(result)


# ====== FOOTER ======
st.markdown("""
<hr>
<p style='text-align:center; color:#64ffda;'>Built with ❤️ using Python, Streamlit & Gemini 2.5 Flash — Maersk AI/ML Intern Assignment</p>
""", unsafe_allow_html=True)
