import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify
import mysql.connector
import logging
import re

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load DeepSeek model and tokenizer
model_name = "deepseek-ai/deepseek-coder-1.3b-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name, 
    trust_remote_code=True, 
    torch_dtype=torch.float32  
).to("cpu")  # Use CPU for inference

# Database connection (Use a context manager to ensure it's closed after use)
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="ab*&^",
        database="school"
    )

# Define schema details
SCHEMA_INFO = """
You are an AI assistant generating MySQL queries. The database schema is:

Table: students
- id (INT, Primary Key)
- name (VARCHAR(255))
- email (VARCHAR(255))
- course (VARCHAR(255))

Generate SQL queries **strictly based on this schema**.
"""

def extract_sql_query(generated_text):
    """Extracts the first valid SQL query from the generated text."""
    # Strip unwanted content before and after the SQL query
    sql_query_start = generated_text.find("SELECT")
    
    if sql_query_start == -1:
        return None
    
    sql_query_end = generated_text.find(";", sql_query_start) + 1
    
    if sql_query_end == -1:
        return None
    
    # Extract the query and strip unnecessary text
    sql_query = generated_text[sql_query_start:sql_query_end].strip()

    # Remove any explanation or additional non-SQL text
    sql_query = re.sub(r"However.*", "", sql_query).strip()

    return sql_query


def generate_sql(user_query):
    prompt = f"""
    You are an AI assistant generating MySQL queries based on the following schema:

    Table: students
    - id (INT, Primary Key)
    - name (VARCHAR(255))
    - email (VARCHAR(255))
    - course (VARCHAR(255))

    User Query: {user_query}

    Generate a valid SQL query based only on this schema.
    """
    
    inputs = tokenizer(prompt, return_tensors="pt").to("cpu")
    
    outputs = model.generate(
        **inputs, 
        max_new_tokens=100, 
        do_sample=True, 
        top_k=50, 
        top_p=0.95, 
        num_return_sequences=1, 
        eos_token_id=tokenizer.eos_token_id
    )
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Generated Text: {generated_text}")  # Debugging line

    # Extract the SQL query from the generated text
    sql_query_start = generated_text.find("SELECT")
    sql_query_end = generated_text.find(";", sql_query_start) + 1
    sql_query = generated_text[sql_query_start:sql_query_end].strip()

    # Check and log the extracted SQL query
    print(f"Extracted SQL Query: {sql_query}")  # Debugging line
    
    # Remove GROUP BY and HAVING clauses if they exist
    if "GROUP BY" in sql_query:
        sql_query = sql_query.split("GROUP BY")[0].strip()
    
    if "HAVING" in sql_query:
        sql_query = sql_query.split("HAVING")[0].strip()

    # Handle "details" or "full details" to select all columns
    if "details" in user_query or "full details" in user_query:
        if "SELECT *" not in sql_query:
            sql_query = sql_query.replace("SELECT name", "SELECT *")

    # Handle email-based queries (e.g., "details of student Tintu@example.com")
    email_match = re.search(r"student (\S+?@\S+?\.\S+)", user_query)
    if email_match:
        email = email_match.group(1).strip()
        # Ensure email condition is only added once
        if "WHERE" in sql_query:
            if "email" not in sql_query:
                sql_query = sql_query.replace("WHERE", f"WHERE email = '{email}' AND")
        else:
            sql_query = sql_query.replace("SELECT *", f"SELECT * FROM students WHERE email = '{email}'")

    # Handle course-based queries (e.g., "Show students taking courses with 'Science' in the name.")
    course_match = re.search(r"courses? with '(.*?)' in the name", user_query)
    if course_match:
        course_name = course_match.group(1).strip()
        # Ensure course condition is only added once and handle the WHERE clause properly
        if "WHERE" in sql_query:
            if "course LIKE" not in sql_query:
                sql_query = sql_query.replace("WHERE", f"WHERE course LIKE '%{course_name}%' AND")
        else:
            sql_query = sql_query.replace("SELECT *", f"SELECT * FROM students WHERE course LIKE '%{course_name}%'")

    # Handle name-based queries (e.g., "with the name 'John'")
    name_match = re.search(r"with the name '(.*?)'", user_query)
    if name_match:
        name = name_match.group(1).strip()
        # Use LOWER() for case-insensitive matching
        if "name LIKE" in sql_query:
            sql_query = sql_query.replace(f"name LIKE '%{name}%'", f"LOWER(name) LIKE LOWER('%{name}%')")
        elif "name =" in sql_query:
            sql_query = sql_query.replace(f"name = '{name}'", f"LOWER(name) = LOWER('{name}')")
        else:
            # If name condition isn't already in the query, add it
            if "WHERE" in sql_query:
                sql_query = sql_query.replace("WHERE", f"WHERE LOWER(name) LIKE LOWER('%{name}%') AND")
            else:
                sql_query = sql_query.replace("SELECT *", f"SELECT * FROM students WHERE LOWER(name) LIKE LOWER('%{name}%')")

    # Ensure no extra "AND" at the end of the WHERE clause
    if sql_query.endswith("AND"):
        sql_query = sql_query[:-3]

    return sql_query


def execute_sql_query(sql_query):
    """Executes the generated SQL query and fetches results."""
    logging.info(f"Executing SQL query: {sql_query}")
    try:
        # Get a fresh database connection for each query
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchall()
        logging.info(f"Query result: {result}")
        
        # Close the connection
        conn.close()
        
        # Adjust the result processing based on the columns selected
        if "SELECT name" in sql_query:
            # Only the name is selected
            return [{'name': row[0]} for row in result]
        elif "SELECT *" in sql_query:
            # Handle general case with all columns
            return [{'id': row[0], 'name': row[1], 'email': row[2], 'course': row[3]} for row in result]
        else:
            # Handle other cases if necessary
            return [{'result': row} for row in result]
    
    except mysql.connector.errors.ProgrammingError as e:
        logging.error(f"SQL error: {e}")
        return None


@app.route('/generate_sql', methods=['POST'])
def generate_sql_endpoint():
    user_query = request.json.get('query')

    if not user_query:
        return jsonify({'error': 'Query cannot be empty'}), 400  # Return error if query is empty

    sql_query = generate_sql(user_query)

    if not sql_query:
        return jsonify({'error': 'Invalid SQL generated'}), 400

    result = execute_sql_query(sql_query)
    
    if result is None:
        response = "There was an error with the SQL query."
    else:
        response = result
    
    return jsonify({'sql_query': sql_query, 'result': response})


if __name__ == '__main__':
    app.run(debug=True, port=5001)
