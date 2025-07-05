import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os

# Load Hugging Face model
@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen-350M-mono", use_auth_token=False)
    model = AutoModelForCausalLM.from_pretrained("Salesforce/codegen-350M-mono", use_auth_token=False)
    return tokenizer, model

tokenizer, model = load_model()

st.set_page_config(page_title="AI SQL Generator", layout="wide")
st.title("🤖 Natural Language to SQL using AI")

# === Convert SQL file to DB if needed ===
sql_file = "customer.sql"
db_file = "customer.db"

if not os.path.exists(db_file):
    if os.path.exists(sql_file):
        with open(sql_file, "r") as f:
            sql_script = f.read()
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.executescript(sql_script)
        conn.commit()
        conn.close()
        st.success(f"Created SQLite DB from {sql_file}")
    else:
        st.error("Neither company.db nor company.sql found.")
        st.stop()
else:
    st.success("Loaded existing company.db")

# === Get schema (internally only) ===
def get_schema_and_relationships(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    schema_str = ""
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for (table_name,) in tables:
        cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
        col_names = [col[1] for col in cols]
        schema_str += f"Table: {table_name} ({', '.join(col_names)})\n"
        fkeys = cursor.execute(f"PRAGMA foreign_key_list({table_name});").fetchall()
        for fkey in fkeys:
            schema_str += f"Foreign Key: {table_name}.{fkey[3]} -> {fkey[2]}.{fkey[4]}\n"
    conn.close()
    return schema_str.strip()

schema_info = get_schema_and_relationships(db_file)

# === Generate SQL ===
def generate_sql_from_nlp(schema_info, question):
    prompt = (
        f"### SQLite tables, with columns and foreign keys:\n{schema_info}\n\n"
        f"### User question:\n{question}\n\n### SQL query:\n"
    )
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(
        inputs.input_ids,
        max_new_tokens=128,
        temperature=0.2,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id
    )
    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    sql = full_output[len(prompt):].strip()
    return sql

# === UI ===
question = st.text_input("Ask a question about the company database:")
if question:
    if st.button("Generate SQL & Run"):
        with st.spinner("Generating SQL..."):
            sql_query = generate_sql_from_nlp(schema_info, question)

        st.header("🧠 Generated SQL Query")
        st.code(sql_query, language="sql")

        try:
            conn = sqlite3.connect(db_file)
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            if df.empty:
                st.warning("⚠️ Query returned no results.")
            else:
                st.success("✅ Query executed successfully!")
                st.dataframe(df)

                numeric_cols = df.select_dtypes(include="number").columns
                if len(numeric_cols) > 0:
                    st.subheader("📊 Numeric Column Visualizations")
                    for col in numeric_cols:
                        st.markdown(f"**Histogram of `{col}`**")
                        sns.histplot(df[col], kde=True)
                        st.pyplot(plt)
                        plt.clf()
        except Exception as e:
            st.error(f"❌ SQL execution error: {e}")
