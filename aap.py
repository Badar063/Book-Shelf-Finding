import html
import re
import sqlite3
import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz


# ============================================================
# CONFIGURATION
# ============================================================

APP_TITLE = "Dar Makkah International"
APP_SUBTITLE = "Library Catalogue Search System"

DATABASE_FILE = Path(__file__).resolve().parent / "library.db"

MAX_RESULTS = 50

MIN_TITLE_SCORE = 82
MIN_AUTHOR_SCORE = 88
MIN_PUBLISHER_SCORE = 90


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CUSTOM CSS FOR HIGH-QUALITY UI/UX
# ============================================================

st.markdown(
    """
    <style>
    /* BASE LAYOUT */
    .stApp {
        background: #f4f7fa;
        color: #172033;
    }

    .main .block-container {
        max-width: 1200px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    /* HERO BANNER */
    .hero-box {
        background: linear-gradient(135deg, #103b5d 0%, #19597d 100%);
        border-radius: 16px;
        padding: 36px 40px;
        margin-bottom: 28px;
        box-shadow: 0 10px 25px rgba(16, 59, 93, 0.12);
    }

    .hero-title {
        color: #ffffff;
        font-size: 34px;
        font-weight: 800;
        line-height: 1.2;
    }

    .hero-subtitle {
        color: #d8e7ef;
        font-size: 16px;
        margin-top: 6px;
    }

    .gold-line {
        width: 60px;
        height: 4px;
        background: #c59a42;
        border-radius: 10px;
        margin-top: 16px;
    }

    /* HEADINGS */
    .section-heading {
        color: #103b5d;
        font-size: 22px;
        font-weight: 800;
        margin-top: 10px;
        margin-bottom: 4px;
    }

    .section-description {
        color: #667085;
        font-size: 14px;
        margin-bottom: 18px;
    }

    /* SEARCH INPUT CUSTOMIZATION */
    .stTextInput input {
        background: #ffffff !important;
        color: #172033 !important;
        border: 1px solid #d0d5dd !important;
        border-radius: 10px !important;
        min-height: 48px !important;
        font-size: 15px !important;
    }

    .stTextInput input:focus {
        border-color: #103b5d !important;
        box-shadow: 0 0 0 2px rgba(16, 59, 93, 0.2) !important;
    }

    /* METRICS CARDS */
    .metric-card {
        background: #ffffff;
        border: 1px solid #eaecf0;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
    }

    .metric-number {
        color: #103b5d;
        font-size: 28px;
        font-weight: 800;
    }

    .metric-label {
        color: #667085;
        font-size: 13px;
        font-weight: 600;
        margin-top: 2px;
    }

    /* CATALOGUE BOOK CARDS */
    .book-card {
        background: #ffffff;
        border: 1px solid #eaecf0;
        border-left: 5px solid #c59a42;
        border-radius: 10px;
        padding: 20px;
        margin-top: 12px;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(16, 24, 40, 0.04);
    }

    .book-title {
        color: #103b5d;
        font-size: 18px;
        font-weight: 800;
        line-height: 1.4;
        margin-bottom: 12px;
    }

    .card-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 12px;
    }

    .card-col {
        flex: 1;
        min-width: 240px;
    }

    .book-info {
        color: #475467;
        font-size: 14px;
        margin-bottom: 6px;
    }

    .book-label {
        color: #103b5d;
        font-weight: 700;
    }

    .shelf-box {
        display: inline-block;
        background: #fcf8ed;
        color: #80651f;
        border: 1px solid #ead9a7;
        border-radius: 6px;
        padding: 4px 10px;
        margin-top: 6px;
        font-size: 13px;
        font-weight: 700;
    }

    .match-box {
        display: inline-block;
        background: #edf5f8;
        color: #19597d;
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: 700;
    }

    /* MANAGEMENT SECTION CARDS */
    .management-card {
        background: #ffffff;
        border: 1px solid #eaecf0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 6px rgba(16, 24, 40, 0.04);
    }

    .management-title {
        color: #103b5d;
        font-size: 17px;
        font-weight: 800;
    }

    .management-description {
        color: #667085;
        font-size: 13.5px;
        margin-top: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CLEAN TEXT UTILITIES
# ============================================================

HTML_TAG_PATTERN = re.compile(r"<[^>]*>", flags=re.IGNORECASE)


def clean_catalogue_text(value):
    if value is None or pd.isna(value):
        return ""

    text = str(value)
    text = html.unescape(text)
    text = HTML_TAG_PATTERN.sub(" ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def display_text(value, fallback="—"):
    cleaned = clean_catalogue_text(value)
    return cleaned if cleaned else fallback


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_connection():
    connection = sqlite3.connect(
        DATABASE_FILE,
        timeout=30,
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_connection()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT DEFAULT '',
                publisher TEXT DEFAULT '',
                language TEXT DEFAULT '',
                shelf_no TEXT DEFAULT ''
            )
            """
        )
        columns = connection.execute("PRAGMA table_info(books)").fetchall()
        column_names = {row["name"] for row in columns}

        if "shelf_no" not in column_names:
            connection.execute(
                "ALTER TABLE books ADD COLUMN shelf_no TEXT DEFAULT ''"
            )

        connection.commit()
    finally:
        connection.close()


