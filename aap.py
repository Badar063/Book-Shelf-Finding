import re
import sqlite3
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

DATABASE_FILE = Path(__file__).resolve().parent / "library.db"

MAX_RESULTS = 100

MIN_TITLE_SCORE = 72
MIN_AUTHOR_SCORE = 78
MIN_PUBLISHER_SCORE = 82


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# DESIGN / CSS
# ============================================================

st.markdown(
    """
<style>

/* ==========================================================
   GLOBAL
   ========================================================== */

.stApp {
    background: #f4f6f8;
    color: #172033;
}

.main .block-container {
    max-width: 1280px;
    padding-top: 1.5rem;
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


/* ==========================================================
   HERO
   ========================================================== */

.hero {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(
            circle at 90% 10%,
            rgba(196,154,66,0.18),
            transparent 28%
        ),
        linear-gradient(
            135deg,
            #0d304c 0%,
            #123b5d 50%,
            #1c587c 100%
        );

    border-radius: 22px;
    padding: 38px 42px;
    margin-bottom: 26px;

    box-shadow:
        0 12px 35px rgba(18,59,93,0.16);
}

.hero-title {
    color: white;
    font-size: 36px;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.5px;
}

.hero-subtitle {
    color: #dce9f2;
    font-size: 16px;
    margin-top: 9px;
}

.hero-line {
    width: 70px;
    height: 4px;
    background: #d0aa5b;
    border-radius: 20px;
    margin-top: 20px;
}


/* ==========================================================
   SECTION HEADINGS
   ========================================================== */

.section-title {
    color: #123b5d;
    font-size: 25px;
    font-weight: 800;
    margin-top: 10px;
    margin-bottom: 5px;
}

.section-description {
    color: #667085;
    font-size: 14px;
    margin-bottom: 18px;
}


/* ==========================================================
   TABS
   ========================================================== */

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: transparent;
}

.stTabs [data-baseweb="tab"] {
    height: 48px;
    padding: 0 20px;
    border-radius: 10px 10px 0 0;
    font-weight: 700;
    color: #667085;
}

.stTabs [aria-selected="true"] {
    color: #123b5d !important;
}


/* ==========================================================
   SEARCH BOX
   ========================================================== */

.search-wrapper {
    background: white;
    border: 1px solid #e4e7ec;
    border-radius: 16px;
    padding: 18px 20px 8px 20px;
    margin-bottom: 24px;

    box-shadow:
        0 5px 18px rgba(16,24,40,0.05);
}

.stTextInput input {
    background: #ffffff !important;
    color: #172033 !important;

    border: 1px solid #d0d5dd !important;
    border-radius: 11px !important;

    min-height: 50px !important;

    font-size: 16px !important;
}

.stTextInput input::placeholder {
    color: #98a2b3 !important;
}

.stTextInput input:focus {
    border-color: #123b5d !important;
    box-shadow: 0 0 0 1px #123b5d !important;
}


/* ==========================================================
   METRIC CARDS
   ========================================================== */

.metric-card {
    background: #ffffff;
    border: 1px solid #e4e7ec;
    border-radius: 16px;

    padding: 20px 22px;

    min-height: 112px;

    box-shadow:
        0 5px 18px rgba(16,24,40,0.05);

    transition:
        transform 0.15s ease,
        box-shadow 0.15s ease;
}

.metric-card:hover {
    transform: translateY(-2px);

    box-shadow:
        0 9px 24px rgba(16,24,40,0.08);
}

.metric-icon {
    font-size: 21px;
    margin-bottom: 6px;
}

.metric-number {
    color: #123b5d;
    font-size: 29px;
    font-weight: 800;
    line-height: 1;
}

.metric-label {
    color: #667085;
    font-size: 13px;
    font-weight: 600;
    margin-top: 7px;
}


/* ==========================================================
   RESULT HEADER
   ========================================================== */

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    margin-top: 25px;
    margin-bottom: 12px;
}

.result-title {
    color: #123b5d;
    font-size: 21px;
    font-weight: 800;
}

.result-count {
    background: #eaf2f7;
    color: #123b5d;

    border-radius: 20px;

    padding: 6px 12px;

    font-size: 13px;
    font-weight: 750;
}


/* ==========================================================
   BOOK CARD
   ========================================================== */

.book-card {
    background: #ffffff;

    border: 1px solid #e4e7ec;
    border-left: 5px solid #c49a42;

    border-radius: 15px;

    padding: 20px 22px;

    margin-bottom: 12px;

    box-shadow:
        0 4px 15px rgba(16,24,40,0.045);
}

.book-title {
    color: #123b5d;

    font-size: 19px;
    font-weight: 800;

    line-height: 1.4;

    margin-bottom: 13px;
}

.book-info {
    color: #475467;

    font-size: 14px;

    margin: 6px 0;
}

.book-label {
    color: #123b5d;
    font-weight: 750;
}

.book-bottom {
    display: flex;
    align-items: center;
    flex-wrap: wrap;

    gap: 8px;

    margin-top: 14px;
}

.shelf-badge {
    display: inline-block;

    background: #fff8e8;
    color: #805f19;

    border: 1px solid #ead49b;

    border-radius: 7px;

    padding: 6px 10px;

    font-size: 13px;
    font-weight: 750;
}

.match-badge {
    display: inline-block;

    background: #eaf2f7;
    color: #123b5d;

    border: 1px solid #d5e4ed;

    border-radius: 7px;

    padding: 6px 10px;

    font-size: 13px;
    font-weight: 700;
}


/* ==========================================================
   EMPTY STATE
   ========================================================== */

.empty-card {
    background: white;

    border: 1px solid #e4e7ec;

    border-radius: 16px;

    padding: 45px 30px;

    text-align: center;

    margin-top: 20px;

    box-shadow:
        0 5px 18px rgba(16,24,40,0.04);
}

.empty-icon {
    font-size: 38px;
}

.empty-title {
    color: #123b5d;

    font-size: 20px;
    font-weight: 800;

    margin-top: 9px;
}

.empty-text {
    color: #667085;

    font-size: 14px;

    margin-top: 7px;
}


/* ==========================================================
   MANAGEMENT CARDS
   ========================================================== */

.management-card {
    background: #ffffff;

    border: 1px solid #e4e7ec;

    border-radius: 16px;

    padding: 24px;

    margin-bottom: 20px;

    box-shadow:
        0 5px 18px rgba(16,24,40,0.045);
}

.management-title {
    color: #123b5d;

    font-size: 20px;
    font-weight: 800;
}

.management-description {
    color: #667085;

    font-size: 14px;

    margin-top: 5px;
    margin-bottom: 17px;
}


/* ==========================================================
   DANGER CARD
   ========================================================== */

.danger-card {
    background: #fff8f7;

    border: 1px solid #f3c8c3;
    border-left: 5px solid #c0392b;

    border-radius: 15px;

    padding: 22px;

    margin-top: 25px;
    margin-bottom: 22px;
}

.danger-title {
    color: #a93226;

    font-size: 19px;
    font-weight: 800;
}

.danger-text {
    color: #7a271a;

    font-size: 14px;

    margin-top: 6px;
    margin-bottom: 15px;
}


/* ==========================================================
   SYSTEM INFORMATION
   ========================================================== */

.system-card {
    background:
        linear-gradient(
            135deg,
            #0d304c,
            #123b5d
        );

    border-radius: 17px;

    padding: 23px 25px;

    margin-top: 30px;

    box-shadow:
        0 8px 25px rgba(18,59,93,0.12);
}

.system-title {
    color: #d9b866;

    font-size: 18px;
    font-weight: 800;

    margin-bottom: 14px;
}

.system-row {
    display: flex;
    justify-content: space-between;

    gap: 20px;

    padding: 10px 0;

    border-bottom:
        1px solid rgba(255,255,255,0.10);
}

.system-row:last-child {
    border-bottom: none;
}

.system-key {
    color: #aebfcd;

    font-size: 13px;
}

.system-value {
    color: white;

    font-size: 13px;
    font-weight: 700;

    text-align: right;
}


/* ==========================================================
   DATAFRAME
   ========================================================== */

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}


/* ==========================================================
   BUTTONS
   ========================================================== */

.stButton > button {
    border-radius: 10px;

    min-height: 44px;

    font-weight: 750;

    border: 1px solid #d0d5dd;
}

.stButton > button[kind="primary"] {
    background: #123b5d;
    border-color: #123b5d;
}

.stButton > button[kind="primary"]:hover {
    background: #0d304c;
    border-color: #0d304c;
}


/* ==========================================================
   FILE UPLOADER
   ========================================================== */

[data-testid="stFileUploader"] {
    background: #f8fafc;

    border: 1px dashed #b9c7d3;

    border-radius: 12px;

    padding: 8px;
}


/* ==========================================================
   ALERTS
   ========================================================== */

.stAlert {
    border-radius: 10px;
}


/* ==========================================================
   CHECKBOX
   ========================================================== */

.stCheckbox label {
    color: #475467 !important;
    font-size: 14px !important;
}


/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 768px) {

    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero {
        padding: 28px 24px;
        border-radius: 17px;
    }

    .hero-title {
        font-size: 28px;
    }

    .hero-subtitle {
        font-size: 14px;
    }

    .book-card {
        padding: 17px;
    }

    .system-row {
        flex-direction: column;
        gap: 3px;
    }

    .system-value {
        text-align: left;
    }

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

        # ----------------------------------------------------
        # Upgrade old database automatically
        # ----------------------------------------------------

        columns = [
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(books)"
            ).fetchall()
        ]

        if "shelf_no" not in columns:

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
# DELETE ALL DATA
# ============================================================

def delete_all_books():

    connection = get_connection()

    try:

        connection.execute(
            "DELETE FROM books"
        )

        try:

            connection.execute(
                "DELETE FROM sqlite_sequence "
                "WHERE name='books'"
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

    return " ".join(text.split())


def tokenize(text):

    value = normalize_text(text)

    return value.split() if value else []


# ============================================================
# SHELF NUMBER FORMAT
# ============================================================

def format_shelf_no(value):

    if value is None:
        return "—"

    value = str(value).strip()

    if not value:
        return "—"

    # q2 35
    # q2-35
    # q2_35
    # Q2 35
    #
    # All become:
    # Q2 35

    value = re.sub(
        r"^\s*q\s*([0-9]+)\s*[-_ ]+\s*([0-9]+)\s*$",
        r"Q\1 \2",
        value,
        flags=re.IGNORECASE,
    )

    # q2 35 without separator
    value = re.sub(
        r"^\s*q\s*([0-9]+)\s+([0-9]+)\s*$",
        r"Q\1 \2",
        value,
        flags=re.IGNORECASE,
    )

    return value


# ============================================================
# SEARCH HELPERS
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


# ============================================================
# SEARCH MATCHING
# ============================================================

def field_match(
    query,
    title,
    author,
    publisher,
):

    q = normalize_text(query)

    if not q:
        return None, 0

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    normalized_title = normalize_text(title)

    if q == normalized_title:

        return (
            "Exact Title Match",
            100,
        )

    if phrase_contains(q, title):

        return (
            "Title Match",
            98,
        )

    if exact_token_match(q, title):

        return (
            "Title Keyword Match",
            96,
        )

    title_score = fuzzy_score(
        q,
        title,
    )

    if title_score >= MIN_TITLE_SCORE:

        return (
            "Strong Title Match",
            title_score,
        )

    # --------------------------------------------------------
    # AUTHOR
    # --------------------------------------------------------

    if phrase_contains(q, author):

        return (
            "Author Match",
            94,
        )

    if exact_token_match(q, author):

        return (
            "Author Keyword Match",
            92,
        )

    author_score = fuzzy_score(
        q,
        author,
    )

    if author_score >= MIN_AUTHOR_SCORE:

        return (
            "Author Match",
            author_score * 0.96,
        )

    # --------------------------------------------------------
    # PUBLISHER
    # --------------------------------------------------------

    if phrase_contains(q, publisher):

        return (
            "Publisher Match",
            91,
        )

    if exact_token_match(q, publisher):

        return (
            "Publisher Keyword Match",
            89,
        )

    publisher_score = fuzzy_score(
        q,
        publisher,
    )

    if publisher_score >= MIN_PUBLISHER_SCORE:

        return (
            "Publisher Match",
            publisher_score * 0.94,
        )

    return None, 0


# ============================================================
# SEARCH BOOKS
# ============================================================

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
    # TITLE
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

    # --------------------------------------------------------
    # AUTHOR
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # PUBLISHER
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    language_column = find_column(
        dataframe.columns,
        [
            "language",
            "lang",
            "اللغة",
        ],
    )

    # --------------------------------------------------------
    # SHELF NUMBER
    # --------------------------------------------------------

    shelf_column = find_column(
        dataframe.columns,
        [
            "shelf",
            "shelf no",
            "shelf number",
            "shelf_no",
            "shelfno",
            "location",
            "call number",
            "call no",
            "shelf location",
            "رف",
            "رقم الرف",
            "رقم الرفوف",
            "مكان الرف",
        ],
    )

    if title_column is None:

        return None, (
            "Could not find a Title column. "
            "Please name it 'Title' or "
            "'Book Title'."
        )

    # --------------------------------------------------------
    # CLEAN DATAFRAME
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
            .map(format_shelf_no)
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
# HERO
# ============================================================

st.markdown(
    f"""
    <div class="hero">

        <div class="hero-title">
            📚 {APP_TITLE}
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
        """
        <div class="section-title">
            Search the Library Catalogue
        </div>

        <div class="section-description">
            Search by book title, author or publisher.
            Arabic and English text are supported.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # SEARCH BOX
    # --------------------------------------------------------

    st.markdown(
        '<div class="search-wrapper">',
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Catalogue Search",
        placeholder=(
            "🔎  Enter title, author or publisher..."
        ),
        label_visibility="collapsed",
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    if query.strip():

        results = search_books(
            query,
            rows,
        )

        if results:

            st.markdown(
                f"""
                <div class="result-header">

                    <div class="result-title">
                        Search Results
                    </div>

                    <div class="result-count">
                        {len(results)} result(s)
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            for book in results:

                title = str(
                    book["title"] or "Untitled"
                )

                author = str(
                    book["author"] or "—"
                )

                publisher = str(
                    book["publisher"] or "—"
                )

                language = str(
                    book["language"] or "—"
                )

                shelf = format_shelf_no(
                    book["shelf_no"]
                )

                reason = str(
                    book["reason"]
                )

                score = book["score"]

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

                        <div class="book-bottom">

                            <span class="shelf-badge">
                                📍 Shelf {shelf}
                            </span>

                            <span class="match-badge">
                                {reason} · {score}%
                            </span>

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
                        Try another title, author
                        or publisher.
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # OVERVIEW
    # --------------------------------------------------------

    else:

        st.markdown(
            """
            <div class="section-title">
                Catalogue Overview
            </div>

            <div class="section-description">
                Current catalogue statistics.
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        metrics = [
            (
                c1,
                "📚",
                f"{total_books:,}",
                "Books",
            ),
            (
                c2,
                "✍️",
                f"{len(authors):,}",
                "Authors",
            ),
            (
                c3,
                "🏢",
                f"{len(publishers):,}",
                "Publishers",
            ),
            (
                c4,
                "🌐",
                f"{len(languages):,}",
                "Languages",
            ),
        ]

        for (
            column,
            icon,
            number,
            label,
        ) in metrics:

            with column:

                st.markdown(
                    f"""
                    <div class="metric-card">

                        <div class="metric-icon">
                            {icon}
                        </div>

                        <div class="metric-number">
                            {number}
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
        """
        <div class="section-title">
            Catalogue Management
        </div>

        <div class="section-description">
            Manage your monthly Excel catalogue.
            Importing a new file replaces the
            previous catalogue.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # IMPORT
    # ========================================================

    st.markdown(
        """
        <div class="management-card">

            <div class="management-title">
                📊 Monthly Catalogue Import
            </div>

            <div class="management-description">
                Upload your latest Excel catalogue.
                The existing catalogue will be replaced
                when you confirm the import.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "Required column: Title  •  "
        "Optional: Author, Publisher, Language, "
        "Shelf No."
    )

    uploaded_file = st.file_uploader(
        "Upload Excel catalogue",
        type=[
            "xlsx",
            "xls",
        ],
        help="Upload the latest monthly catalogue.",
    )

    if uploaded_file:

        dataframe, error = process_excel(
            uploaded_file
        )

        if error:

            st.error(error)

        else:

            st.success(
                f"{len(dataframe):,} valid "
                "book records detected."
            )

            # ------------------------------------------------
            # PREVIEW
            # ------------------------------------------------

            st.markdown(
                """
                <div class="section-title">
                    Catalogue Preview
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.dataframe(
                dataframe.head(20),
                use_container_width=True,
                hide_index=True,
            )

            # ------------------------------------------------
            # IMPORT METRICS
            # ------------------------------------------------

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
                f"{len(dataframe):,} books."
            )

            if st.button(
                "💾  Replace Catalogue",
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

    # ========================================================
    # DELETE
    # ========================================================

    st.markdown(
        """
        <div class="danger-card">

            <div class="danger-title">
                🗑️ Delete Current Catalogue
            </div>

            <div class="danger-text">
                This permanently removes all books
                currently stored in library.db.
                The database itself remains available
                for the next Excel import.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    delete_confirmation = st.checkbox(
        "I understand that all current catalogue records will be deleted."
    )

    if st.button(
        "🗑️  Delete All Catalogue Data",
        disabled=not delete_confirmation,
        use_container_width=True,
    ):

        try:

            delete_all_books()

            st.success(
                "All catalogue data has been deleted."
            )

            st.rerun()

        except Exception as exc:

            st.error(
                f"Could not delete catalogue: {exc}"
            )


# ============================================================
# SYSTEM INFORMATION
# ============================================================

st.markdown(
    f"""
    <div class="system-card">

        <div class="system-title">
            ⚙️ System Information
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

        <div class="system-row">

            <span class="system-key">
                Database Location
            </span>

            <span class="system-value">
                {str(DATABASE_FILE)}
            </span>

        </div>

    </div>
    """,
    unsafe_allow_html=True,
)
