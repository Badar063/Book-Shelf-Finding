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

# Strict search settings.
# These prevent unrelated books appearing for short searches.
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
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* =====================================================
       GLOBAL
       ===================================================== */

    .stApp {
        background: #f4f7fa;
        color: #172033;
    }

    .main .block-container {
        max-width: 1250px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
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


    /* =====================================================
       HERO
       ===================================================== */

    .hero-box {
        background: linear-gradient(
            135deg,
            #103b5d 0%,
            #19597d 100%
        );

        border-radius: 20px;
        padding: 34px 38px;
        margin-bottom: 24px;

        box-shadow:
            0 10px 30px rgba(16, 59, 93, 0.15);
    }

    .hero-title {
        color: white;
        font-size: 36px;
        font-weight: 800;
        line-height: 1.2;
        margin: 0;
    }

    .hero-subtitle {
        color: #d8e7ef;
        font-size: 16px;
        margin-top: 8px;
    }

    .gold-line {
        width: 70px;
        height: 4px;
        background: #c59a42;
        border-radius: 20px;
        margin-top: 18px;
    }


    /* =====================================================
       SECTION HEADINGS
       ===================================================== */

    .section-heading {
        color: #103b5d;
        font-size: 25px;
        font-weight: 800;
        margin-top: 10px;
        margin-bottom: 4px;
    }

    .section-description {
        color: #667085;
        font-size: 14px;
        margin-bottom: 18px;
    }


    /* =====================================================
       SEARCH BOX
       ===================================================== */

    .stTextInput input {
        background: white !important;
        color: #172033 !important;

        border: 1px solid #d0d5dd !important;
        border-radius: 12px !important;

        min-height: 50px !important;

        font-size: 16px !important;
    }

    .stTextInput input:focus {
        border-color: #103b5d !important;

        box-shadow:
            0 0 0 1px #103b5d !important;
    }


    /* =====================================================
       METRIC CARDS
       ===================================================== */

    .metric-card {
        background: white;
        border: 1px solid #e4e7ec;

        border-radius: 15px;

        padding: 20px;

        min-height: 110px;

        box-shadow:
            0 3px 12px rgba(16, 24, 40, 0.05);
    }

    .metric-number {
        color: #103b5d;
        font-size: 30px;
        font-weight: 800;
    }

    .metric-label {
        color: #667085;
        font-size: 14px;
        margin-top: 3px;
    }


    /* =====================================================
       BOOK CARDS
       ===================================================== */

    .book-card {
        background: white;

        border: 1px solid #e4e7ec;
        border-left: 5px solid #c59a42;

        border-radius: 14px;

        padding: 20px;

        margin-top: 12px;
        margin-bottom: 10px;

        box-shadow:
            0 3px 12px rgba(16, 24, 40, 0.05);
    }

    .book-title {
        color: #103b5d;
        font-size: 19px;
        font-weight: 800;
        line-height: 1.4;

        margin-bottom: 12px;
    }

    .book-info {
        color: #475467;
        font-size: 14px;

        margin-top: 6px;
    }

    .book-label {
        color: #103b5d;
        font-weight: 700;
    }

    .shelf-box {
        display: inline-block;

        background: #f8f1df;
        color: #80651f;

        border: 1px solid #ead9a7;

        border-radius: 7px;

        padding: 5px 10px;

        margin-top: 12px;

        font-size: 13px;
        font-weight: 700;
    }

    .match-box {
        display: inline-block;

        background: #edf5f8;
        color: #19597d;

        border-radius: 7px;

        padding: 5px 10px;

        margin-top: 10px;

        font-size: 12px;
        font-weight: 700;
    }


    /* =====================================================
       MANAGEMENT
       ===================================================== */

    .management-card {
        background: white;

        border: 1px solid #e4e7ec;

        border-radius: 15px;

        padding: 22px;

        margin-bottom: 18px;

        box-shadow:
            0 3px 12px rgba(16, 24, 40, 0.05);
    }

    .management-title {
        color: #103b5d;
        font-size: 19px;
        font-weight: 800;
    }

    .management-description {
        color: #667085;
        font-size: 14px;
        margin-top: 5px;
    }


    /* =====================================================
       SYSTEM CARD
       ===================================================== */

    .system-card {
        background: #103b5d;

        border-radius: 15px;

        padding: 22px;

        margin-top: 28px;
    }

    .system-title {
        color: #d9b866;

        font-size: 17px;
        font-weight: 800;

        margin-bottom: 14px;
    }

    .system-row {
        display: flex;
        justify-content: space-between;

        padding: 9px 0;

        border-bottom:
            1px solid rgba(255,255,255,0.12);
    }

    .system-row:last-child {
        border-bottom: none;
    }

    .system-key {
        color: #b8c7d4;
    }

    .system-value {
        color: white;
        font-weight: 700;
    }


    /* =====================================================
       BUTTONS
       ===================================================== */

    .stButton > button {
        border-radius: 10px !important;
        min-height: 44px !important;

        font-weight: 700 !important;
    }


    /* =====================================================
       TABS
       ===================================================== */

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 46px;

        padding-left: 18px;
        padding-right: 18px;

        font-weight: 700;
    }


    /* =====================================================
       DATAFRAME
       ===================================================== */

    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
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

                language TEXT DEFAULT '',

                shelf_no TEXT DEFAULT ''
            )
            """
        )

        # Add shelf_no if an older database already exists.
        columns = connection.execute(
            "PRAGMA table_info(books)"
        ).fetchall()

        column_names = {
            row["name"]
            for row in columns
        }

        if "shelf_no" not in column_names:

            connection.execute(
                """
                ALTER TABLE books
                ADD COLUMN shelf_no TEXT DEFAULT ''
                """
            )

        connection.commit()

    finally:

        connection.close()


create_database()


# ============================================================
# LOAD BOOKS
# ============================================================

@st.cache_data(
    ttl=60,
    show_spinner=False,
)
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
                language,
                shelf_no
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
                row["shelf_no"] or "",
            )
            for row in rows
        ]

    finally:

        connection.close()


# ============================================================
# DELETE CATALOGUE
# ============================================================

def delete_all_books():

    connection = get_connection()

    try:

        connection.execute(
            "DELETE FROM books"
        )

        try:

            connection.execute(
                """
                DELETE FROM sqlite_sequence
                WHERE name='books'
                """
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


# ============================================================
# REPLACE DATABASE
# ============================================================

def replace_database(dataframe):

    connection = get_connection()

    try:

        connection.execute(
            "DELETE FROM books"
        )

        records = []

        for _, row in dataframe.iterrows():

            records.append(
                (
                    str(row["title"]).strip(),
                    str(row["author"]).strip(),
                    str(row["publisher"]).strip(),
                    str(row["language"]).strip(),
                    str(row["shelf_no"]).strip(),
                )
            )

        connection.executemany(
            """
            INSERT INTO books
            (
                title,
                author,
                publisher,
                language,
                shelf_no
            )
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

    text = str(text).strip()

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

    return " ".join(
        text.split()
    )


