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
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL
       ======================================================== */

    .stApp {
        background-color: #F6F8FB;
        color: #172033;
    }

    .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent !important;
    }


    /* ========================================================
       HEADER
       ======================================================== */

    .hero-box {
        background: #123B5D;
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 28px;
        box-shadow: 0 8px 25px rgba(18, 59, 93, 0.12);
    }

    .hero-title-text {
        color: #FFFFFF;
        font-size: 36px;
        font-weight: 800;
        line-height: 1.2;
        margin: 0;
    }

    .hero-subtitle-text {
        color: #DCE8F0;
        font-size: 17px;
        margin-top: 8px;
    }

    .gold-line {
        width: 65px;
        height: 4px;
        background: #C49A42;
        border-radius: 10px;
        margin-top: 18px;
    }


    /* ========================================================
       SECTION HEADINGS
       ======================================================== */

    .section-title-text {
        color: #123B5D;
        font-size: 24px;
        font-weight: 750;
        margin-top: 15px;
        margin-bottom: 5px;
    }

    .section-description-text {
        color: #667085;
        font-size: 15px;
        margin-bottom: 18px;
    }


    /* ========================================================
       SEARCH INPUT
       ======================================================== */

    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #172033 !important;
        border: 1px solid #D0D5DD !important;
        border-radius: 10px !important;
        min-height: 48px !important;
    }

    .stTextInput input:focus {
        border-color: #123B5D !important;
        box-shadow: 0 0 0 1px #123B5D !important;
    }


    /* ========================================================
       METRIC CARDS
       ======================================================== */

    .metric-box {
        background: #FFFFFF;
        border: 1px solid #E4E7EC;
        border-radius: 14px;
        padding: 22px;
        min-height: 105px;
        box-shadow: 0 3px 12px rgba(16, 24, 40, 0.05);
    }

    .metric-number-text {
        color: #123B5D;
        font-size: 30px;
        font-weight: 800;
    }

    .metric-label-text {
        color: #667085;
        font-size: 14px;
        margin-top: 3px;
    }


    /* ========================================================
       BOOK CARD
       ======================================================== */

    .book-box {
        background: #FFFFFF;
        border: 1px solid #E4E7EC;
        border-left: 4px solid #C49A42;
        border-radius: 12px;
        padding: 20px;
        margin-top: 14px;
        margin-bottom: 8px;
        box-shadow: 0 4px 14px rgba(16, 24, 40, 0.05);
    }

    .book-title-text {
        color: #123B5D;
        font-size: 20px;
        font-weight: 750;
        line-height: 1.4;
        margin-bottom: 12px;
    }

    .book-info {
        color: #475467;
        font-size: 14px;
        margin-top: 5px;
    }


    /* ========================================================
       IMPORT
       ======================================================== */

    .import-box {
        background: #FFFFFF;
        border: 1px solid #E4E7EC;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 3px 12px rgba(16, 24, 40, 0.05);
    }

    .import-title-text {
        color: #123B5D;
        font-size: 20px;
        font-weight: 750;
    }

    .import-description {
        color: #667085;
        font-size: 14px;
        margin-top: 5px;
    }


    /* ========================================================
       EMPTY STATE
       ======================================================== */

    .empty-box {
        background: #FFFFFF;
        border: 1px solid #E4E7EC;
        border-radius: 14px;
        padding: 40px;
        text-align: center;
        margin-top: 20px;
    }

    .empty-title-text {
        color: #123B5D;
        font-size: 19px;
        font-weight: 700;
    }

    .empty-description {
        color: #667085;
        margin-top: 6px;
    }


    /* ========================================================
       SYSTEM INFORMATION
       ======================================================== */

    .system-box {
        background: #123B5D;
        border-radius: 14px;
        padding: 22px;
        margin-top: 35px;
    }

    .system-title-text {
        color: #D9B866;
        font-size: 17px;
        font-weight: 750;
        margin-bottom: 12px;
    }

    .system-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.12);
    }

    .system-row:last-child {
        border-bottom: none;
    }

    .system-key {
        color: #B8C7D4;
    }

    .system-value {
        color: #FFFFFF;
        font-weight: 600;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {
        border-radius: 9px;
        min-height: 45px;
        font-weight: 650;
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
            title TEXT NOT NULL,
            author TEXT DEFAULT '',
            publisher TEXT DEFAULT '',
            language TEXT DEFAULT ''
        )
        """
    )

    connection.commit()
    connection.close()


create_database()


# ============================================================
# LOAD BOOKS
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

    return [
        (
            row["id"],
            row["title"] or "",
            row["author"] or "",
            row["publisher"] or "",
            row["language"] or "",
        )
        for row in rows
    ]


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
        char
        for char in text
        if not unicodedata.combining(char)
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

    if not query or not field:
        return False

    return query in field


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

    if not q:
        return None, 0

    # Exact title
    if q == normalize_text(title):
        return "Exact Title Match", 100

    # Title phrase
    if phrase_contains(q, title):
        return "Title Match", 98

    # Title keywords
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
        return "Author Match", score * 0.96

    # Publisher
    if phrase_contains(q, publisher):
        return "Publisher Match", 91

    if exact_token_match(q, publisher):
        return "Publisher Keyword Match", 89

    score = fuzzy_score(q, publisher)

    if score >= MIN_PUBLISHER_SCORE:
        return "Publisher Match", score * 0.94

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
# EXCEL HELPERS
# ============================================================

def find_column(columns, names):

    normalized_columns = {
        normalize_text(column): column
        for column in columns
    }

    for name in names:

        normalized_name = normalize_text(name)

        if normalized_name in normalized_columns:
            return normalized_columns[normalized_name]

    return None


def process_excel(uploaded_file):

    try:

        dataframe = pd.read_excel(uploaded_file)

    except Exception as exc:

        return None, f"Unable to read Excel file: {exc}"

    if dataframe.empty:
        return None, "The Excel file is empty."

    dataframe = dataframe.dropna(
        axis=1,
        how="all",
    )

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
            "Please name it 'Title' or 'Book Title'.",
        )

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

    clean = clean[
        clean["title"].str.strip() != ""
    ]

    clean["_key"] = (
        clean["title"].map(normalize_text)
        + "|"
        + clean["author"].map(normalize_text)
        + "|"
        + clean["publisher"].map(normalize_text)
    )

    clean = clean.drop_duplicates(
        subset=["_key"]
    )

    clean = clean.drop(
        columns=["_key"]
    )

    clean = clean.reset_index(drop=True)

    if clean.empty:
        return None, "No valid book records were found."

    return clean, None


# ============================================================
# DATABASE REPLACEMENT
# ============================================================

def replace_database(dataframe):

    connection = get_connection()

    try:

        connection.execute(
            "DELETE FROM books"
        )

        records = [
            (
                str(row["title"]),
                str(row["author"]),
                str(row["publisher"]),
                str(row["language"]),
            )
            for _, row in dataframe.iterrows()
        ]

        connection.executemany(
            """
            INSERT INTO books
            (
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
    <div class="hero-box">
        <div class="hero-title-text">
            {APP_TITLE}
        </div>

        <div class="hero-subtitle-text">
            {APP_SUBTITLE}
        </div>

        <div class="gold-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD DATA
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

search_tab, management_tab = st.tabs(
    [
        "🔎 Catalogue Search",
        "📥 Catalogue Management",
    ]
)


# ============================================================
# SEARCH
# ============================================================

with search_tab:

    st.markdown(
        '<div class="section-title-text">'
        'Search the Library Catalogue'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description-text">'
        'Search by title, author, publisher or keyword. '
        'Arabic and English text are supported.'
        '</div>',
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Catalogue Search",
        placeholder=(
            "Enter book title, author, publisher or keyword..."
        ),
        label_visibility="collapsed",
    )

    if query.strip():

        results = search_books(
            query,
            rows,
        )

        if results:

            st.markdown(
                f'<div class="section-title-text">'
                f'{len(results)} Matching Record(s)'
                f'</div>',
                unsafe_allow_html=True,
            )

            for book in results:

                st.markdown(
                    f"""
                    <div class="book-box">

                        <div class="book-title-text">
                            {book["title"]}
                        </div>

                        <div class="book-info">
                            <b>Author:</b>
                            {book["author"] or "—"}
                        </div>

                        <div class="book-info">
                            <b>Publisher:</b>
                            {book["publisher"] or "—"}
                        </div>

                        <div class="book-info">
                            <b>Language:</b>
                            {book["language"] or "—"}
                        </div>

                        <div class="book-info">
                            <b>Match:</b>
                            {book["reason"]}
                            ({book["score"]}%)
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:

            st.markdown(
                """
                <div class="empty-box">

                    <div style="font-size:34px;">
                        🔍
                    </div>

                    <div class="empty-title-text">
                        No matching books found
                    </div>

                    <div class="empty-description">
                        Try another title, author,
                        publisher or keyword.
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.markdown(
            '<div class="section-title-text">'
            'Catalogue Overview'
            '</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        metric_data = [
            (total_books, "Books"),
            (len(authors), "Authors"),
            (len(publishers), "Publishers"),
            (len(languages), "Languages"),
        ]

        for column, (number, label) in zip(
            [c1, c2, c3, c4],
            metric_data,
        ):

            with column:

                st.markdown(
                    f"""
                    <div class="metric-box">

                        <div class="metric-number-text">
                            {number:,}
                        </div>

                        <div class="metric-label-text">
                            {label}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ============================================================
# MANAGEMENT
# ============================================================

with management_tab:

    st.markdown(
        '<div class="section-title-text">'
        'Catalogue Management'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description-text">'
        'Upload your Excel catalogue and replace the '
        'current catalogue database.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="import-box">

            <div class="import-title-text">
                📊 Excel Catalogue Import
            </div>

            <div class="import-description">
                Recommended columns:
                Title, Author, Publisher and Language.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload Excel file",
        type=["xlsx", "xls"],
    )

    if uploaded_file:

        dataframe, error = process_excel(
            uploaded_file
        )

        if error:

            st.error(error)

        else:

            st.success(
                f"{len(dataframe):,} book records detected."
            )

            st.markdown("### Preview")

            st.dataframe(
                dataframe.head(20),
                use_container_width=True,
                hide_index=True,
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric(
                    "Books",
                    f"{len(dataframe):,}",
                )

            with c2:
                st.metric(
                    "Authors",
                    dataframe["author"]
                    .replace("", pd.NA)
                    .dropna()
                    .nunique(),
                )

            with c3:
                st.metric(
                    "Publishers",
                    dataframe["publisher"]
                    .replace("", pd.NA)
                    .dropna()
                    .nunique(),
                )

            st.warning(
                "This will replace the current contents "
                "of library.db."
            )

            if st.button(
                "💾 Import Catalogue",
                type="primary",
                use_container_width=True,
            ):

                try:

                    replace_database(
                        dataframe
                    )

                    st.success(
                        f"Successfully imported "
                        f"{len(dataframe):,} books."
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
    '<div class="system-box">'
    '<div class="system-title-text">'
    'System Information'
    '</div>'
    f'<div class="system-row">'
    f'<span class="system-key">Database</span>'
    f'<span class="system-value">{DATABASE_FILE.name}</span>'
    f'</div>'
    f'<div class="system-row">'
    f'<span class="system-key">Books Indexed</span>'
    f'<span class="system-value">{total_books:,}</span>'
    f'</div>'
    f'<div class="system-row">'
    f'<span class="system-key">Search Engine</span>'
    f'<span class="system-value">Exact + Token + Fuzzy</span>'
    f'</div>'
    f'<div class="system-row">'
    f'<span class="system-key">Catalogue Source</span>'
    f'<span class="system-value">Excel</span>'
    f'</div>'
    '</div>',
    unsafe_allow_html=True,
)
