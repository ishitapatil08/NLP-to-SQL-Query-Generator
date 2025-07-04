import streamlit as st
import pandas as pd
import sqlite3
import re
import io
import numpy as np

def generate_sql_from_nlp(query, df):
    """Advanced rule-based SQL generation - works offline!"""
    query = query.lower().strip()
    columns = list(df.columns)
    numeric_cols = list(df.select_dtypes(include=['number']).columns)
    text_cols = list(df.select_dtypes(include=['object', 'string']).columns)
    
    # Helper function to find mentioned columns
    def find_mentioned_columns(text):
        mentioned = []
        for col in columns:
            if col.lower() in text.lower():
                mentioned.append(col)
        return mentioned
    
    # Extract numbers from query
    numbers = re.findall(r'\d+', query)
    
    # ===== AGGREGATION QUERIES =====
    if any(word in query for word in ['count', 'how many', 'number of']):
        mentioned_cols = find_mentioned_columns(query)
        
        if any(word in query for word in ['by', 'group', 'each', 'per']):
            # GROUP BY query
            if mentioned_cols:
                group_col = mentioned_cols[0]
                return f"SELECT {group_col}, COUNT(*) as count FROM data GROUP BY {group_col} ORDER BY count DESC;"
            elif text_cols:
                return f"SELECT {text_cols[0]}, COUNT(*) as count FROM data GROUP BY {text_cols[0]} ORDER BY count DESC;"
        
        # Simple count
        if mentioned_cols:
            return f"SELECT COUNT(*) as total_count FROM data WHERE {mentioned_cols[0]} IS NOT NULL;"
        return "SELECT COUNT(*) as total_count FROM data;"
    
    elif any(word in query for word in ['average', 'avg', 'mean']):
        mentioned_cols = [col for col in find_mentioned_columns(query) if col in numeric_cols]
        
        if mentioned_cols:
            col = mentioned_cols[0]
            if any(word in query for word in ['by', 'group', 'each', 'per']):
                group_cols = [col for col in find_mentioned_columns(query) if col in text_cols]
                if group_cols:
                    return f"SELECT {group_cols[0]}, AVG({col}) as avg_{col} FROM data GROUP BY {group_cols[0]} ORDER BY avg_{col} DESC;"
            return f"SELECT AVG({col}) as avg_{col} FROM data;"
        elif numeric_cols:
            return f"SELECT AVG({numeric_cols[0]}) as avg_{numeric_cols[0]} FROM data;"
    
    elif any(word in query for word in ['sum', 'total', 'add up']):
        mentioned_cols = [col for col in find_mentioned_columns(query) if col in numeric_cols]
        
        if mentioned_cols:
            col = mentioned_cols[0]
            if any(word in query for word in ['by', 'group', 'each', 'per']):
                group_cols = [col for col in find_mentioned_columns(query) if col in text_cols]
                if group_cols:
                    return f"SELECT {group_cols[0]}, SUM({col}) as total_{col} FROM data GROUP BY {group_cols[0]} ORDER BY total_{col} DESC;"
            return f"SELECT SUM({col}) as total_{col} FROM data;"
        elif numeric_cols:
            return f"SELECT SUM({numeric_cols[0]}) as total_{numeric_cols[0]} FROM data;"
    
    # ===== MIN/MAX QUERIES =====
    elif any(word in query for word in ['max', 'maximum', 'highest', 'largest', 'biggest']):
        mentioned_cols = [col for col in find_mentioned_columns(query) if col in numeric_cols]
        
        if mentioned_cols:
            col = mentioned_cols[0]
            if 'show' in query or 'display' in query or 'record' in query:
                return f"SELECT * FROM data WHERE {col} = (SELECT MAX({col}) FROM data);"
            return f"SELECT MAX({col}) as max_{col} FROM data;"
        elif numeric_cols:
            return f"SELECT * FROM data ORDER BY {numeric_cols[0]} DESC LIMIT 1;"
    
    elif any(word in query for word in ['min', 'minimum', 'lowest', 'smallest']):
        mentioned_cols = [col for col in find_mentioned_columns(query) if col in numeric_cols]
        
        if mentioned_cols:
            col = mentioned_cols[0]
            if 'show' in query or 'display' in query or 'record' in query:
                return f"SELECT * FROM data WHERE {col} = (SELECT MIN({col}) FROM data);"
            return f"SELECT MIN({col}) as min_{col} FROM data;"
        elif numeric_cols:
            return f"SELECT * FROM data ORDER BY {numeric_cols[0]} ASC LIMIT 1;"
    
    # ===== FILTERING QUERIES =====
    elif any(word in query for word in ['where', 'filter', 'only', 'just']):
        mentioned_cols = find_mentioned_columns(query)
        
        # Look for comparison operators
        if '>' in query:
            if mentioned_cols and mentioned_cols[0] in numeric_cols:
                col = mentioned_cols[0]
                num_match = re.search(r'>\s*(\d+)', query)
                if num_match:
                    return f"SELECT * FROM data WHERE {col} > {num_match.group(1)};"
                return f"SELECT * FROM data WHERE {col} > (SELECT AVG({col}) FROM data);"
        
        elif '<' in query:
            if mentioned_cols and mentioned_cols[0] in numeric_cols:
                col = mentioned_cols[0]
                num_match = re.search(r'<\s*(\d+)', query)
                if num_match:
                    return f"SELECT * FROM data WHERE {col} < {num_match.group(1)};"
                return f"SELECT * FROM data WHERE {col} < (SELECT AVG({col}) FROM data);"
        
        elif '=' in query or 'equals' in query:
            if mentioned_cols:
                col = mentioned_cols[0]
                return f"SELECT * FROM data WHERE {col} IS NOT NULL;"
        
        # Text filtering
        if mentioned_cols:
            return f"SELECT * FROM data WHERE {mentioned_cols[0]} IS NOT NULL;"
    
    # ===== SORTING QUERIES =====
    elif any(word in query for word in ['top', 'first', 'highest', 'best']):
        limit = numbers[0] if numbers else "10"
        mentioned_cols = find_mentioned_columns(query)
        
        if mentioned_cols and mentioned_cols[0] in numeric_cols:
            return f"SELECT * FROM data ORDER BY {mentioned_cols[0]} DESC LIMIT {limit};"
        elif numeric_cols:
            return f"SELECT * FROM data ORDER BY {numeric_cols[0]} DESC LIMIT {limit};"
        else:
            return f"SELECT * FROM data LIMIT {limit};"
    
    elif any(word in query for word in ['bottom', 'last', 'worst']):
        limit = numbers[0] if numbers else "10"
        mentioned_cols = find_mentioned_columns(query)
        
        if mentioned_cols and mentioned_cols[0] in numeric_cols:
            return f"SELECT * FROM data ORDER BY {mentioned_cols[0]} ASC LIMIT {limit};"
        elif numeric_cols:
            return f"SELECT * FROM data ORDER BY {numeric_cols[0]} ASC LIMIT {limit};"
        else:
            return f"SELECT * FROM data LIMIT {limit};"
    
    # ===== SPECIFIC COLUMN QUERIES =====
    elif any(word in query for word in ['show', 'display', 'get', 'list']):
        mentioned_cols = find_mentioned_columns(query)
        
        if mentioned_cols:
            if len(mentioned_cols) == 1:
                return f"SELECT {mentioned_cols[0]} FROM data WHERE {mentioned_cols[0]} IS NOT NULL;"
            else:
                cols = ', '.join(mentioned_cols)
                return f"SELECT {cols} FROM data;"
        
        # Show all with limit
        limit = numbers[0] if numbers else "10"
        return f"SELECT * FROM data LIMIT {limit};"
    
    # ===== UNIQUE/DISTINCT QUERIES =====
    elif any(word in query for word in ['unique', 'distinct', 'different']):
        mentioned_cols = find_mentioned_columns(query)
        
        if mentioned_cols:
            return f"SELECT DISTINCT {mentioned_cols[0]} FROM data ORDER BY {mentioned_cols[0]};"
        elif text_cols:
            return f"SELECT DISTINCT {text_cols[0]} FROM data ORDER BY {text_cols[0]};"
    
    # ===== DEFAULT FALLBACK =====
    else:
        # Try to be smart about what user wants
        if any(word in query for word in ['all', 'everything', 'data']):
            return "SELECT * FROM data;"
        
        limit = numbers[0] if numbers else "10"
        return f"SELECT * FROM data LIMIT {limit};"

