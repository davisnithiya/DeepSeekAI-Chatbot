# DeepSeekAI-Chatbot
## Overview
This project is a chatbot application built using Spring Boot that interacts with a Python-based AI model (DeepSeek AI) to generate and execute SQL queries. The chatbot takes user queries in natural language and converts them into SQL commands, fetching results from a MySQL database.

### Features
Chatbot UI: Simple web interface for user interaction.
Natural Language to SQL Conversion: Uses DeepSeek Coder 1.3B Instruct to generate SQL queries.
Spring Boot Backend: Manages user requests and database execution.
Python API Integration: Sends user queries to a Python service for SQL generation.
MySQL Database: Stores student data and processes SQL queries.

### AI Model (Python API)
DeepSeek AI for SQL query generation
Model: deepseek-ai/deepseek-coder-1.3b-instruct
Repository: DeepSeek AI on Hugging Face
Flask (for hosting Python API)

### Python API Setup (DeepSeek AI Integration)
1. Install Python Dependencies
Ensure you have Python 3.8+ installed. Then, install required libraries:
pip install flask transformers torch
2. Start Python API
Run the Python Flask API that communicates with DeepSeek AI:
python flask_api.py
This should start a local API at http://localhost:5001/generate_sql.