create_database()


# ============================================================
# LOAD & MANAGEMENT DATA OPERATIONS
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def load_books():
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT id, title, author, publisher, language, shelf_no
            FROM books
            ORDER BY title COLLATE NOCASE
            """
        ).fetchall()

        return [
            (
                row["id"],
                clean_catalogue_text(row["title"]),
                clean_catalogue_text(row["author"]),
                clean_catalogue_text(row["publisher"]),
                clean_catalogue_text(row["language"]),
                clean_catalogue_text(row["shelf_no"]),
            )
            for row in rows
        ]
    finally:
        connection.close()


def delete_all_books():
    connection = get_connection()
    try:
        connection.execute("DELETE FROM books")
        try:
            connection.execute(
                "DELETE FROM sqlite_sequence WHERE name = 'books'"
            )
        except sqlite3.OperationalError:
            pass
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    load_books.clear()


def replace_database(dataframe):
    connection = get_connection()
    try:
        connection.execute("DELETE FROM books")
        records = [
            (
                clean_catalogue_text(row["title"]),
                clean_catalogue_text(row["author"]),
                clean_catalogue_text(row["publisher"]),
                clean_catalogue_text(row["language"]),
                clean_catalogue_text(row["shelf_no"]),
            )
            for _, row in dataframe.iterrows()
        ]

        connection.executemany(
            """
            INSERT INTO books (title, author, publisher, language, shelf_no)
            VALUES (?, ?, ?, ?, ?)
            """,
            records,
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    load_books.clear()


# ============================================================
# TEXT NORMALIZATION & MATCHING
# ============================================================

ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)

ARABIC_TRANSLATION = str.maketrans(
    {
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
        "ى": "ي", "ئ": "ي", "ؤ": "و", "ـ": "",
        "ﻻ": "لا", "ﻷ": "لا", "ﻹ": "لا", "ﻵ": "لا",
    }
)


def normalize_text(text):
    text = clean_catalogue_text(text)
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text if not unicodedata.combining(char)
    )
    text = ARABIC_DIACRITICS.sub("", text)
    text = text.translate(ARABIC_TRANSLATION).lower()
    text = (
        text.replace("’", "'")
        .replace("‘", "'")
        .replace("–", "-")
        .replace("—", "-")
    )
    text = re.sub(r"[^\w\u0600-\u06FF]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def tokenize(text):
    val = normalize_text(text)
    return val.split() if val else []


def exact_token_match(query, field):
    q_tokens = tokenize(query)
    f_tokens = set(tokenize(field))
    return bool(q_tokens and f_tokens and all(t in f_tokens for t in q_tokens))


def phrase_contains(query, field):
    q, f = normalize_text(query), normalize_text(field)
    return bool(q and f and q in f)


def fuzzy_score(query, field):
    q, f = normalize_text(query), normalize_text(field)
    if not q or not f:
        return 0
    return max(
        fuzz.ratio(q, f),
        fuzz.partial_ratio(q, f),
        fuzz.token_set_ratio(q, f),
        fuzz.WRatio(q, f),
    )


def field_match(query, title, author, publisher):
    q = normalize_text(query)
    if not q:
        return None, 0

    q_tokens = tokenize(q)
    title_norm = normalize_text(title)

    # Title Search Rules
    if q == title_norm:
        return "Exact Title Match", 100
    if len(q_tokens) == 1 and q in tokenize(title):
        return "Title Keyword Match", 97
    if len(q_tokens) > 1 and exact_token_match(q, title):
        return "Title Keyword Match", 96
    if len(q) >= 4 and phrase_contains(q, title):
        return "Title Match", 95

    t_score = fuzzy_score(q, title)
    t_thresh = 93 if len(q) <= 3 else MIN_TITLE_SCORE
    if t_score >= t_thresh:
        return "Strong Title Match", t_score

    # Author Search Rules
    a_tokens = tokenize(author)
    if (len(q_tokens) == 1 and q in a_tokens) or (
        len(q_tokens) > 1 and exact_token_match(q, author)
    ):
        return "Author Match", 93

    a_score = fuzzy_score(q, author)
    if len(q) >= 4 and a_score >= MIN_AUTHOR_SCORE:
        return "Author Match", a_score

    # Publisher Search Rules
    p_tokens = tokenize(publisher)
    if (len(q_tokens) == 1 and q in p_tokens) or (
        len(q_tokens) > 1 and exact_token_match(q, publisher)
    ):
        return "Publisher Match", 90

    p_score = fuzzy_score(q, publisher)
    if len(q) >= 4 and p_score >= MIN_PUBLISHER_SCORE:
        return "Publisher Match", p_score

    return None, 0


def search_books(query, rows):
    results = []
    for row in rows:
        book_id, title, author, publisher, language, shelf_no = row
        reason, score = field_match(query, title, author, publisher)
        if not reason:
            continue

        results.append(
            {
                "id": book_id,
                "title": clean_catalogue_text(title),
                "author": clean_catalogue_text(author),
                "publisher": clean_catalogue_text(publisher),
                "language": clean_catalogue_text(language),
                "shelf_no": clean_catalogue_text(shelf_no),
                "score": round(score, 1),
                "reason": reason,
            }
        )

    priority = {
        "Exact Title Match": 0,
        "Title Keyword Match": 1,
        "Title Match": 2,
        "Strong Title Match": 3,
        "Author Match": 4,
        "Publisher Match": 5,
    }

    results.sort(
        key=lambda x: (
            priority.get(x["reason"], 99),
            -x["score"],
            normalize_text(x["title"]),
        )
    )
    return results[:MAX_RESULTS]


# ============================================================
# EXCEL PROCESSING UTILITIES
# ============================================================

def find_column(columns, names):
    norm_cols = {normalize_text(c): c for c in columns}
    for name in names:
        norm_name = normalize_text(name)
        if norm_name in norm_cols:
            return norm_cols[norm_name]
    return None


def process_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as exc:
        return None, f"Unable to read Excel file: {exc}"

    if df.empty:
        return None, "The Excel file is empty."

    df = df.dropna(axis=1, how="all")

    t_col = find_column(
        df.columns,
        ["title", "book title", "book", "name", "book name", "العنوان", "عنوان الكتاب", "اسم الكتاب"],
    )
    a_col = find_column(
        df.columns,
        ["author", "book author", "writer", "المؤلف", "اسم المؤلف"],
    )
    p_col = find_column(
        df.columns,
        ["publisher", "publishing house", "publisher name", "الناشر", "دار النشر"],
    )
    l_col = find_column(
        df.columns,
        ["language", "lang", "اللغة"],
    )
    s_col = find_column(
        df.columns,
        ["shelf no", "shelf no.", "shelf number", "shelf", "shelfno", "shelf_no", "location", "rack", "رف", "رقم الرف"],
    )

    if t_col is None:
        return None, "Could not find a valid Title column in the uploaded file."

    clean = pd.DataFrame()
    clean["title"] = df[t_col].fillna("").apply(clean_catalogue_text)
    clean["author"] = df[a_col].fillna("").apply(clean_catalogue_text) if a_col else ""
    clean["publisher"] = df[p_col].fillna("").apply(clean_catalogue_text) if p_col else ""
    clean["language"] = df[l_col].fillna("").apply(clean_catalogue_text) if l_col else ""
    clean["shelf_no"] = df[s_col].fillna("").apply(clean_catalogue_text) if s_col else ""

    clean = clean[clean["title"].str.strip() != ""]

    clean["_key"] = (
        clean["title"].map(normalize_text) + "|" +
        clean["author"].map(normalize_text) + "|" +
        clean["publisher"].map(normalize_text) + "|" +
        clean["shelf_no"].map(normalize_text)
    )
    clean = clean.drop_duplicates(subset=["_key"]).drop(columns=["_key"]).reset_index(drop=True)

    if clean.empty:
        return None, "No valid book records were found after parsing."

    return clean, None


# ============================================================
# APP UI & FLOW
# ============================================================

rows = load_books()
total_books = len(rows)
authors = {normalize_text(r[2]) for r in rows if normalize_text(r[2])}
publishers = {normalize_text(r[3]) for r in rows if normalize_text(r[3])}
languages = {normalize_text(r[4]) for r in rows if normalize_text(r[4])}
shelves = {normalize_text(r[5]) for r in rows if normalize_text(r[5])}

# HERO HEADER
st.markdown(
    f"""
    <div class="hero-box">
        <div class="hero-title">{APP_TITLE}</div>
        <div class="hero-subtitle">{APP_SUBTITLE}</div>
        <div class="gold-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

