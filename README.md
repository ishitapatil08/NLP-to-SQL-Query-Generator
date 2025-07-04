# NLP to SQL Query Generator
## Project Overview
This project is an AI-powered tool that converts plain English questions into SQL queries using LLMs (Large Language Models). It supports both:
## User Interface
![image]()

## Features

- Upload your `.csv` file 📂
- Ask a question in natural language 💬
- See the generated SQL query 💾
- Execute it instantly on your dataset ⚡
- Download the result as `.csv` ⬇️
- Use either **OpenAI's API** or **fully offline model**

##  Installation & Setup
### 1️. Clone the Repository
```bash
git clone https://github.com/ghaihitasha/llm-sql-query-generator.git
cd llm-sql-query-generator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up the `.env` File
Create a `.env` file in the root directory and add your **OpenAI API Key**:
```ini
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Run the Streamlit App
```bash
streamlit run app.py (Using OpenAI)
streamlit run src/app.py(Offline)
```

## Usage
1. Enter your **OpenAI API Key** in the **Project Settings** section or let it load from `.env`.
2. Provide the **database path** to your SQLite file.
3. Enter a natural language query (e.g., "Show all employees who joined after 2020").
4. Click **Generate SQL** to get the SQL query.
5. Validate & Execute the query to see the results.

## Contributing
Pull requests are welcome! If you’d like to contribute, please open an issue first to discuss your changes.
