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

DATABASE_FILE = Path("library.db")

MAX_RESULTS = 100

MIN_TITLE_SCORE = 72
MIN_AUTHOR_SCORE = 78
MIN_PUBLISHER_SCORE = 82


# ============================================================
# STREAMLIT
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# PROFESSIONAL LIGHT UI
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #F5F7FA;
        color: #172033;
    }

    .main .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    #MainMenu,
    footer {
        visibility: hidden;
    }

    header {
        background: transparent !important;
    }


    /* ---------- HEADER ---------- */

    .hero {
        background: linear-gradient(
            135deg,
            #12304A 0%,
            #174E70 100%
        );

        border-radius: 18px;
        padding: 2.2rem 2rem;
        margin-bottom: 1.8rem;

        box-shadow: 0 8px 30px rgba(18, 48, 74, 0.15);
    }

    .hero-title {
        color: white;
        font-size: 2.35rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: .3px;
    }

    .hero-subtitle {
        color: #D9E8F2;
        font-size: 1.05rem;
        margin-top: .5rem;
    }

    .hero-line {
        width: 70px;
        height: 4px;
        background: #C69A3A;
        border-radius: 5px;
        margin-top: 1rem;
    }


    /* ---------- SEARCH ---------- */

    .search-title {
        color: #12304A;
        font-size: 1.25rem;
        font-weight: 750;
        margin-bottom: .5rem;
    }

    .search-help {
        color: #667085;
        margin-bottom: .8rem;
    }

    .stTextInput > div > div > input {
        background: white !important;
        color: #172033 !important;

        border: 1px solid #D0D5DD !important;
        border-radius: 10px !important;

        padding: 13px !important;
        font-size: 1rem !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #174E70 !important;
        box-shadow: 0 0 0 1px #174E70 !important;
    }


    /* ---------- METRICS ---------- */

    .metric-card {
        background: white;
        border: 1px solid #E4E7EC;
        border-radius: 14px;

        padding: 1.25rem;

        box-shadow: 0 3px 12px rgba(16, 24, 40, .05);
    }

    .metric-number {
        color: #174E70;
        font-size: 1.9rem;
        font-weight: 800;
    }

    .metric-label {
        color: #667085;
        font-size: .86rem;
        margin-top: .2rem;
    }


    /* ---------- RESULT ---------- */

    .book-card {
        background: white;

        border: 1px solid #E4E7EC;
        border-left: 4px solid #C69A3A;

        border-radius: 12px;

        padding: 1.2rem 1.3rem;

        margin: 1rem 0 .45rem 0;

        box-shadow: 0 4px 14px rgba(16, 24, 40, .06);
    }

    .book-title {
        color: #12304A;
        font-size: 1.25rem;
        font-weight: 750;
        line-height: 1.4;
        margin-bottom: .7rem;
    }

    .badge {
        display: inline-block;

        background: #F2F4F7;
        color: #475467;

        border: 1px solid #E4E7EC;

        border-radius: 6px;

        padding: 4px 9px;

        margin-right: 5px;
        margin-bottom: 4px;

        font-size: .78rem;
        font-weight: 600;
    }

    .match {
        display: inline-block;

        background: #174E70;
        color: white;

        border-radius: 6px;

        padding: 4px 9px;

        font-size: .78rem;
        font-weight: 650;
    }

    .match-exact {
        background: #18794E;
    }

    .match-title {
        background: #1769AA;
    }

    .match-author {
        background: #087F8C;
    }

    .match-publisher {
        background: #9A6F00;
    }


    /* ---------- SECTION ---------- */

    .section-title {
        color: #12304A;
        font-size: 1.3rem;
        font-weight: 750;

        border-left: 4px solid #C69A3A;

        padding-left: .7rem;

        margin-top: 1.8rem;
        margin-bottom: .5rem;
    }

    .section-description {
        color: #667085;
        margin-bottom: 1rem;
    }


    /* ---------- IMPORT ---------- */

    .import-box {
        background: white;

        border: 1px solid #E4E7EC;
        border-radius: 14px;

        padding: 1.4rem;

        box-shadow: 0 3px 12px rgba(16, 24, 40, .05);
    }

    .import-title {
        color: #12304A;
        font-size: 1.15rem;
        font-weight: 750;
    }


    /* ---------- EMPTY ---------- */

    .empty {
        background: white;

        border: 1px solid #E4E7EC;

        border-radius: 14px;

        padding: 2.5rem;

        text-align: center;

        margin-top: 1rem;
    }

    .empty-icon {
        font-size: 2rem;
    }

    .empty-title {
        color: #12304A;
        font-size: 1.15rem;
        font-weight: 700;
        margin-top: .5rem;
    }

    .empty-text {
        color: #667085;
        margin-top: .4rem;
    }


    /* ---------- SYSTEM ---------- */

    .system {
        background: #12304A;
        color: white;

        border-radius: 14px;

        padding: 1.2rem 1.4rem;

        margin-top: 2rem;
    }

    .system-title {
        color: #D8B65A;
        font-weight: 750;
        margin-bottom: .7rem;
    }

    .system-row {
        display: flex;
        justify-content: space-between;

        padding: .45rem 0;

        border-bottom: 1px solid rgba(255,255,255,.12);

        font-size: .88rem;
    }

    .system-row:last-child {
        border-bottom: none;
    }

    .system-key {
        color: #B8C7D4;
    }

    .system-value {
        color: white;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
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

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            publisher TEXT,
            language TEXT
        )
        """
    )

    connection.commit()
    connection.close()


create_database()


# ============================================================
# LOAD DATABASE
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def load_books():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            title,
            author,
            publisher,
            language
        FROM books
        ORDER BY title COLLATE NOCASE
        """
    ).fetchall()

    connection.close()

    return tuple(
        (
            row["id"],
            row["title"] or "",
            row["author"] or "",
            row["publisher"] or "",
            row["language"] or "",
        )
        for row in rows
    )