def get_query_explanation(sql_query):
    """Explain what the SQL query does"""
    sql_lower = sql_query.lower()
    
    if 'count(*)' in sql_lower:
        if 'group by' in sql_lower:
            return "📊 Counting records grouped by category"
        return "📊 Counting total number of records"
    
    elif 'avg(' in sql_lower:
        return "📊 Calculating average values"
    
    elif 'sum(' in sql_lower:
        return "📊 Calculating sum/total"
    
    elif 'max(' in sql_lower:
        return "📊 Finding maximum values"
    
    elif 'min(' in sql_lower:
        return "📊 Finding minimum values"
    
    elif 'order by' in sql_lower and 'desc' in sql_lower:
        return "📊 Showing records sorted from highest to lowest"
    
    elif 'order by' in sql_lower and 'asc' in sql_lower:
        return "📊 Showing records sorted from lowest to highest"
    
    elif 'where' in sql_lower:
        return "📊 Filtering records based on conditions"
    
    elif 'distinct' in sql_lower:
        return "📊 Showing unique values"
    
    elif 'group by' in sql_lower:
        return "📊 Grouping records by category"
    
    else:
        return "📊 Displaying data records"

# ====== 🚀 Streamlit UI ======
st.set_page_config(page_title="🧠 Smart NLP to SQL (Offline)", layout="centered")
st.title("🧠 Smart Natural Language to SQL")
st.markdown("*✨ Works completely offline - no API keys needed!*")

