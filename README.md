Bank Statement Analyst AI

An intelligent financial assistant that allows you to chat with your bank statements. Upload PDF, DOCX, or Excel files and ask questions about your spending, trends, and transactions using the power of RAG (Retrieval-Augmented Generation) and Google Gemini.

Use Case Objective

Simplify Analysis: Turn dense financial PDFs into interactive conversations.

Visual Insights: Automatically generate charts for spending habits without using Excel.

Contextual Understanding: Combine private banking data with public web knowledge (e.g., currency rates, merchant details).

Technical Architecture

Frontend: Streamlit

AI Model: Google Gemini 2.0 Flash

Orchestration: LangChain

Vector Store: FAISS (Local, In-Memory)

Embeddings: Google Generative AI (models/text-embedding-004)

⚠️ Known Limitations

Aggregation & Math Accuracy: This tool uses RAG, which retrieves the most relevant parts of a document, not the entire document.
Good Query: "How much did I spend on Starbucks last month?" (Retrieves specific hits).

Bad Query: "Calculate the exact sum of every transaction in this 50-page PDF." (Might miss transactions not in the top retrieved chunks).

Scanned Documents: The system currently supports digital PDFs only (files where you can highlight text). Scanned image-based PDFs (photocopies) will return an error as no OCR engine is currently integrated.
⚙️ Installation & Setup

Navigate to the folder:

cd usecase

Install Dependencies:

pip install -r requirements.txt

Configure API Key: Create a .env file in this folder:

GOOGLE_API_KEY=your_actual_api_key_here

Run the Application:

streamlit run app.py

📂 Features Implemented

Secure Decryption: msoffcrypto handles password-protected bank statements.

Smart Graphing: Detects when a user asks for a plot and generates a Streamlit-native Bar or Line chart.

Web Search Fallback: Uses DuckDuckGo to define unknown financial terms found in your statement.
