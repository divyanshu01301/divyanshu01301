import streamlit as st
import pandas as pd
import re



# Set Streamlit Page Configuration
st.set_page_config(page_title="Invoice Chatbot", layout="wide")
st.title("💬 Turnpikes Chatbot")

# Initialize session state for chat history & uploaded data
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "first_upload" not in st.session_state:
    st.session_state.first_upload = True

# Welcome message on first load
if not st.session_state.messages:
    welcome_message = {
        "role": "assistant",
        "content": "👋 Hello! I'm your Invoice Assistant. Upload an invoice file, and I'll help answer your questions about vendors, payments, and statuses."
    }
    st.session_state.messages.append(welcome_message)

# Predefined Questions
predefined_questions = [
    "How many distinct vendors are there?",
    "How many of them are Non-PO invoices?",
    "How many of them have status 'Posted'?",
    "How many PO invoices are there?",
    "How many total distinct count are there?"
]

# Custom CSS
st.markdown("""
<style>
    .chat-container {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        padding: 20px;
        margin-bottom: 20px;
        height: 400px;
        overflow-y: auto;
    }
    .stButton button {
        width: 100%;
        text-align: left;
        white-space: normal;
        height: auto;
        padding: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Chat Input
user_input = st.chat_input("Type your invoice-related question...")

# Predefined Questions as buttons
st.write("### Quick Questions")
col1, col2, col3, col4, col5 = st.columns(5)
if col1.button(predefined_questions[0], key="btn_vendors"):
    user_input = predefined_questions[0]
if col2.button(predefined_questions[1], key="btn_non_po"):
    user_input = predefined_questions[1]
if col3.button(predefined_questions[2], key="btn_posted"):
    user_input = predefined_questions[2]
if col4.button(predefined_questions[3], key="btn_po"):
    user_input = predefined_questions[3]
if col5.button(predefined_questions[4], key="btn_total_distinct"):
    user_input = predefined_questions[4]

# Function to process natural language queries
def process_query(query, df):
    query_lower = query.lower()
    response = ""
    display_df = None

    if df is None or df.empty:
        return "I need data to analyze this question. Please upload an invoice file.", None

    def get_column_if_exists(possible_names, default=None):
        for name in possible_names:
            if name in df.columns:
                return name
        return default

    vendor_col = get_column_if_exists(["VEND_NAME", "vendor", "vendor_name", "supplier"])
    vendor_num_col = get_column_if_exists(["LIFNR", "vendor_number", "supplier_number"])
    doctype_col = get_column_if_exists(["DOCTYPE", "doctype", "document_type"])
    status_col = get_column_if_exists(["STATUS", "status", "invoice_status"])
    docid_col = get_column_if_exists(["DOCID", "docid", "document_id"])

    if "how many distinct vendors" in query_lower or "how many suppliers are there" in query_lower or "how many sellers are there" in query_lower:
        if vendor_col and vendor_num_col:
            distinct_count = df[vendor_col].nunique()
            vendor_data = df[[vendor_col, vendor_num_col]].drop_duplicates()
            display_df = vendor_data
            
            term = "vendors"
            if "supplier" in query_lower:
                term = "suppliers"
            elif "seller" in query_lower:
                term = "sellers"
            
            response = f"📌 There are **{distinct_count}** {term}.\n\n🔹 **Here is the list of {term}:**"
        else:
            response = "⚠️ I couldn't find the vendor column in your data."
    
    elif "can you tell me the vendor name" in query_lower:
        if vendor_col and vendor_num_col:
            vendor_data = df[[vendor_col, vendor_num_col]].drop_duplicates()
            display_df = vendor_data
            response = "📌 Here is the list of vendors along with their vendor numbers."
        else:
            response = "⚠️ I couldn't find the required columns for vendor names and numbers."
    
    elif "how many of them are non-po" in query_lower:
        if doctype_col:
            non_po_df = df[df[doctype_col].astype(str).str.contains("NPO|non.?po", regex=True, case=False, na=False)]
            response = f"📌 There are **{len(non_po_df)}** Non-PO invoices."
            display_df = non_po_df
        else:
            response = "⚠️ I couldn't find a document type column to identify Non-PO invoices."

    elif "how many of them have status 'posted'" in query_lower:
        if status_col:
            posted_df = df[df[status_col] == 15]
            response = f"📌 There are **{len(posted_df)}** invoices with status 'Posted'."
            display_df = posted_df
        else:
            response = "⚠️ I couldn't find a status column in your data."
    
    elif "how many po invoices are there" in query_lower:
        if doctype_col:
            po_df = df[df[doctype_col] == "ZPO_IN_AUP"]
            response = f"📌 There are **{len(po_df)}** PO invoices."
            display_df = po_df
        else:
            response = "⚠️ I couldn't find a document type column to identify PO invoices."
    
    elif "how many total distinct count are there" in query_lower:
        if docid_col:
            distinct_docid_count = df[docid_col].nunique()
            response = f"📌 There are **{distinct_docid_count}** total distinct documents."
        else:
            response = "⚠️ I couldn't find the DOCID column in your data."
    
    else:
        response = "Hey, How can I help you?"
    
    return response, display_df


# Handle user input
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    response, display_df = process_query(user_input, st.session_state.df)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
    
    if display_df is not None:
        with st.chat_message("assistant"):
            st.dataframe(display_df, use_container_width=True)

st.header("📂 Upload an Invoice File for Analysis")
uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "csv"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl') if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
        st.session_state.df = df
        if st.session_state.first_upload:
            st.session_state.messages.append({"role": "assistant", "content": f"✅ Successfully loaded '{uploaded_file.name}' with {len(df)} rows and {len(df.columns)} columns."})
            st.session_state.first_upload = False
            st.rerun()
        with st.expander("📋 Preview Uploaded Data", expanded=False):
            st.dataframe(df.head(10), use_container_width=True)
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")

st.markdown("---")
st.markdown("💡 **Tip**: Use the quick question buttons above or type your question in the chat box.")