# ====== FILE UPLOAD ======
uploaded_file = st.file_uploader("📂 Upload a CSV file", type=["csv"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("✅ CSV loaded successfully!")
        
        # Show data preview
        st.subheader("📊 Data Preview")
        st.dataframe(df.head())
        
        # Show data info
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📋 **Rows:** {len(df)}")
            st.info(f"📊 **Columns:** {len(df.columns)}")
        
        with col2:
            numeric_cols = df.select_dtypes(include=['number']).columns
            text_cols = df.select_dtypes(include=['object', 'string']).columns
            st.info(f"🔢 **Numeric:** {len(numeric_cols)}")
            st.info(f"📝 **Text:** {len(text_cols)}")
        
        # Show column details
        with st.expander("📋 Column Details"):
            st.write("**All Columns:**", ", ".join(df.columns))
            if len(numeric_cols) > 0:
                st.write("**Numeric Columns:**", ", ".join(numeric_cols))
            if len(text_cols) > 0:
                st.write("**Text Columns:**", ", ".join(text_cols))
        
    except Exception as e:
        st.error(f"❌ Error reading CSV: {e}")
        df = None
else:
    df = None

# ====== QUERY INPUT ======
user_input = st.text_input("💬 Ask a question about your data:", placeholder="e.g., Count all rows, Show top 10 records, What's the average salary?")

# ====== EXAMPLE QUERIES ======
with st.expander("💡 Example Queries"):
    if df is not None:
        cols = list(df.columns)
        numeric_cols = list(df.select_dtypes(include=['number']).columns)
        
        st.markdown("**📊 Aggregation Examples:**")
        st.write(f"• Count all rows")
        st.write(f"• Count by {cols[0] if cols else 'category'}")
        if numeric_cols:
            st.write(f"• Average {numeric_cols[0]}")
            st.write(f"• Sum of {numeric_cols[0]}")
            st.write(f"• Maximum {numeric_cols[0]}")
        
        st.markdown("**🔍 Filtering Examples:**")
        st.write(f"• Show top 10 records")
        if numeric_cols:
            st.write(f"• Show where {numeric_cols[0]} > 100")
        st.write(f"• Show unique {cols[0] if cols else 'values'}")
        
        st.markdown("**📋 Display Examples:**")
        st.write(f"• Show all data")
        if len(cols) > 1:
            st.write(f"• Show {cols[0]} and {cols[1]}")
    else:
        st.markdown("""
        **📊 Aggregation Examples:**
        • Count all rows
        • Count by category
        • Average salary
        • Sum of sales
        • Maximum price
        
        **🔍 Filtering Examples:**
        • Show top 10 records
        • Show where age > 30
        • Show unique departments
        
        **📋 Display Examples:**
        • Show all data
        • Show name and age
        """)

# ====== QUERY PROCESSING ======
if st.button("🚀 Generate SQL & Run", type="primary"):
    if df is None:
        st.warning("⚠️ Please upload a CSV file first.")
    elif not user_input.strip():
        st.warning("⚠️ Please enter a question about your data.")
    else:
        with st.spinner("🤖 Generating SQL..."):
            # Generate SQL using our smart rule-based system
            sql_query = generate_sql_from_nlp(user_input, df)
            
            # Show the generated SQL
            st.subheader("🧾 Generated SQL")
            st.code(sql_query, language="sql")
            
            # Show explanation
            explanation = get_query_explanation(sql_query)
            st.info(f"**What this does:** {explanation}")
            
            # Execute the SQL
            try:
                with st.spinner("⚡ Running query..."):
                    conn = sqlite3.connect(":memory:")
                    df.to_sql("data", conn, index=False, if_exists="replace")
                    query_result = pd.read_sql_query(sql_query, conn)
                    conn.close()

                st.success("✅ Query executed successfully!")
                
                # Show results
                st.subheader("📊 Results")
                st.dataframe(query_result)
                
                # Show result stats
                st.info(f"📈 **Result:** {len(query_result)} rows × {len(query_result.columns)} columns")
                
                # Download button
                csv_buffer = io.StringIO()
                query_result.to_csv(csv_buffer, index=False)
                st.download_button(
                    "⬇️ Download Results as CSV", 
                    csv_buffer.getvalue(), 
                    file_name="query_results.csv", 
                    mime="text/csv"
                )

            except Exception as e:
                st.error(f"❌ SQL Execution Error: {e}")
                
                # Show debugging help
                st.info("💡 **Debugging Tips:**")
                st.write("• Check if column names are correct")
                st.write("• Try a simpler query")
                st.write("• Make sure numeric operations are on numeric columns")

# ====== MANUAL SQL SECTION ======
st.markdown("---")
st.subheader("🛠️ Manual SQL Query")
st.write("Want to write SQL directly? Try it here!")

manual_sql = st.text_area("Enter your SQL query:", 
                         value="SELECT * FROM data LIMIT 10;",
                         height=100)

if st.button("🔧 Run Manual SQL"):
    if df is None:
        st.warning("⚠️ Please upload a CSV file first.")
    elif not manual_sql.strip():
        st.warning("⚠️ Please enter a SQL query.")
    else:
        try:
            conn = sqlite3.connect(":memory:")
            df.to_sql("data", conn, index=False, if_exists="replace")
            manual_result = pd.read_sql_query(manual_sql, conn)
            conn.close()
            
            st.success("✅ Manual query executed!")
            st.dataframe(manual_result)
            
            # Download button for manual results
            csv_buffer = io.StringIO()
            manual_result.to_csv(csv_buffer, index=False)
            st.download_button(
                "⬇️ Download Manual Results", 
                csv_buffer.getvalue(), 
                file_name="manual_results.csv", 
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"❌ Manual SQL Error: {e}")

# ====== SIDEBAR INFO ======
st.sidebar.title("ℹ️ How It Works")
st.sidebar.markdown("""
### 🧠 Smart Rule-Based SQL Generation
This app uses advanced pattern matching to convert your natural language into SQL queries.

### 🎯 Supported Query Types
- **Aggregation**: count, average, sum, max, min
- **Filtering**: where, greater than, less than
- **Sorting**: top, bottom, highest, lowest
- **Grouping**: count by, average by
- **Display**: show, list, all data

### 💡 Tips for Better Results
1. **Be specific**: Mention column names
2. **Use keywords**: "count", "average", "top 10"
3. **Include numbers**: "top 5", "greater than 100"
4. **Reference columns**: Use exact column names from your data

### ✨ Features
- ✅ Works 100% offline
- ✅ No API keys required
- ✅ Smart column detection
- ✅ Handles complex queries
- ✅ Detailed explanations
""")


st.sidebar.markdown("Created by Ishita Patil")