search_tab, management_tab = st.tabs(
    ["🔎 Catalogue Search", "📥 Catalogue Management"]
)

# ------------------------------------------------------------
# TAB 1: CATALOGUE SEARCH
# ------------------------------------------------------------
with search_tab:
    st.markdown(
        """
        <div class="section-heading">Search the Library Catalogue</div>
        <div class="section-description">Search by title, author, or publisher. Arabic and English are fully supported.</div>
        """,
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Catalogue Search",
        placeholder="Enter title, author or publisher...",
        label_visibility="collapsed",
    )

    if query.strip():
        results = search_books(query, rows)

        if results:
            result_count = len(results)
            st.markdown(
                f"""
                <div class="section-heading">
                    {result_count} Matching Record{"s" if result_count != 1 else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )

            for book in results:
                title = display_text(book["title"], "Untitled")
                author = display_text(book["author"])
                publisher = display_text(book["publisher"])
                language = display_text(book["language"])
                shelf_no = display_text(book["shelf_no"], "Not specified")
                reason = display_text(book["reason"], "Match")
                score = book["score"]

                # Fully encapsulated HTML string ensures rendered tags are unbroken
                card_html = f"""
                <div class="book-card">
                    <div class="book-title">{html.escape(title)}</div>
                    <div class="card-grid">
                        <div class="card-col">
                            <div class="book-info"><span class="book-label">Author:</span> {html.escape(author)}</div>
                            <div class="book-info"><span class="book-label">Publisher:</span> {html.escape(publisher)}</div>
                        </div>
                        <div class="card-col">
                            <div class="book-info"><span class="book-label">Language:</span> {html.escape(language)}</div>
                            <div class="shelf-box">📍 Shelf: {html.escape(shelf_no)}</div>
                        </div>
                    </div>
                    <div class="match-box">
                        {html.escape(reason)} · {score}%
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
        else:
            st.info("No matching books found. Try full titles, author names, or alternative keywords.")

    else:
        # OVERVIEW STATS
        st.markdown(
            """
            <div class="section-heading">Catalogue Overview</div>
            <div class="section-description">Current live statistics of stored records.</div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        metrics = [
            (total_books, "Total Books"),
            (len(authors), "Authors"),
            (len(publishers), "Publishers"),
            (len(shelves), "Shelf Locations"),
        ]

        for col, (num, label) in zip([c1, c2, c3, c4], metrics):
            with col:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-number">{num:,}</div>
                        <div class="metric-label">{label}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ------------------------------------------------------------
# TAB 2: MANAGEMENT
# ------------------------------------------------------------
with management_tab:
    st.markdown(
        """
        <div class="section-heading">Catalogue Management</div>
        <div class="section-description">Update or replace the current database via Excel uploads.</div>
        """,
        unsafe_allow_html=True,
    )

    # IMPORT EXCEL
    st.markdown(
        """
        <div class="management-card">
            <div class="management-title">📊 Import Excel Catalogue</div>
            <div class="management-description">Upload an updated Excel file. Valid records will replace the current dataset.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload Excel File",
        type=["xlsx", "xls"],
        help="Make sure the file includes a column for Title.",
    )

    if uploaded_file is not None:
        clean_df, error_msg = process_excel(uploaded_file)
        if error_msg:
            st.error(error_msg)
        else:
            st.success(f"Parsed {len(clean_df):,} valid records from file.")
            if st.button("Overwrite Database with Uploaded File", use_container_width=True):
                try:
                    replace_database(clean_df)
                    st.success("Catalogue replaced successfully!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to update database: {exc}")

    st.divider()

    # DELETE DATABASE
    st.markdown(
        """
        <div class="management-card">
            <div class="management-title">🗑️ Clear Catalogue Data</div>
            <div class="management-description">Completely wipe all stored books from the system database.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    delete_confirmation = st.checkbox("I confirm that I want to delete all stored records.")
    if st.button("Delete All Records", disabled=not delete_confirmation, use_container_width=True):
        try:
            delete_all_books()
            st.success("Database cleared.")
            st.rerun()
        except Exception as exc:
            st.error(f"Deletion failed: {exc}")
