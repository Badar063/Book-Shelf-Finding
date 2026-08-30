import sqlite3
import unicodedata
import re
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from rapidfuzz import fuzz
import streamlit as st

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================

st.set_page_config(
    page_title="Dar Makkah Catalogue",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #f4f6f9;
    }
    .header-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 2.5rem 2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .header-banner h1 {
        color: #ffffff;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .header-banner p {
        color: #e0e6ed;
        font-size: 1.1rem;
        margin-bottom: 0;
    }
    .book-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .book-title {
        color: #1e3c72;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .book-meta {
        color: #4a5568;
        font-size: 0.95rem;
        margin-bottom: 0.75rem;
    }
    .badge-container {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        align-items: center;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .badge-category {
        background-color: #ebf8ff;
        color: #2b6cb0;
        border: 1px solid #bee3f8;
    }
    .badge-shelf {
        background-color: #feebc8;
        color: #c05621;
        border: 1px solid #fbd38d;
        font-family: monospace;
    }
    .badge-match {
        background-color: #f0fff4;
        color: #276749;
        border: 1px solid #c6f6d5;
        margin-left: auto;
    }
    .admin-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# USER AUTHENTICATION STATE
# ==========================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

def login(username, password):
    """Authenticates against .streamlit/secrets.toml"""
    try:
        secret_user = str(st.secrets["credentials"]["admin_user"])
        secret_pass = str(st.secrets["credentials"]["admin_password"])

        if str(username) == secret_user and str(password) == secret_pass:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success(f"Welcome, {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password.")
    except KeyError:
        st.error("Credentials missing in .streamlit/secrets.toml")

def logout():
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.rerun()

# ==========================================
# DATABASE SET UP & MIGRATION
# ==========================================

DB_FILE = "library.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            publisher TEXT,
            isbn TEXT,
            year TEXT,
            category TEXT,
            language TEXT,
            shelf TEXT
        )
    """)
    conn.commit()

    c.execute("PRAGMA table_info(books)")
    existing_columns = [column[1] for column in c.fetchall()]
    
    required_columns = {
        "title": "TEXT",
        "author": "TEXT",
        "publisher": "TEXT",
        "isbn": "TEXT",
        "year": "TEXT",
        "category": "TEXT",
        "language": "TEXT",
        "shelf": "TEXT"
    }

    for col_name, col_type in required_columns.items():
        if col_name not in existing_columns:
            c.execute(f"ALTER TABLE books ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()

init_db()

def add_books_from_df(df):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    df.columns = [str(col).strip().lower() for col in df.columns]

    column_mapping = {
        "title": "title", "book title": "title", "book name": "title", "name": "title",
        "author": "author", "publisher": "publisher", "isbn": "isbn", "year": "year",
        "category": "category", "language": "language", "shelf": "shelf",
        "shelf location": "shelf", "shelf number": "shelf", "shelf no": "shelf", "shelf no.": "shelf"
    }

    df = df.rename(columns=column_mapping)

    expected_cols = ["title", "author", "publisher", "isbn", "year", "category", "language", "shelf"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    for _, row in df.iterrows():
        c.execute("""
            INSERT INTO books (title, author, publisher, isbn, year, category, language, shelf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(row.get("title", "")),
            str(row.get("author", "")),
            str(row.get("publisher", "")),
            str(row.get("isbn", "")),
            str(row.get("year", "")),
            str(row.get("category", "")),
            str(row.get("language", "")),
            str(row.get("shelf", ""))
        ))

    conn.commit()
    conn.close()

def clear_database():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM books")
    conn.commit()
    conn.close()

def delete_single_book(book_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

def get_all_books():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM books", conn)
    conn.close()
    return df

# ==========================================
# TEXT NORMALIZATION & SEARCH LOGIC
# ==========================================

def normalize_text(text):
    if not isinstance(text, str):
        return ""

    text = re.sub(r'\?+', ' ', text)

    tashkeel_regex = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    text = re.sub(tashkeel_regex, '', text)

    text = re.sub(r'[أإآٱ]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ؤ', 'و', text)
    text = re.sub(r'ئ', 'ي', text)

    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)

    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    text = text.lower().strip()

    stop_words = {"and", "or", "the", "of", "in", "by", "a", "an", "و"}
    words = text.split()
    processed_words = [w for w in words if w not in stop_words]

    return " ".join(processed_words)

def search_books(query, threshold=60):
    df = get_all_books()
    if df.empty or not query.strip():
        return pd.DataFrame()

    query_norm = normalize_text(query)
    if not query_norm:
        return pd.DataFrame()

    results = []
    for _, row in df.iterrows():
        title_norm = normalize_text(row.get("title", ""))
        author_norm = normalize_text(row.get("author", ""))
        publisher_norm = normalize_text(row.get("publisher", ""))

        t_score = max(fuzz.partial_ratio(query_norm, title_norm), fuzz.token_set_ratio(query_norm, title_norm))
        a_score = max(fuzz.partial_ratio(query_norm, author_norm), fuzz.token_set_ratio(query_norm, author_norm))
        p_score = max(fuzz.partial_ratio(query_norm, publisher_norm), fuzz.token_set_ratio(query_norm, publisher_norm))

        max_score = max(t_score, a_score, p_score)

        if max_score >= threshold:
            row_dict = row.to_dict()
            row_dict['match_score'] = max_score
            results.append(row_dict)

    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df = result_df.sort_values(by="match_score", ascending=False)

    return result_df

