import streamlit as st
import logging
import json
import re
import pandas as pd

# Assuming these modules exist in your project structure based on your previous snippet
from models.llm import get_llm
from utils.pdf_processor import process_document 
from utils.search_tool import perform_web_search 
from config.config import GOOGLE_API_KEY

st.set_page_config(page_title='NeoStats - Bank Statement Analyst', layout='wide')
st.title('NeoStats: Bank Statement Analyst AI')
st.caption('Upload your financial statement (PDF/DOCX/XLSX) and ask questions about your spending.')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not GOOGLE_API_KEY:
    st.error("API Key not found! Please configure it in Streamlit Secrets or your .env file.")
    st.stop()


@st.cache_resource(show_spinner=False)
def load_and_process_document(uploaded_file, password):
    """Processes the uploaded file into a FAISS retriever."""
    uploaded_file.seek(0) 
    return process_document(uploaded_file, password)


st.sidebar.header('Statement & Controls')

uploaded_file = st.sidebar.file_uploader(
    'Upload Bank/Financial Statement', 
    type=['pdf', 'docx', 'xlsx']
)

pdf_password = None
if uploaded_file and uploaded_file.name.lower().endswith('.pdf'):
    pdf_password = st.sidebar.text_input(
        "Enter PDF Password (if protected)", 
        type="password",
        key="pdf_password_input",
        help="Required to decrypt password-protected PDF statements."
    )

mode = st.sidebar.radio(
    'Response Mode', 
    ['Concise', 'Detailed'], 
    help='Concise: Short summary (2 sentences). Detailed: In-depth analysis/Tables/Graphs.'
)

force_web_search = st.sidebar.checkbox(
    'Force Web Search', 
    value=False, 
    help='Adds web search context to every query.'
)

# --- Document Processing Logic ---
retriever = None

if uploaded_file:
    password_to_pass = st.session_state.get("pdf_password_input") if uploaded_file.name.lower().endswith('.pdf') else None
    
    with st.spinner("⏳ Analyzing financial data..."):
        try:
            retriever = load_and_process_document(uploaded_file, password_to_pass)
            
            st.sidebar.success(f" Statement **{uploaded_file.name}** processed successfully!")
            st.markdown(f"> **Status:** Document **{uploaded_file.name}** ready for analysis.")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Processing error: {error_msg}")
            if "password" in error_msg.lower():
                st.sidebar.error(" Error: Password failure. Please enter the correct password.")
            else:
                st.sidebar.error(f" Error: {error_msg}")
            retriever = None

st.markdown('---')

# --- Chat Interface ---
user_query = st.chat_input("Ask about your finances (e.g., 'Total spent on food?' or 'Plot a chart of spending').")

