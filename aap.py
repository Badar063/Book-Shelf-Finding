import sqlite3
import unicodedata
import re
import requests
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
# DATABASE SET UP & MIGRATION
# ==========================================

DB_FILE = "library.db"

def init_db():
    """Initialize SQLite table and automatically patch missing columns."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Create main table if it doesn't exist
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

    # 2. Check for missing columns in existing database and add them
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
    """Imports dataframe records safely even with varying column names/count."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Standardize column headers
    df.columns = [str(col).strip().lower() for col in df.columns]

    column_mapping = {
        "title": "title",
        "book title": "title",
        "book name": "title",
        "name": "title",
        "author": "author",
        "publisher": "publisher",
        "isbn": "isbn",
        "year": "year",
        "category": "category",
        "language": "language",
        "shelf": "shelf",
        "shelf location": "shelf",
        "shelf number": "shelf",
        "shelf no": "shelf",
        "shelf no.": "shelf"
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
    """Removes all data from the database table."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM books")
    conn.commit()
    conn.close()

def get_all_books():
    """Retrieves all library records."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM books", conn)
    conn.close()
    return df

# ==========================================
# REST API INTEGRATION VIA SECRETS.TOML
# ==========================================

@st.cache_data(ttl=300)
def fetch_api_book_details(title, isbn=""):
    """
    Fetches price and image URLs from REST API defined in .streamlit/secrets.toml.
    Supports multiple image URLs for matches.
    """
    if "api" not in st.secrets:
        return {"price": "N/A", "images": []}

    api_url = st.secrets["api"].get("url", "")
    api_key = st.secrets["api"].get("key") or st.secrets["api"].get("token", "")

    if not api_url:
        return {"price": "N/A", "images": []}

    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    params = {"title": title, "isbn": isbn}

    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Parse responses returning price and list or single string of images
            price = data.get("price", "N/A")
            raw_images = data.get("images", data.get("image", []))
            
            if isinstance(raw_images, str):
                images = [raw_images] if raw_images else []
            elif isinstance(raw_images, list):
                images = [img for img in raw_images if isinstance(img, str) and img]
            else:
                images = []

            return {"price": price, "images": images}
    except Exception:
        pass

    return {"price": "N/A", "images": []}

# ==========================================
# ADVANCED NORMALIZATION & SEARCH LOGIC
# ==========================================

def normalize_text(text):
    """
    Comprehensive text cleaner for Arabic & English:
    - Removes question mark sequences (????) and unreadable non-printable tokens
    - Removes Tashkeel/Diacritics
    - Normalizes Arabic letters (أ/إ/آ -> ا, ة -> ه, ى -> ي)
    - Strips special symbols/punctuation (; & : - / ?)
    - Removes common stop words (and, or, the, of, و)
    - Normalizes English transliterations (ee -> i, oo -> u)
    """
    if not isinstance(text, str):
        return ""

    # Ignore/remove sequences of question marks resulting from encoding issues (e.g., Arabic ????)
    text = re.sub(r'\?+', ' ', text)

    # 1. Remove Tashkeel / Harakat
    tashkeel_regex = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    text = re.sub(tashkeel_regex, '', text)

    # 2. Normalize Arabic character variants
    text = re.sub(r'[أإآٱ]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ؤ', 'و', text)
    text = re.sub(r'ئ', 'ي', text)

    # 3. Strip special characters, punctuation, and symbols
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)

    # 4. Strip Latin accents & convert to lowercase
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    text = text.lower().strip()

    # 5. Remove stop words & apply transliteration rules
    stop_words = {"and", "or", "the", "of", "in", "by", "a", "an", "و"}
    words = text.split()
    processed_words = []
    
    transliteration_rules = [
        (r'ee', 'i'),
        (r'oo', 'u'),
        (r'ah$', 'a'),
        (r'at$', 'a'),
    ]

    for word in words:
        if word in stop_words or word.startswith("?"):
            continue
        if re.search(r'[a-z]', word):
            for rule, replacement in transliteration_rules:
                word = re.sub(rule, replacement, word)
        processed_words.append(word)

    return " ".join(processed_words)

def calculate_best_match(query_norm, target_norm):
    """Computes similarity score using token set ratio and partial ratio."""
    if not target_norm:
        return 0
    partial = fuzz.partial_ratio(query_norm, target_norm)
    token_set = fuzz.token_set_ratio(query_norm, target_norm)
    return max(partial, token_set)

def search_books(query, threshold=60):
    """Performs search across titles, authors, and publishers."""
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

        title_score = calculate_best_match(query_norm, title_norm)
        author_score = calculate_best_match(query_norm, author_norm)
        publisher_score = calculate_best_match(query_norm, publisher_norm)

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

st.markdown("""
    <div class="header-banner">
        <h1>📚 Dar Makkah International</h1>
        <p>Library Catalogue & Search System</p>
    </div>
""", unsafe_allow_html=True)

tab_search, tab_admin = st.tabs(["🔍 Search Catalogue", "⚙️ Admin & Catalogue Management"])

# TAB 1: SEARCH
with tab_search:
    st.subheader("Search Library Collection")
    
    search_query = st.text_input(
        "Enter title, author, or publisher name:",
        placeholder="e.g., sunn;ah, Sahih & Bukhari, Seerah...",
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
                title_val = book.get("title") or "Untitled"
                author_val = book.get("author") or "Unknown Author"
                publisher_val = book.get("publisher") or "Unknown Publisher"
                category_val = book.get("category") or "General"
                shelf_val = book.get("shelf") or "Unassigned"
                isbn_val = book.get("isbn") or ""
                score_val = int(book.get("match_score", 0))

                # Fetch price and image assets via secrets.toml REST API endpoint
                api_details = fetch_api_book_details(title_val, isbn_val)
                price_val = api_details.get("price", "N/A")
                image_list = api_details.get("images", [])

                st.markdown(f"""
                    <div class="book-card">
                        <div class="book-title">📖 {title_val}</div>
                        <div class="book-meta">
                            <strong>Author:</strong> {author_val} &nbsp;|&nbsp; 
                            <strong>Publisher:</strong> {publisher_val} &nbsp;|&nbsp; 
                            <strong>Price:</strong> {price_val}
                        </div>
                        <div class="badge-container">
                            <span class="badge badge-category">📂 Category: {category_val}</span>
                            <span class="badge badge-shelf">📍 Shelf: {shelf_val}</span>
                            <span class="badge badge-match">Match Score: {score_val}%</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Render multiple images dynamically if returned by API
                if image_list:
                    st.caption("📸 **Book Cover / Images:**")
                    cols = st.columns(min(len(image_list), 4))
                    for idx, img_url in enumerate(image_list):
                        col_target = cols[idx % len(cols)]
                        col_target.image(img_url, use_column_width=True)

        else:
            st.warning("No matching books found. Try broadening your query or adjusting the sensitivity slider.")
    else:
        st.info("Enter a query above to start searching the catalogue.")

# TAB 2: ADMIN
with tab_admin:
    st.subheader("Catalogue Management Panel")

    df_current = get_all_books()
    st.metric(label="Total Registered Books", value=len(df_current))
    st.markdown("---")

    col_upload, col_danger = st.columns([2, 1])

    with col_upload:
        st.markdown('<div class="admin-card">', unsafe_allow_html=True)
        st.write("### 📥 Import Spreadsheet")
        uploaded_file = st.file_uploader(
            "Upload Excel File (.xlsx, .xls)", 
            type=["xlsx", "xls"]
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
