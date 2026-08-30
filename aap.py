import sqlite3
import unicodedata
import re
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

# Custom CSS for enhanced UI/UX
st.markdown("""
    <style>
    /* Main Background & Font Styling */
    .stApp {
        background-color: #f4f6f9;
    }
    
    /* Header Container */
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

    /* Result Cards */
    .book-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .book-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
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
    
    /* Tags & Badges */
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

    /* Admin Container Styling */
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
# DATABASE SET UP
# ==========================================

DB_FILE = "library.db"

def init_db():
    """Initialize the SQLite database schema if it doesn't exist."""
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
    conn.close()

init_db()

def add_books_from_df(df):
    """Import records from a Pandas DataFrame into the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    column_mapping = {
        "title": "title",
        "book title": "title",
        "author": "author",
        "publisher": "publisher",
        "isbn": "isbn",
        "year": "year",
        "category": "category",
        "language": "language",
        "shelf": "shelf",
        "shelf location": "shelf"
    }

    df.columns = [str(col).strip().lower() for col in df.columns]
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
    """Clear all records from the database table."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM books")
    conn.commit()
    conn.close()

def get_all_books():
    """Retrieve all books from the database."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM books", conn)
    conn.close()
    return df

# ==========================================
# SEARCH & HELPER FUNCTIONS
# ==========================================

def normalize_text(text):
    """Normalize text for searching: remove diacritics, extra spaces, and lower case."""
    if not isinstance(text, str):
        return ""

    arabic_diacritics = re.compile(r'[\u064B-\u0652]')
    text = re.sub(arabic_diacritics, '', text)

    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

    return text.lower().strip()

def search_books(query, threshold=60):
    """Search catalogue using exact and fuzzy matching techniques."""
    df = get_all_books()
    if df.empty or not query.strip():
        return pd.DataFrame()

    query_norm = normalize_text(query)

    results = []
    for _, row in df.iterrows():
        title_norm = normalize_text(row.get("title", ""))
        author_norm = normalize_text(row.get("author", ""))
        publisher_norm = normalize_text(row.get("publisher", ""))

        title_score = fuzz.partial_ratio(query_norm, title_norm)
        author_score = fuzz.partial_ratio(query_norm, author_norm)
        publisher_score = fuzz.partial_ratio(query_norm, publisher_norm)

        max_score = max(title_score, author_score, publisher_score)

        if max_score >= threshold:
            row_dict = row.to_dict()
            row_dict['match_score'] = max_score
            results.append(row_dict)

    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df = result_df.sort_values(by="match_score", ascending=False)

    return result_df

# ==========================================
# STREAMLIT USER INTERFACE
# ==========================================

# Top Banner Header
st.markdown("""
    <div class="header-banner">
        <h1>📚 Dar Makkah International</h1>
        <p>Library Catalogue & Search System</p>
    </div>
""", unsafe_allow_html=True)

# Main Navigation Tabs
tab_search, tab_admin = st.tabs(["🔍 Search Catalogue", "⚙️ Admin & Catalogue Management"])

# ------------------------------------------
# TAB 1: SEARCH CATALOGUE
# ------------------------------------------
with tab_search:
    st.subheader("Search Library Collection")
    
    # Primary Search Input Controls
    search_query = st.text_input(
        "Enter title, author, or publisher name:",
        placeholder="e.g., Sahih Al-Bukhari, Ibn Kathir...",
        key="search_input"
    )

    with st.expander("⚙️ Search Options & Sensitivity", expanded=False):
        match_threshold = st.slider(
            "Match Sensitivity Level",
            min_value=30,
            max_value=100,
            value=60,
            help="Lower values yield broader results; higher values require closer matches."
        )

    st.markdown("---")

    if search_query:
        results = search_books(search_query, threshold=match_threshold)

        if not results.empty:
            st.markdown(f"**Found {len(results)} matching record(s):**")
            
            for _, book in results.iterrows():
                # Safe attribute extraction to avoid KeyErrors
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
                            <span class="badge badge-shelf">📍 Shelf: {shelf_val}</span>
                            <span class="badge badge-match">Match Score: {score_val}%</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No matching books found. Try broadening your query or adjusting the sensitivity slider.")
    else:
        st.info("Enter a query above to start searching the catalogue.")

# ------------------------------------------
# TAB 2: ADMIN & IMPORT
# ------------------------------------------
with tab_admin:
    st.subheader("Catalogue Management Panel")

    df_current = get_all_books()
    
    # Overview metrics
    st.metric(label="Total Registered Books", value=len(df_current))
    st.markdown("---")

    col_upload, col_danger = st.columns([2, 1])

    with col_upload:
        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.write("### 📥 Import Spreadsheet")
        uploaded_file = st.file_uploader(
            "Upload Excel File (.xlsx, .xls)", 
            type=["xlsx", "xls"],
            help="Ensure headers contain Title, Author, Publisher, Category, Shelf Location, etc."
        )

        if uploaded_file is not None:
            if st.button("Process & Import Data", type="primary"):
                try:
                    df_upload = pd.read_excel(uploaded_file)
                    add_books_from_df(df_upload)
                    st.success(f"Successfully imported records from {uploaded_file.name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to process file: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_danger:
        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.write("### 🚨 Database Actions")
        st.caption("Permanently clear the library catalogue database.")
        if st.button("Clear All Database Records", type="secondary"):
            clear_database()
            st.success("Database table reset successfully.")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if not df_current.empty:
        st.markdown("---")
        st.write("### Complete Database Overview")
        st.dataframe(df_current, use_container_width=True)
