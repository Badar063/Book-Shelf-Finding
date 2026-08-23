import re
import sqlite3
import html
import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz


# ============================================================
# CONFIG
# ============================================================

APP_TITLE = "Dar Makkah International"
APP_SUBTITLE = "Library Catalogue Search System"

# Keep database beside this Python file.
BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR / "library.db"

MAX_RESULTS = 100

MIN_TITLE_SCORE = 72
MIN_AUTHOR_SCORE = 78
MIN_PUBLISHER_SCORE = 82


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background: #f5f7fa;
    color: #172033;
}

.main .block-container {
    max-width: 1200px;
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

.hero {
    background: linear-gradient(135deg, #123b5d, #1b587d);
    border-radius: 18px;
    padding: 34px 36px;
    margin-bottom: 28px;
    box-shadow: 0 8px 28px rgba(18, 59, 93, 0.15);
}

.hero-title {
    color: #ffffff;
    font-size: 36px;
    font-weight: 800;
    line-height: 1.2;
}

.hero-subtitle {
    color: #dbe8f0;
    font-size: 17px;
    margin-top: 8px;
}

.hero-line {
    width: 65px;
    height: 4px;
    background: #c49a42;
    border-radius: 10px;
    margin-top: 18px;
}

.section-title {
    color: #123b5d;
    font-size: 24px;
    font-weight: 750;
    margin-top: 12px;
    margin-bottom: 6px;
}

.section-description {
    color: #667085;
    font-size: 15px;
    margin-bottom: 18px;
}

.stTextInput input {
    background: #ffffff !important;
    color: #172033 !important;
    border: 1px solid #d0d5dd !important;
    border-radius: 10px !important;
    min-height: 48px !important;
    font-size: 16px !important;
}

.stTextInput input:focus {
    border-color: #123b5d !important;
    box-shadow: 0 0 0 1px #123b5d !important;
}

.metric-card {
    background: #ffffff;
    border: 1px solid #e4e7ec;
    border-radius: 14px;
    padding: 22px;
    min-height: 105px;
    box-shadow: 0 3px 12px rgba(16, 24, 40, 0.05);
}

.metric-number {
    color: #123b5d;
    font-size: 30px;
    font-weight: 800;
}

.metric-label {
    color: #667085;
    font-size: 14px;
    margin-top: 4px;
}

.book-card {
    background: #ffffff;
    border: 1px solid #e4e7ec;
    border-left: 4px solid #c49a42;
    border-radius: 12px;
    padding: 20px;
    margin-top: 14px;
    margin-bottom: 8px;
    box-shadow: 0 4px 14px rgba(16, 24, 40, 0.05);
}

.book-title {
    color: #123b5d;
    font-size: 20px;
    font-weight: 750;
    line-height: 1.4;
    margin-bottom: 12px;
}

.book-info {
    color: #475467;
    font-size: 14px;
    margin: 6px 0;
}

.book-label {
    color: #123b5d;
    font-weight: 700;
}

.match-badge {
    display: inline-block;
    background: #eaf2f7;
    color: #123b5d;
    border-radius: 6px;
    padding: 5px 9px;
    margin-top: 8px;
    font-size: 13px;
    font-weight: 650;
}

.import-card {
    background: #ffffff;
    border: 1px solid #e4e7ec;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 18px;
    box-shadow: 0 3px 12px rgba(16, 24, 40, 0.05);
}

.import-title {
    color: #123b5d;
    font-size: 20px;
    font-weight: 750;
}

.import-text {
    color: #667085;
    font-size: 14px;
    margin-top: 6px;
}

.empty-card {
    background: #ffffff;
    border: 1px solid #e4e7ec;
    border-radius: 14px;
    padding: 40px;
    text-align: center;
    margin-top: 20px;
}

.empty-icon {
    font-size: 34px;
}

.empty-title {
    color: #123b5d;
    font-size: 19px;
    font-weight: 700;
    margin-top: 8px;
}

.empty-text {
    color: #667085;
    margin-top: 6px;
}

.system-card {
    background: #123b5d;
    border-radius: 14px;
    padding: 22px;
    margin-top: 35px;
}

.system-title {
    color: #d9b866;
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
    color: #b8c7d4;
}

.system-value {
    color: #ffffff;
    font-weight: 600;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    height: 48px;
    border-radius: 8px 8px 0 0;
    padding-left: 18px;
    padding-right: 18px;
    font-weight: 650;
}

.stButton > button {
    border-radius: 9px;
    min-height: 45px;
    font-weight: 650;
}

.danger-box {
    background: #fff4f4;
    border: 1px solid #f1b5b5;
    border-radius: 12px;
    padding: 18px;
    margin-top: 20px;
    margin-bottom: 15px;
}

.danger-title {
    color: #a61b1b;
    font-weight: 750;
    font-size: 18px;
}

.danger-text {
    color: #6b3030;
    margin-top: 6px;
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

    try:
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

    finally:
        connection.close()


create_database()


# ============================================================
# LOAD BOOKS
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def load_books():

    connection = get_connection()

    try:
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

    finally:
        connection.close()


# ============================================================
# HTML CLEANING
# ============================================================

def clean_excel_text(value):
    """
    Remove HTML tags and decode HTML entities from Excel cells.

    Example:
        <p>Introduction to Python</p>
    becomes:
        Introduction to Python
    """

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    text = str(value)

    # Decode things such as:
    # &amp; -> &
    # &quot; -> "
    text = html.unescape(text)

    # Convert common HTML line breaks
    text = re.sub(
        r"<\s*br\s*/?\s*>",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"</\s*(p|div|li|tr|h[1-6])\s*>",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # Remove remaining HTML tags
    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    # Remove any leftover HTML entities
    text = html.unescape(text)

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# TEXT NORMALIZATION
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

    text = clean_excel_text(text)

    if not text:
        return ""

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    text = ARABIC_DIACRITICS.sub(
        "",
        text,
    )

    text = text.translate(
        ARABIC_TRANSLATION
    )

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

    return bool(
        query
        and field
        and query in field
    )


def exact_token_match(query, field):

    query_tokens = tokenize(query)
    field_tokens = set(
        tokenize(field)
    )

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


def field_match(
    query,
    title,
    author,
    publisher,
):

    q = normalize_text(query)

    if not q:
        return None, 0

    # -------------------------------
    # TITLE
    # -------------------------------

    if q == normalize_text(title):
        return "Exact Title Match", 100

    if phrase_contains(q, title):
        return "Title Match", 98

    if exact_token_match(q, title):
        return "Title Keyword Match", 96

    score = fuzzy_score(
        q,
        title,
    )

    if score >= MIN_TITLE_SCORE:
        return "Strong Title Match", score

    # -------------------------------
    # AUTHOR
    # -------------------------------

    if phrase_contains(q, author):
        return "Author Match", 94

    if exact_token_match(q, author):
        return "Author Keyword Match", 92

    score = fuzzy_score(
        q,
        author,
    )

    if score >= MIN_AUTHOR_SCORE:
        return "Author Match", score * 0.96

    # -------------------------------
    # PUBLISHER
    # -------------------------------

    if phrase_contains(q, publisher):
        return "Publisher Match", 91

    if exact_token_match(q, publisher):
        return "Publisher Keyword Match", 89

    score = fuzzy_score(
        q,
        publisher,
    )

    if score >= MIN_PUBLISHER_SCORE:
        return "Publisher Match", score * 0.94

    return None, 0


def search_books(query, rows):

    results = []

    for row in rows:

        (
            book_id,
            title,
            author,
            publisher,
            language,
        ) = row

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
                "title": clean_excel_text(title),
                "author": clean_excel_text(author),
                "publisher": clean_excel_text(publisher),
                "language": clean_excel_text(language),
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
            priority.get(
                item["reason"],
                99,
            ),
            -item["score"],
            normalize_text(
                item["title"]
            ),
        )
    )

    return results[:MAX_RESULTS]


# ============================================================
# EXCEL
# ============================================================

def find_column(
    columns,
    names,
):

    normalized_columns = {
        normalize_text(column): column
        for column in columns
    }

    for name in names:

        normalized_name = normalize_text(
            name
        )

        if normalized_name in normalized_columns:
            return normalized_columns[
                normalized_name
            ]

    return None


def process_excel(uploaded_file):

    try:

        dataframe = pd.read_excel(
            uploaded_file
        )

    except Exception as exc:

        return (
            None,
            f"Unable to read Excel file: {exc}",
        )

    if dataframe.empty:
        return None, "The Excel file is empty."

    dataframe = dataframe.dropna(
        axis=1,
        how="all",
    )

    # -------------------------------
    # FIND COLUMNS
    # -------------------------------

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

    # -------------------------------
    # CLEAN DATA
    # -------------------------------

    clean = pd.DataFrame()

    clean["title"] = (
        dataframe[title_column]
        .apply(clean_excel_text)
    )

    if author_column is not None:

        clean["author"] = (
            dataframe[author_column]
            .apply(clean_excel_text)
        )

    else:

        clean["author"] = ""

    if publisher_column is not None:

        clean["publisher"] = (
            dataframe[publisher_column]
            .apply(clean_excel_text)
        )

    else:

        clean["publisher"] = ""

    if language_column is not None:

        clean["language"] = (
            dataframe[language_column]
            .apply(clean_excel_text)
        )

    else:

        clean["language"] = ""

    # -------------------------------
    # REMOVE EMPTY TITLES
    # -------------------------------

    clean = clean[
        clean["title"].map(
            normalize_text
        ) != ""
    ]

    # -------------------------------
    # REMOVE DUPLICATES
    # -------------------------------

    clean["_key"] = (
        clean["title"].map(normalize_text)
        + "|"
        + clean["author"].map(normalize_text)
        + "|"
        + clean["publisher"].map(normalize_text)
    )

    clean = clean.drop_duplicates(
        subset=["_key"],
        keep="first",
    )

    clean = clean.drop(
        columns=["_key"]
    )

    clean = clean.reset_index(
        drop=True
    )

    if clean.empty:

        return (
            None,
            "No valid book records were found.",
        )

    return clean, None


# ============================================================
# DATABASE REPLACEMENT
# ============================================================

def replace_database(dataframe):

    connection = get_connection()

    try:

        # IMPORTANT:
        # Delete the entire old catalogue first.
        connection.execute(
            "DELETE FROM books"
        )

        records = [
            (
                clean_excel_text(
                    row["title"]
                ),
                clean_excel_text(
                    row["author"]
                ),
                clean_excel_text(
                    row["publisher"]
                ),
                clean_excel_text(
                    row["language"]
                ),
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
# CLEAR DATABASE
# ============================================================

def clear_database():

    connection = get_connection()

    try:

        connection.execute(
            "DELETE FROM books"
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()

    load_books.clear()


# ============================================================
# DATABASE INFO
# ============================================================

def database_book_count():

    connection = get_connection()

    try:

        result = connection.execute(
            "SELECT COUNT(*) FROM books"
        ).fetchone()

        return int(result[0])

    finally:

        connection.close()


# ============================================================
# HERO
# ============================================================

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-title">
            {APP_TITLE}
        </div>

        <div class="hero-subtitle">
            {APP_SUBTITLE}
        </div>

        <div class="hero-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATA
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
# TABS
# ============================================================

search_tab, management_tab = st.tabs(
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
        '<div class="section-title">'
        'Search the Library Catalogue'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'Search by title, author, publisher or keyword. '
        'Arabic and English text are supported.'
        '</div>',
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Catalogue Search",
        placeholder=(
            "Enter book title, author, "
            "publisher or keyword..."
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
                f'<div class="section-title">'
                f'{len(results)} Matching Record(s)'
                f'</div>',
                unsafe_allow_html=True,
            )

            for book in results:

                # Escape HTML only for safe display.
                # HTML tags from Excel have already
                # been removed by clean_excel_text().

                title = html.escape(
                    str(book["title"])
                )

                author = html.escape(
                    str(
                        book["author"]
                        or "—"
                    )
                )

                publisher = html.escape(
                    str(
                        book["publisher"]
                        or "—"
                    )
                )

                language = html.escape(
                    str(
                        book["language"]
                        or "—"
                    )
                )

                reason = html.escape(
                    str(book["reason"])
                )

                st.markdown(
                    f"""
                    <div class="book-card">

                        <div class="book-title">
                            {title}
                        </div>

                        <div class="book-info">
                            <span class="book-label">
                                Author:
                            </span>
                            {author}
                        </div>

                        <div class="book-info">
                            <span class="book-label">
                                Publisher:
                            </span>
                            {publisher}
                        </div>

                        <div class="book-info">
                            <span class="book-label">
                                Language:
                            </span>
                            {language}
                        </div>

                        <div class="match-badge">
                            Match: {reason}
                            ({book["score"]}%)
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:

            st.markdown(
                """
                <div class="empty-card">

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
            '<div class="section-title">'
            'Catalogue Overview'
            '</div>',
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
# MANAGEMENT TAB
# ============================================================

with management_tab:

    st.markdown(
        '<div class="section-title">'
        'Catalogue Management'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'Use this area every month to replace the '
        'old catalogue with your new Excel file.'
        '</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # CURRENT DATABASE STATUS
    # --------------------------------------------------------

    current_count = database_book_count()

    st.markdown(
        f"""
        <div class="import-card">

            <div class="import-title">
                📚 Current Catalogue
            </div>

            <div class="import-text">
                Current books stored in the database:
                <b>{current_count:,}</b>
            </div>

            <div class="import-text">
                Database file:
                <b>{DATABASE_FILE.name}</b>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # MONTHLY IMPORT
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="import-card">

            <div class="import-title">
                📊 Monthly Excel Catalogue Import
            </div>

            <div class="import-text">
                Upload your new Excel catalogue.
                Importing it will DELETE the old
                catalogue and replace it with the
                new catalogue.
            </div>

            <div class="import-text">
                Required column:
                <b>Title</b>
            </div>

            <div class="import-text">
                Optional:
                <b>Author</b>,
                <b>Publisher</b>,
                <b>Language</b>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload Excel catalogue",
        type=["xlsx", "xls"],
        help="Upload your monthly library catalogue.",
    )

    if uploaded_file:

        dataframe, error = process_excel(
            uploaded_file
        )

        if error:

            st.error(error)

        else:

            st.success(
                f"{len(dataframe):,} clean book "
                f"records detected."
            )

            st.markdown(
                "### Preview"
            )

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
                f"This will DELETE the current "
                f"{current_count:,} books and replace "
                f"them with {len(dataframe):,} books "
                f"from this Excel file."
            )

            if st.button(
                "🔄 Replace Catalogue with This Excel File",
                type="primary",
                use_container_width=True,
            ):

                try:

                    replace_database(
                        dataframe
                    )

                    st.success(
                        f"Catalogue replaced successfully. "
                        f"{len(dataframe):,} books are now "
                        f"stored in library.db."
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Database update failed: {exc}"
                    )

    # --------------------------------------------------------
    # DELETE / CLEAR DATABASE
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="danger-box">

            <div class="danger-title">
                🗑️ Clear Entire Catalogue
            </div>

            <div class="danger-text">
                This removes ALL books from
                library.db. Use this only when
                you want an empty catalogue.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    confirm_delete = st.checkbox(
        "I understand that this will remove all books.",
        key="confirm_delete_database",
    )

    if st.button(
        "🗑️ Delete All Catalogue Data",
        type="secondary",
        use_container_width=True,
    ):

        if not confirm_delete:

            st.error(
                "Please confirm the checkbox before "
                "deleting the catalogue."
            )

        else:

            try:

                clear_database()

                st.success(
                    "All catalogue data has been deleted."
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Unable to clear database: {exc}"
                )


# ============================================================
# SYSTEM INFORMATION
# ============================================================

st.markdown(
    f"""
    <div class="system-card">

        <div class="system-title">
            System Information
        </div>

        <div class="system-row">
            <span class="system-key">
                Database
            </span>

            <span class="system-value">
                {DATABASE_FILE.name}
            </span>
        </div>

        <div class="system-row">
            <span class="system-key">
                Database Location
            </span>

            <span class="system-value">
                {html.escape(str(DATABASE_FILE))}
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
