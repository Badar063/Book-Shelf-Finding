import sqlite3
import unicodedata
import pandas as pd
from rapidfuzz import fuzz
import re
import streamlit as st

# ==========================================
# DATABASE SET UP
# ==========================================

DB_FILE = "library.db"


def init_db():
    """Initialize the SQLite database schema if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """
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
    """
    )
    conn.commit()
    conn.close()


init_db()


def add_books_from_df(df):
    """Import records from a Pandas DataFrame into the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Column mapping to standardize uploaded files
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
        "shelf location": "shelf",
    }

    # Normalize DataFrame column names
    df.columns = [str(col).strip().lower() for col in df.columns]
    df = df.rename(columns=column_mapping)

    # Ensure all expected columns exist
    expected_cols = [
        "title",
        "author",
        "publisher",
        "isbn",
        "year",
        "category",
        "language",
        "shelf",
    ]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    # Insert rows into database
    for _, row in df.iterrows():
        c.execute(
            """
            INSERT INTO books (title, author, publisher, isbn, year, category, language, shelf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                str(row.get("title", "")),
                str(row.get("author", "")),
                str(row.get("publisher", "")),
                str(row.get("isbn", "")),
                str(row.get("year", "")),
                str(row.get("category", "")),
                str(row.get("language", "")),
                str(row.get("shelf", "")),
            ),
        )

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

    # Remove Arabic diacritics
    arabic_diacritics = re.compile(r"[\u064B-\u0652]")
    text = re.sub(arabic_diacritics, "", text)

    # Remove general unicode diacritics
    text = "".join(
        c
        for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
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
        title_norm = normalize_text(row["title"])
        author_norm = normalize_text(row["author"])
        publisher_norm = normalize_text(row["publisher"])

        # Calculate fuzzy similarity scores
        title_score = fuzz.partial_ratio(query_norm, title_norm)
        author_score = fuzz.partial_ratio(query_norm, author_norm)
        publisher_score = fuzz.partial_ratio(query_norm, publisher_norm)

        max_score = max(title_score, author_score, publisher_score)

        if max_score >= threshold:
            row_dict = row.to_dict()
            row_dict["match_score"] = max_score
            results.append(row_dict)

    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df = result_df.sort_values(by="match_score", ascending=False)

    return result_df


# ==========================================
# STREAMLIT USER INTERFACE
# ==========================================

st.set_page_config(
    page_title="Dar Makkah Catalogue", page_icon="📚", layout="wide"
)

# Inject Custom CSS
st.markdown(
    """
    <style>
    .hero-container {
        padding: 2rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1.2rem;
        border-left: 4px solid #1e3c72;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .book-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Navigation / Tabs
st.markdown(
    """
    <div class="hero-container">
        <h1>📚 Dar Makkah International</h1>
        <p>Library Catalogue & Search System</p>
    </div>
""",
    unsafe_allow_html=True,
)

tab_search, tab_admin = st.tabs(["🔍 Search Catalogue", "⚙️ Admin & Import"])

# ------------------------------------------
# TAB 1: SEARCH CATALOGUE
# ------------------------------------------
with tab_search:
    st.subheader("Search Books")

    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search_query = st.text_input(
            "Search by Title, Author, or Publisher:",
            placeholder="Type your search term...",
        )
    with col_filter:
        match_threshold = st.slider(
            "Match Sensitivity",
            min_value=30,
            max_value=100,
            value=60,
            help="Lower values find more broad matches; higher values require closer matches.",
        )

    if search_query:
        results = search_books(search_query, threshold=match_threshold)

        if not results.empty:
            st.success(f"Found {len(results)} matching record(s).")
            for _, book in results.iterrows():
                with st.container():
                    st.markdown(
                        f"""
                        <div class="book-card">
                            <h4>📖 {book['title']}</h4>
                            <p><strong>Author:</strong> {book['author'] or 'N/A'} | <strong>Publisher:</strong> {book['publisher'] or 'N/A'}</p>
                            <p><strong>Category:</strong> {book['category'] or 'N/A'} | <strong>Shelf Location:</strong> <code>{book['shelf'] or 'N/A'}</code></p>
                        </div>
                    """,
                        unsafe_allow_html=True,
                    )
        else:
            st.warning("No matching books found. Try adjusting your search term or sensitivity.")
    else:
        st.info("Enter a query above to search through the library catalogue.")

# ------------------------------------------
# TAB 2: ADMIN & IMPORT
# ------------------------------------------
with tab_admin:
    st.subheader("Catalogue Management")

    df_current = get_all_books()
    st.metric("Total Books in Database", len(df_current))

    st.markdown("---")
    st.write("### Upload Data File")
    uploaded_file = st.file_uploader(
        "Upload an Excel spreadsheet (.xlsx, .xls)", type=["xlsx", "xls"]
    )

    col1, col2 = st.columns(2)

    with col1:
        if uploaded_file is not None:
            if st.button("📥 Import Excel Records"):
                try:
                    df_upload = pd.read_excel(uploaded_file)
                    add_books_from_df(df_upload)
                    st.success(f"Successfully imported records from {uploaded_file.name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing file: {e}")

    with col2:
        if st.button("🚨 Clear Entire Database", type="secondary"):
            clear_database()
            st.success("Database cleared successfully.")
            st.rerun()

    if not df_current.empty:
        st.markdown("---")
        st.write("### Database View")
        st.dataframe(df_current, use_container_width=True)