# ============================================================
# NORMALIZATION
# ============================================================

ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)

ARABIC_TRANSLATION = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ئ": "ي",
        "ؤ": "و",
        "ـ": "",
        "ﻻ": "لا",
        "ﻷ": "لا",
        "ﻹ": "لا",
        "ﻵ": "لا",
    }
)


def normalize_text(text):

    if text is None:
        return ""

    text = str(text).strip()

    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    text = ARABIC_DIACRITICS.sub("", text)

    text = text.translate(ARABIC_TRANSLATION)

    text = text.lower()

    text = (
        text
        .replace("’", "'")
        .replace("‘", "'")
        .replace("–", "-")
        .replace("—", "-")
    )

    text = re.sub(
        r"[^\w\u0600-\u06FF]+",
        " ",
        text,
        flags=re.UNICODE,
    )

    return " ".join(text.split())


def tokenize(text):

    value = normalize_text(text)

    return value.split() if value else []


# ============================================================
# SEARCH
# ============================================================

def phrase_contains(query, field):

    query = normalize_text(query)
    field = normalize_text(field)

    return bool(query and field and query in field)


def exact_token_match(query, field):

    query_tokens = tokenize(query)
    field_tokens = set(tokenize(field))

    if not query_tokens or not field_tokens:
        return False

    return all(
        token in field_tokens
        for token in query_tokens
    )


def fuzzy_score(query, field):

    q = normalize_text(query)
    f = normalize_text(field)

    if not q or not f:
        return 0

    if q == f:
        return 100

    if q in f:
        return 98

    return max(
        fuzz.ratio(q, f),
        fuzz.partial_ratio(q, f),
        fuzz.token_set_ratio(q, f),
        fuzz.WRatio(q, f),
    )


def field_match(query, title, author, publisher):

    q = normalize_text(query)

    # Exact title
    if q == normalize_text(title) and q:
        return "Exact Title Match", 100

    # Title phrase
    if phrase_contains(q, title):
        return "Title Match", 98

    # Title words
    if exact_token_match(q, title):
        return "Title Keyword Match", 96

    # Fuzzy title
    score = fuzzy_score(q, title)

    if score >= MIN_TITLE_SCORE:
        return "Strong Title Match", score

    # Author
    if phrase_contains(q, author):
        return "Author Match", 94

    if exact_token_match(q, author):
        return "Author Keyword Match", 92

    score = fuzzy_score(q, author)

    if score >= MIN_AUTHOR_SCORE:
        return "Author Match", score * .96

    # Publisher
    if phrase_contains(q, publisher):
        return "Publisher Match", 91

    if exact_token_match(q, publisher):
        return "Publisher Keyword Match", 89

    score = fuzzy_score(q, publisher)

    if score >= MIN_PUBLISHER_SCORE:
        return "Publisher Match", score * .94

    return None, 0


def search_books(query, rows):

    results = []

    for row in rows:

        book_id, title, author, publisher, language = row

        reason, score = field_match(
            query,
            title,
            author,
            publisher,
        )

        if not reason:
            continue

        results.append(
            {
                "id": book_id,
                "title": title,
                "author": author,
                "publisher": publisher,
                "language": language,
                "score": round(score, 1),
                "reason": reason,
            }
        )

    priority = {
        "Exact Title Match": 0,
        "Title Match": 1,
        "Title Keyword Match": 2,
        "Strong Title Match": 3,
        "Author Match": 4,
        "Author Keyword Match": 5,
        "Publisher Match": 6,
        "Publisher Keyword Match": 7,
    }

    results.sort(
        key=lambda item: (
            priority.get(item["reason"], 99),
            -item["score"],
            normalize_text(item["title"]),
        )
    )

    return results[:MAX_RESULTS]