def tokenize(text):

    value = normalize_text(text)

    return value.split() if value else []


# ============================================================
# SEARCH ENGINE
# ============================================================

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


def phrase_contains(query, field):

    q = normalize_text(query)
    f = normalize_text(field)

    return bool(
        q and f and q in f
    )


def fuzzy_score(query, field):

    q = normalize_text(query)
    f = normalize_text(field)

    if not q or not f:

        return 0

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

    q_tokens = tokenize(q)

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title_normalized = normalize_text(title)

    if q == title_normalized:

        return "Exact Title Match", 100

    # For short queries, require the query to be a complete
    # word in the title.
    if len(q_tokens) == 1:

        if q in tokenize(title):

            return "Title Keyword Match", 97

    else:

        if exact_token_match(
            q,
            title,
        ):

            return "Title Keyword Match", 96

    # Phrase match only when query is reasonably substantial.
    if len(q) >= 4:

        if phrase_contains(
            q,
            title,
        ):

            return "Title Match", 95

    # Fuzzy title matching.
    score = fuzzy_score(
        q,
        title,
    )

    # Short searches need higher similarity.
    threshold = (
        90
        if len(q) <= 3
        else MIN_TITLE_SCORE
    )

    if score >= threshold:

        return "Strong Title Match", score


    # --------------------------------------------------------
    # AUTHOR
    # --------------------------------------------------------

    author_tokens = tokenize(author)

    if len(q_tokens) >= 2:

        if exact_token_match(
            q,
            author,
        ):

            return "Author Match", 93

    elif q in author_tokens:

        return "Author Match", 93

    author_score = fuzzy_score(
        q,
        author,
    )

    if len(q) >= 4 and author_score >= MIN_AUTHOR_SCORE:

        return "Author Match", author_score


    # --------------------------------------------------------
    # PUBLISHER
    # --------------------------------------------------------

    publisher_tokens = tokenize(
        publisher
    )

    if len(q_tokens) >= 2:

        if exact_token_match(
            q,
            publisher,
        ):

            return "Publisher Match", 90

    elif q in publisher_tokens:

        return "Publisher Match", 90

    publisher_score = fuzzy_score(
        q,
        publisher,
    )

    if (
        len(q) >= 4
        and publisher_score >= MIN_PUBLISHER_SCORE
    ):

        return "Publisher Match", publisher_score


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
            shelf_no,
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
                "title": title,
                "author": author,
                "publisher": publisher,
                "language": language,
                "shelf_no": shelf_no,
                "score": round(
                    score,
                    1,
                ),
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
# EXCEL COLUMN FINDER
# ============================================================