# ==========================================
# SIDEBAR LOGIN & PORTAL
# ==========================================

with st.sidebar:
    st.header("👤 Staff Login")
    
    if st.session_state["logged_in"]:
        st.success(f"Logged in as: **{st.session_state['username']}**")
        if st.button("Log Out"):
            logout()
    else:
        st.info("Staff members can log in here to manage uploads and database settings.")
        with st.form("login_form"):
            input_user = st.text_input("Username")
            input_pass = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Log In")
            
            if submit_login:
                login(input_user, input_pass)

# ==========================================
# STREAMLIT USER INTERFACE
# ==========================================

st.markdown("""
    <div class="header-banner">
        <h1>📚 Dar Makkah International</h1>
        <p>Library Catalogue & Shelf Location Finder</p>
    </div>
""", unsafe_allow_html=True)

# Dynamic tab display: Customer Search is always visible; Admin tab requires login
if st.session_state["logged_in"]:
    tab_search, tab_admin = st.tabs(["🔍 Customer Book Search", "⚙️ Admin & Sheet Management"])
else:
    tab_search, = st.tabs(["🔍 Customer Book Search"])
    tab_admin = None

# ------------------------------------------
# TAB 1: CUSTOMER BOOK SEARCH
# ------------------------------------------
with tab_search:
    st.subheader("Find Books & Shelf Locations")
    
    search_query = st.text_input(
        "Search by book title, author, or publisher:",
        placeholder="e.g., Bukhari, Seerah, Riyadh...",
        key="customer_search_input"
    )

    with st.expander("⚙️ Search Match Options", expanded=False):
        match_threshold = st.slider("Sensitivity Level", min_value=30, max_value=100, value=60)

    st.markdown("---")

    if search_query:
        results = search_books(search_query, threshold=match_threshold)

        if not results.empty:
            st.markdown(f"**Found {len(results)} matching record(s):**")
            
            for _, book in results.iterrows():
                title_val = book.get("title") or "Untitled"
                author_val = book.get("author") or "Unknown Author"
                publisher_val = book.get("publisher") or "Unknown Publisher"
                category_val = book.get("category") or "General"
                shelf_val = book.get("shelf") or "Unassigned"
                score_val = int(book.get("match_score", 0))

                st.markdown(f"""
                    <div class="book-card">
                        <div class="book-title">📖 {title_val}</div>
                        <div class="book-meta">
                            <strong>Author:</strong> {author_val} &nbsp;|&nbsp; 
                            <strong>Publisher:</strong> {publisher_val}
                        </div>
                        <div class="badge-container">
                            <span class="badge badge-category">📂 Category: {category_val}</span>
                            <span class="badge badge-shelf">📍 Shelf Location: {shelf_val}</span>
                            <span class="badge badge-match">Match: {score_val}%</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        else:
            st.warning("No books found matching your query. Try adjusting the search terms.")
    else:
        st.info("Use the search bar above to look up titles, authors, and shelf locations.")

# ------------------------------------------
# TAB 2: ADMIN MANAGEMENT (LOGGED-IN ONLY)
# ------------------------------------------
if st.session_state["logged_in"] and tab_admin is not None:
    with tab_admin:
        st.subheader("Admin Control Panel")

        df_current = get_all_books()
        st.metric(label="Total Books in Database", value=len(df_current))
        st.markdown("---")

        col_upload, col_danger = st.columns([2, 1])

        with col_upload:
            st.markdown('<div class="admin-card">', unsafe_allow_html=True)
            st.write("### 📥 Upload Excel Spreadsheet")
            uploaded_file = st.file_uploader("Upload Excel File (.xlsx, .xls)", type=["xlsx", "xls"])

            if uploaded_file is not None:
                if st.button("Import Spreadsheet to Database", type="primary"):
                    try:
                        df_upload = pd.read_excel(uploaded_file)
                        add_books_from_df(df_upload)
                        st.success(f"Successfully imported records from {uploaded_file.name}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to import file: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_danger:
            st.markdown('<div class="admin-card">', unsafe_allow_html=True)
            st.write("### 🚨 Reset Database")
            st.caption("Remove all book records from the database.")
            if st.button("Delete All Records", type="secondary"):
                clear_database()
                st.success("Database cleared successfully.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if not df_current.empty:
            st.markdown("---")
            st.write("### Current Database Records")
            
            for idx, row in df_current.iterrows():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                c1.write(f"**{row['title']}**")
                c2.write(f"Author: {row['author']}")
                c3.write(f"Shelf: `{row['shelf']}`")
                if c4.button("🗑️ Delete", key=f"delete_btn_{row['id']}"):
                    delete_single_book(row['id'])
                    st.rerun()