# ============================================================
# EXCEL IMPORT
# ============================================================

def find_column(columns, possible_names):

    normalized = {
        normalize_text(column): column
        for column in columns
    }

    for name in possible_names:

        name_normalized = normalize_text(name)

        if name_normalized in normalized:
            return normalized[name_normalized]

    return None


def process_excel(uploaded_file):

    try:

        dataframe = pd.read_excel(
            uploaded_file
        )

    except Exception as exc:

        return None, f"Unable to read Excel file: {exc}"


    if dataframe.empty:
        return None, "The Excel file is empty."


    # Remove completely empty columns
    dataframe = dataframe.dropna(
        axis=1,
        how="all",
    )


    # --------------------------------------------------------
    # Detect columns
    # --------------------------------------------------------

    title_column = find_column(
        dataframe.columns,
        [
            "title",
            "book title",
            "book",
            "name",
            "book name",
            "العنوان",
            "عنوان الكتاب",
            "اسم الكتاب",
        ],
    )

    author_column = find_column(
        dataframe.columns,
        [
            "author",
            "book author",
            "writer",
            "المؤلف",
            "اسم المؤلف",
        ],
    )

    publisher_column = find_column(
        dataframe.columns,
        [
            "publisher",
            "publishing house",
            "publisher name",
            "الناشر",
            "دار النشر",
        ],
    )

    language_column = find_column(
        dataframe.columns,
        [
            "language",
            "lang",
            "اللغة",
        ],
    )


    if title_column is None:

        return (
            None,
            "Could not find a Title column. "
            "Please name the column 'Title' or 'Book Title'.",
        )


    # --------------------------------------------------------
    # Build clean dataframe
    # --------------------------------------------------------

    clean = pd.DataFrame()

    clean["title"] = (
        dataframe[title_column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    if author_column:
        clean["author"] = (
            dataframe[author_column]
            .fillna("")
            .astype(str)
            .str.strip()
        )
    else:
        clean["author"] = ""


    if publisher_column:
        clean["publisher"] = (
            dataframe[publisher_column]
            .fillna("")
            .astype(str)
            .str.strip()
        )
    else:
        clean["publisher"] = ""


    if language_column:
        clean["language"] = (
            dataframe[language_column]
            .fillna("")
            .astype(str)
            .str.strip()
        )
    else:
        clean["language"] = ""


    # Remove empty titles
    clean = clean[
        clean["title"].str.strip() != ""
    ]


    # Remove duplicate books
    clean["_duplicate_key"] = (
        clean["title"].map(normalize_text)
        + "|"
        + clean["author"].map(normalize_text)
        + "|"
        + clean["publisher"].map(normalize_text)
    )

    clean = clean.drop_duplicates(
        subset=["_duplicate_key"]
    )

    clean = clean.drop(
        columns=["_duplicate_key"]
    )

    clean = clean.reset_index(drop=True)


    if clean.empty:
        return None, "No valid book records were found."


    return clean, None


def replace_database(dataframe):

    connection = get_connection()

    try:

        connection.execute(
            "DELETE FROM books"
        )

        records = [
            (
                row["title"],
                row["author"],
                row["publisher"],
                row["language"],
            )
            for _, row in dataframe.iterrows()
        ]

        connection.executemany(
            """
            INSERT INTO books (
                title,
                author,
                publisher,
                language
            )
            VALUES (?, ?, ?, ?)
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
# HEADER
# ============================================================

st.markdown(
    f"""
    <div class="hero">

        <div class="hero-title">
            {html.escape(APP_TITLE)}
        </div>

        <div class="hero-subtitle">
            {html.escape(APP_SUBTITLE)}
        </div>

        <div class="hero-line"></div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE DATA
# ============================================================

rows = load_books()

total_books = len(rows)

authors = {
    normalize_text(row[2])
    for row in rows
    if normalize_text(row[2])
}

publishers = {
    normalize_text(row[3])
    for row in rows
    if normalize_text(row[3])
}

languages = {
    normalize_text(row[4])
    for row in rows
    if normalize_text(row[4])
}


# ============================================================
# NAVIGATION
# ============================================================

search_tab, import_tab = st.tabs(
    [
        "🔎 Catalogue Search",
        "📥 Catalogue Management",
    ]
)


# ============================================================
# SEARCH TAB
# ============================================================

with search_tab:

    st.markdown(
        """
        <div class="search-title">
            Search the Library Catalogue
        </div>

        <div class="search-help">
            Search by title, author, publisher or keyword.
            Arabic and English text are supported.
        </div>
        """,
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Search",
        placeholder="e.g. Riyad al-Salihin, Ibn Kathir, Dar al-Fikr...",
        label_visibility="collapsed",
    )


    if query.strip():

        results = search_books(
            query,
            rows,
        )

        if results:

            st.markdown(
                f"""
                <div class="section-title">
                    {len(results)} Matching Record(s)
                </div>
                """,
                unsafe_allow_html=True,
            )

            for book in results:

                reason = book["reason"]

                if reason == "Exact Title Match":
                    match_class = "match-exact"

                elif "Title" in reason:
                    match_class = "match-title"

                elif "Author" in reason:
                    match_class = "match-author"

                elif "Publisher" in reason:
                    match_class = "match-publisher"

                else:
                    match_class = ""

                st.markdown(
                    f"""
                    <div class="book-card">

                        <div class="book-title">
                            {html.escape(book["title"])}
                        </div>

                        <span class="badge">
                            Author:
                            {html.escape(book["author"] or "—")}
                        </span>

                        <span class="badge">
                            Publisher:
                            {html.escape(book["publisher"] or "—")}
                        </span>

                        <span class="badge">
                            Language:
                            {html.escape(book["language"] or "—")}
                        </span>

                        <span class="match {match_class}">
                            {html.escape(reason)}
                            · {book["score"]}%
                        </span>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:

            st.markdown(
                """
                <div class="empty">

                    <div class="empty-icon">
                        🔍
                    </div>

                    <div class="empty-title">
                        No matching books found
                    </div>

                    <div class="empty-text">
                        Try another title, author,
                        publisher or keyword.
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


    else:

        st.markdown(
            """
            <div class="section-title">
                Catalogue Overview
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        metrics = [
            (total_books, "Books"),
            (len(authors), "Authors"),
            (len(publishers), "Publishers"),
            (len(languages), "Languages"),
        ]

        for column, (number, label) in zip(
            [c1, c2, c3, c4],
            metrics,
        ):

            with column:

                st.markdown(
                    f"""
                    <div class="metric-card">

                        <div class="metric-number">
                            {number:,}
                        </div>

                        <div class="metric-label">
                            {label}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ============================================================
# IMPORT TAB
# ============================================================

with import_tab:

    st.markdown(
        """
        <div class="section-title">
            Catalogue Management
        </div>

        <div class="section-description">
            Upload your Excel catalogue to create or replace
            the library database.
        </div>
        """,
        unsafe_allow_html=True,
    )


    st.markdown(
        """
        <div class="import-box">

            <div class="import-title">
                📊 Import Excel Catalogue
            </div>

            <p style="color:#667085;">
                Recommended columns:
                <b>Title</b>, <b>Author</b>,
                <b>Publisher</b>, and optionally
                <b>Language</b>.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )


    uploaded_file = st.file_uploader(
        "Upload Excel catalogue",
        type=["xlsx", "xls"],
        help="Upload your library catalogue in Excel format.",
    )


    if uploaded_file:

        dataframe, error = process_excel(
            uploaded_file
        )

        if error:

            st.error(error)

        else:

            st.success(
                f"Excel file successfully read. "
                f"{len(dataframe):,} book records detected."
            )


            st.markdown(
                "### Preview"
            )

            st.dataframe(
                dataframe.head(10),
                use_container_width=True,
                hide_index=True,
            )


            p1, p2, p3 = st.columns(3)

            with p1:
                st.metric(
                    "Books Detected",
                    f"{len(dataframe):,}",
                )

            with p2:
                st.metric(
                    "Authors",
                    dataframe["author"]
                    .replace("", pd.NA)
                    .dropna()
                    .nunique(),
                )

            with p3:
                st.metric(
                    "Publishers",
                    dataframe["publisher"]
                    .replace("", pd.NA)
                    .dropna()
                    .nunique(),
                )


            st.warning(
                "Importing this catalogue will replace "
                "the current contents of library.db."
            )


            if st.button(
                "💾 Replace Database with This Catalogue",
                type="primary",
                use_container_width=True,
            ):

                try:

                    replace_database(
                        dataframe
                    )

                    st.success(
                        f"Successfully imported "
                        f"{len(dataframe):,} books into library.db."
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Database update failed: {exc}"
                    )


# ============================================================
# SYSTEM INFORMATION
# ============================================================

st.markdown(
    f"""
    <div class="system">

        <div class="system-title">
            System Information
        </div>

        <div class="system-row">
            <span class="system-key">
                Database
            </span>

            <span class="system-value">
                {html.escape(DATABASE_FILE.name)}
            </span>
        </div>

        <div class="system-row">
            <span class="system-key">
                Books Indexed
            </span>

            <span class="system-value">
                {total_books:,}
            </span>
        </div>

        <div class="system-row">
            <span class="system-key">
                Search Engine
            </span>

            <span class="system-value">
                Exact + Token + Fuzzy
            </span>
        </div>

        <div class="system-row">
            <span class="system-key">
                Catalogue Source
            </span>

            <span class="system-value">
                Excel
            </span>
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)