def find_column(columns, names):

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


# ============================================================
# PROCESS EXCEL
# ============================================================

def process_excel(uploaded_file):

    try:

        dataframe = pd.read_excel(
            uploaded_file
        )

    except Exception as exc:

        return None, (
            f"Unable to read Excel file: {exc}"
        )

    if dataframe.empty:

        return None, (
            "The Excel file is empty."
        )

    dataframe = dataframe.dropna(
        axis=1,
        how="all",
    )

    # --------------------------------------------------------
    # FIND COLUMNS
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

    shelf_column = find_column(
        dataframe.columns,
        [
            "shelf no",
            "shelf no.",
            "shelf number",
            "shelf",
            "shelfno",
            "shelf_no",
            "location",
            "rack",
            "rack no",
            "rack number",
            "رف",
            "رقم الرف",
            "رقم رف",
            "مكان الرف",
        ],
    )

    # --------------------------------------------------------
    # TITLE IS REQUIRED
    # --------------------------------------------------------

    if title_column is None:

        return None, (
            "Could not find the Title column. "
            "Please make sure your Excel file has "
            "a column called Title or Book Title."
        )

    # --------------------------------------------------------
    # CLEAN DATA
    # --------------------------------------------------------

    clean = pd.DataFrame()

    clean["title"] = (
        dataframe[title_column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    if author_column is not None:

        clean["author"] = (
            dataframe[author_column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    else:

        clean["author"] = ""

    if publisher_column is not None:

        clean["publisher"] = (
            dataframe[publisher_column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    else:

        clean["publisher"] = ""

    if language_column is not None:

        clean["language"] = (
            dataframe[language_column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    else:

        clean["language"] = ""

    if shelf_column is not None:

        clean["shelf_no"] = (
            dataframe[shelf_column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    else:

        clean["shelf_no"] = ""

    # --------------------------------------------------------
    # REMOVE EMPTY TITLES
    # --------------------------------------------------------

    clean = clean[
        clean["title"].str.strip() != ""
    ]

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    clean["_key"] = (
        clean["title"].map(normalize_text)
        + "|"
        + clean["author"].map(normalize_text)
        + "|"
        + clean["publisher"].map(normalize_text)
        + "|"
        + clean["shelf_no"].map(normalize_text)
    )

    clean = clean.drop_duplicates(
        subset=["_key"]
    )

    clean = clean.drop(
        columns=["_key"]
    )

    clean = clean.reset_index(
        drop=True
    )

    if clean.empty:

        return None, (
            "No valid book records were found."
        )

    return clean, None


# ============================================================
# LOAD CURRENT DATA
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

shelves = {
    normalize_text(row[5])
    for row in rows
    if normalize_text(row[5])
}


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero-box">
        <div class="hero-title">
            Dar Makkah International
        </div>

        <div class="hero-subtitle">
            Library Catalogue Search System
        </div>

        <div class="gold-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TABS
# ============================================================

search_tab, management_tab = st.tabs(
    [
        "🔎  Catalogue Search",
        "📥  Catalogue Management",
    ]
)


# ============================================================
# SEARCH TAB
# ============================================================

with search_tab:

    st.markdown(
        '<div class="section-heading">'
        'Search the Library Catalogue'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'Search by exact title, title keyword, author or publisher.'
        ' Arabic and English are supported.'
        '</div>',
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Catalogue Search",
        placeholder=(
            "Enter title, author or publisher..."
        ),
        label_visibility="collapsed",
    )

    # --------------------------------------------------------
    # SEARCH RESULTS
    # --------------------------------------------------------

    if query.strip():

        results = search_books(
            query,
            rows,
        )

        if results:

            st.markdown(
                f'<div class="section-heading">'
                f'{len(results)} Matching Record'
                f'{"s" if len(results) != 1 else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )

            for book in results:

                title = str(
                    book["title"]
                )

                author = (
                    book["author"]
                    or "—"
                )

                publisher = (
                    book["publisher"]
                    or "—"
                )

                language = (
                    book["language"]
                    or "—"
                )

                shelf_no = (
                    book["shelf_no"]
                    or "Not specified"
                )

                reason = str(
                    book["reason"]
                )

                score = book["score"]

                # SAFE STREAMLIT DISPLAY.
                # No user/database text is rendered as HTML.

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f'<div class="book-title">'
                        f'{title}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    c1, c2 = st.columns(2)

                    with c1:

                        st.markdown(
                            f'<div class="book-info">'
                            f'<span class="book-label">'
                            f'Author:'
                            f'</span> '
                            f'{author}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            f'<div class="book-info">'
                            f'<span class="book-label">'
                            f'Publisher:'
                            f'</span> '
                            f'{publisher}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    with c2:

                        st.markdown(
                            f'<div class="book-info">'
                            f'<span class="book-label">'
                            f'Language:'
                            f'</span> '
                            f'{language}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            f'<div class="shelf-box">'
                            f'📍 Shelf: {shelf_no}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    st.markdown(
                        f'<div class="match-box">'
                        f'{reason} · {score}%'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        else:

            st.info(
                "No matching books found. "
                "Try the full title, author name, "
                "or another keyword."
            )

    # --------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------

    else:

        st.markdown(
            '<div class="section-heading">'
            'Catalogue Overview'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-description">'
            'Current catalogue statistics.'
            '</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        metrics = [
            (
                total_books,
                "Books",
            ),
            (
                len(authors),
                "Authors",
            ),
            (
                len(publishers),
                "Publishers",
            ),
            (
                len(shelves),
                "Shelf Locations",
            ),
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

        st.write("")

        # Additional language metric.
        if languages:

            st.caption(
                f"{len(languages):,} language"
                f"{'s' if len(languages) != 1 else ''}"
                " represented in the catalogue."
            )


# ============================================================
# MANAGEMENT TAB
# ============================================================

with management_tab:

    st.markdown(
        '<div class="section-heading">'
        'Catalogue Management'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'Update the catalogue each month by uploading your '
        'latest Excel file. The new file replaces the previous '
        'catalogue.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ========================================================
    # DELETE
    # ========================================================

    st.markdown(
        """
        <div class="management-card">

            <div class="management-title">
                🗑️ Delete Current Catalogue
            </div>

            <div class="management-description">
                Remove all books currently stored in the database.
                The database itself will remain available.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    delete_confirmation = st.checkbox(
        "I understand that all current catalogue records will be deleted."
    )

    if st.button(
        "🗑️ Delete All Catalogue Data",
        disabled=not delete_confirmation,
        use_container_width=True,
    ):

        try:

            delete_all_books()

            st.success(
                "All catalogue records have been deleted."
            )

            st.rerun()

        except Exception as exc:

            st.error(
                f"Could not delete catalogue: {exc}"
            )

    st.divider()

    # ========================================================
    # EXCEL IMPORT
    # ========================================================

    st.markdown(
        """
        <div class="management-card">

            <div class="management-title">
                📊 Monthly Catalogue Import
            </div>

            <div class="management-description">
                Upload your latest Excel catalogue.
                The new catalogue will replace the current one.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "Required column: Title. "
        "Recommended columns: Author, Publisher, "
        "Language and Shelf No."
    )

    uploaded_file = st.file_uploader(
        "Upload monthly Excel catalogue",
        type=[
            "xlsx",
            "xls",
        ],
        help=(
            "The Excel file should contain a Title column. "
            "Shelf No. will be imported and shown with each book."
        ),
    )

    if uploaded_file:

        dataframe, error = process_excel(
            uploaded_file
        )

        if error:

            st.error(error)

        else:

            st.success(
                f"{len(dataframe):,} valid book records detected."
            )

            st.markdown("### Excel Preview")

            st.dataframe(
                dataframe.head(20),
                use_container_width=True,
                hide_index=True,
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                st.metric(
                    "Books",
                    f"{len(dataframe):,}",
                )

            with c2:

                author_count = (
                    dataframe["author"]
                    .replace("", pd.NA)
                    .dropna()
                    .nunique()
                )

                st.metric(
                    "Authors",
                    f"{author_count:,}",
                )

            with c3:

                publisher_count = (
                    dataframe["publisher"]
                    .replace("", pd.NA)
                    .dropna()
                    .nunique()
                )

                st.metric(
                    "Publishers",
                    f"{publisher_count:,}",
                )

            with c4:

                shelf_count = (
                    dataframe["shelf_no"]
                    .replace("", pd.NA)
                    .dropna()
                    .nunique()
                )

                st.metric(
                    "Shelf Locations",
                    f"{shelf_count:,}",
                )

            st.warning(
                f"This will replace the current "
                f"{total_books:,} books with "
                f"{len(dataframe):,} books from this Excel file."
            )

            if st.button(
                "💾 Replace Catalogue",
                type="primary",
                use_container_width=True,
            ):

                try:

                    replace_database(
                        dataframe
                    )

                    st.success(
                        "Catalogue successfully replaced."
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
    """
    <div class="system-card">

        <div class="system-title">
            System Information
        </div>

        <div class="system-row">
            <span class="system-key">
                Database
            </span>

            <span class="system-value">
                library.db
            </span>
        </div>

        <div class="system-row">
            <span class="system-key">
                Books Indexed
            </span>

            <span class="system-value">
                """
    + f"{total_books:,}"
    + """
            </span>
        </div>

        <div class="system-row">
            <span class="system-key">
                Shelf Locations
            </span>

            <span class="system-value">
                """
    + f"{len(shelves):,}"
    + """
            </span>
        </div>

        <div class="system-row">
            <span class="system-key">
                Search Engine
            </span>

            <span class="system-value">
                Exact + Keyword + Strict Fuzzy
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