if user_query and retriever:
    try:
        # 1. Retrieve Context
        with st.spinner('🔍 Reading statement...'):
            relevant_docs = retriever.invoke(user_query)
            rag_context = "\n---\n".join([doc.page_content for doc in relevant_docs])

        # 2. Determine Web Search Necessity
        web_context = ""
        generic_keywords = ["what", "who", "how", "define", "explain", "rate", "price", "news", "compare", "analysis", "trend"]
        is_generic_query = any(w in user_query.lower() for w in generic_keywords)
        
        perform_search = force_web_search or (mode == "Detailed") or is_generic_query
        
        if perform_search:
            with st.spinner('🌐 Checking the web...'):
                web_results_text = perform_web_search(user_query)
                web_context = f"\n\n--- LIVE WEB SEARCH CONTEXT ---\n{web_results_text}\n---\n"
                if mode == "Detailed":
                    st.info("🌐 Web search included for detailed context.")

        # 3. Define System Prompts
        if mode == "Concise":
            system_instruction = """
            ROLE: You are a precise Data Assistant.
            
            LOGIC FLOW:
            1. Check DOCUMENT_CONTEXT for the answer.
            2. If data is NOT available in DOCUMENT_CONTEXT and the question is generic, use web search.
            
            STRICT CONSTRAINTS:
            1. Answer in 2 sentences MAXIMUM.
            2. Do calculations if needed within the answer.
            3. NO intro fillers.
            4. NO bullet points.
            """
        else: # Detailed Mode
            system_instruction = """
            ROLE: You are a Senior Financial Analyst.
            
            LOGIC FLOW:
            1. IF user asks for "Total Transaction Table" or similar list:
               - You MUST generate a structured Markdown Table containing Date, Description, and Amount.
               
            2. IF user asks to DRAW/PLOT/GRAPH/VISUALIZE:
               - You MUST provide the analysis in text FIRST.
               - THEN, generate a JSON block at the very end of your response.
               - JSON Format:
                 ```json
                 {
                    "chart_type": "bar", 
                    "data": {"Category": ["A", "B"], "Amount": [10, 20]},
                    "title": "Chart Title"
                 }
                 ```
               - Supported chart_types: "bar", "line".
               - Ensure "data" keys are suitable for a pandas DataFrame (e.g., "Category"/"Date" and "Amount").

            3. IF user asks for Analysis or Generic Question:
               - Provide a comprehensive deep-dive.
               - Integrate insights from WEB_CONTEXT with DOCUMENT_CONTEXT.
            
            STRICT CONSTRAINTS:
            1. Use "Large Points" (Bullet points with detailed explanations).
            2. If performing analysis, explain your reasoning clearly.
            3. For tables, ensure columns are aligned.
            """
        
        # 4. Construct Prompt
        prompt_template = f"""
        {system_instruction}

        _____________
        CONTEXT DATA (From Uploaded Statement):
        {rag_context}

        _____________
        EXTERNAL KNOWLEDGE (Web Search):
        {web_context}
        
        _____________
        USER QUERY:
        {user_query}
        
        _____________
        YOUR ANSWER:
        """
        
        # 5. Display User Message
        with st.chat_message("user"):
            st.write(user_query)

        # 6. Generate and Display Assistant Response
        # 6. Generate and Display Assistant Response
        with st.spinner("🤖 Thinking..."):
            llm = get_llm()
            response = llm.invoke(prompt_template).content
            
            with st.chat_message("assistant"):
                # Regex to find the JSON block
                json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
                
                if json_match:
                    # 1. Extract the JSON content
                    json_str = json_match.group(1)
                    
                    # 2. Remove the JSON block from the text shown to the user
                    clean_text = response.replace(json_match.group(0), "")
                    st.write(clean_text)  # Display only the conversation text
                    
                    # 3. Render the Graph (Hidden from text, shown as visual)
                    try:
                        chart_data = json.loads(json_str)
                        
                        if "data" in chart_data:
                            # Create a container for the graph to make it pop
                            with st.container():
                                st.markdown("### 📊 Visualization")
                                df = pd.DataFrame(chart_data["data"])
                                
                                # Set Index for X-Axis Labels
                                if "Category" in df.columns:
                                    df = df.set_index("Category")
                                elif "Date" in df.columns:
                                    df = df.set_index("Date")
                                    
                                chart_type = chart_data.get("chart_type", "bar")
                                title = chart_data.get("title", "Data Visualization")
                                
                                st.caption(title)
                                
                                if chart_type == "line":
                                    st.line_chart(df)
                                else:
                                    st.bar_chart(df)
                                    
                    except Exception as graph_err:
                        st.warning(f"Could not render chart: {graph_err}")
                        logger.error(f"Graph rendering error: {graph_err}")
                
                else:
                    # No graph found, just print the response as is
                    st.write(response)

            # 7. Show Sources (Expandable)
            with st.expander("See Source Context"):
                if rag_context:
                    st.markdown("**Document Excerpts:**")
                    for d in relevant_docs:
                        page_num = d.metadata.get('page', 'N/A')
                        st.caption(f"Page {page_num}: {d.page_content[:200]}...")
                if web_context:
                    st.markdown("**Web Search:**")
                    st.caption(web_context)

    except Exception as e:
        st.error(f"An error occurred during generation: {e}")
        logger.error(f"Generation error: {e}")

elif user_query and not retriever:
    st.warning("⚠️ Please upload a financial statement to begin.")

# --- Dev Tools ---
if st.sidebar.button("Clear Cache & Rerun"):
    st.cache_resource.clear()
    st.rerun()