import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("❌ GOOGLE_API_KEY not found in .env file")

# === Configure Gemini ===
genai.configure(api_key=api_key)
model = genai.GenerativeModel("models/gemini-2.5-flash")

# === Load dataset ===
df = pd.read_csv("data/olist_merged_full.csv")
# Ensure timestamp is in datetime format
df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')


# === Function to safely run generated code ===
def safe_execute(code):
    try:
        # Only allow pandas/numpy-like commands, no dangerous ops
        allowed_globals = {"pd": pd, "df": df}
        result = eval(code, {"__builtins__": {}}, allowed_globals)
        return result
    except Exception as e:
        return f"⚠️ Error executing code: {e}"

# === Ask AI Function ===
def ask_gemini(question):
    prompt = f"""
You are an expert data analyst. You are working on an e-commerce dataset (df) with the following columns:
{', '.join(df.columns[:20])} ...

Answer the user query by writing a single valid Python (Pandas) expression that uses df to compute the answer.

User question:
\"\"\"{question}\"\"\"

Rules:
- Use Pandas methods only (e.g., groupby, mean, sort_values, etc.).
- Never import or print anything.
- Return only the final variable (no explanations).
"""

    response = model.generate_content(prompt)
    code = response.text.strip().replace("```python", "").replace("```", "")
    print("\n🔹 Generated Code:\n", code)

    result = safe_execute(code)
    return result


# === Main interactive loop ===
if __name__ == "__main__":
    print("🤖 Gemini Data Analyst Ready! Type 'exit' to quit.\n")

    while True:
        q = input("Ask your question: ")
        if q.lower() == "exit":
            print("👋 Goodbye!")
            break

        answer = ask_gemini(q)
        print("\n💬 Result:\n", answer, "\n")
