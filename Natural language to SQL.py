import streamlit as st
import requests
import mysql.connector
import re

# Main class for the application.
class SQLGeneratorApp:
    global sql_output_text
    def __init__(self):
        self.title = st.title("Natural Language to SQL")
        self.db_name = st.text_input("Database Name:")
        self.db_user = st.text_input("Database User:")
        self.db_password = st.text_input("Database Password:", type="password")
        self.user_input = st.text_input("Enter a natural language query:")
        self.status_button = st.markdown('',unsafe_allow_html=True)
        self.sql_output_text = st.text("Generated Query will show here!")
        
        if st.button("Generate SQL Query"):
            self.generate_sql_query()
    # Gets user inputs from Streamlit and calls the OpenAI key to send the query as a prompt.
    def generate_sql_query(self):
        db_name = self.db_name
        db_user = self.db_user
        db_password = self.db_password
        user_input = self.user_input

        openai_url = "https://api.pawan.krd/v1/completions"  # Replace with your reverse proxy URL
        openai_api_key = "pk-DRZbCkIrUhcsuUXdgCtfzlerMcgVReeigMvGysRPfCWbwuAS"  # Replace with your OpenAI API key

        headers = {
            "Authorization": "Bearer pk-DRZbCkIrUhcsuUXdgCtfzlerMcgVReeigMvGysRPfCWbwuAS",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "pai-001-light",
            "prompt": f"request : {user_input}. \n Fulfill the request by providing MySQL code for it. only provide the code required, in ``` CODE  ``` format. do not create a database, do not explain and do not include any header or comments in the code. Only the code is required. the response should never be larger than 800 tokens",
            "max_tokens": 999,
        }

        try:
            response = requests.post(openai_url, json=payload, headers=headers)
            response.raise_for_status()
            generated_sql_query = response.json()["choices"][0]["text"].strip()
            print(generated_sql_query)
            print("################################################################################")

            # Markdown checks
            match5 = re.search(r'``` CODE(.+?)```', generated_sql_query, re.DOTALL)
            if match5:
                generated_sql_query = match5.group(1)
            else:
                match4 = re.search(r'```CODE(.+?)```', generated_sql_query, re.DOTALL)
                if match4:
                    generated_sql_query = match4.group(1)
                else:
                    match1 = re.search(r'```sql(.+?)```', generated_sql_query, re.DOTALL)
                    if match1:
                        generated_sql_query = match1.group(1)
                    else:
                        match2 = re.search(r'```mysql(.+?)```', generated_sql_query, re.DOTALL)
                        if match2:
                            generated_sql_query = match2.group(1)
                        else:
                            match3 = re.search(r'```SQL(.+?)```', generated_sql_query, re.DOTALL)
                            if match3:
                                generated_sql_query = match3.group(1)
                            else:
                                match6 = re.search(r'```SQL(.+?)```', generated_sql_query, re.DOTALL)
                                if match6:
                                    generated_sql_query = match6.group(1)


            self.sql_output_text.text(generated_sql_query)
            print(generated_sql_query)

            # Simulate execution status (you should replace this with actual query execution)
            self.execute_sql_query(db_name, db_user, db_password, generated_sql_query)

        except requests.exceptions.RequestException as e:
            # Display an error message for OpenAI API request failure
            self.sql_output_text.text(f"Error generating SQL query: {e}")

            # Update status button
            self.status_button.text("Error")

        except KeyError:
            # Handle missing key in JSON response (e.g., choices or text)
            self.sql_output_text.text("Error parsing OpenAI response")

            # Update status button
            self.status_button.text("Error")

    def execute_sql_query(self, db_name, db_user, db_password, sql_query):
        # Connect to the MySQL database
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user=db_user,
                password=db_password,
                database=db_name,
                auth_plugin='mysql_native_password'
            )

            cursor = connection.cursor()

            # Split the queries and execute them one by one
            queries = sql_query.split(';')
            for query in queries:
                if query.strip():  # Check if the query is not an empty string
                    cursor.execute(query)

            # Commit the changes
            connection.commit()
            # Close the cursor and connection
            cursor.close()
            connection.close()
            # Update status button for success
            self.status_button.markdown('<div style="width:20px;height:20px;background-color:green;"></div>Success!', unsafe_allow_html=True)

        except mysql.connector.Error as e:
            # Handle MySQL errors
            error_message = f"Error executing SQL query: {e}"
            self.sql_output_text.text(error_message)
            # Update status button for error
            self.status_button.markdown('<div style="width:20px;height:20px;background-color:red;"></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    app = SQLGeneratorApp()