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
# PAGE
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
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
# DELETE DATABASE CONTENT
# ============================================================

def delete_all_books():

    connection = get_connection()

    try:
        connection.execute("DELETE FROM books")

        # Reset SQLite AUTOINCREMENT counter
        connection.execute(
            "DELETE FROM sqlite_sequence WHERE name='books'"
        )

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

        # Remove old catalogue
        connection.execute("DELETE FROM books")

        records = []

        for _, row in dataframe.iterrows():

            records.append(
                (
                    str(row["title"]).strip(),
                    str(row["author"]).strip(),
                    str(row["publisher"]).strip(),
                    str(row["language"]).strip(),
                )
            )

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

    return bool(
        query and field and query in field
    )


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


def field_match(
    query,
    title,
    author,
    publisher,
):

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
            priority.get(
                item["reason"],
                99,
            ),
            -item["score"],
            normalize_text(item["title"]),
        )
    )

    return results[:MAX_RESULTS]


# ============================================================
# EXCEL
# ============================================================

def find_column(columns, names):

    normalized_columns = {
        normalize_text(column): column
        for column in columns
    }

    for name in names:

        normalized_name = normalize_text(name)

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

        return None, (
            f"Unable to read Excel file: {exc}"
        )

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

        return None, (
            "Could not find a Title column. "
            "Please name it 'Title' or 'Book Title'."
        )

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

    # Remove empty titles
    clean = clean[
        clean["title"].str.strip() != ""
    ]

    # Remove duplicates
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

st.title(APP_TITLE)

st.caption(APP_SUBTITLE)

st.divider()


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
# SEARCH
# ============================================================

with search_tab:

    st.header("Search the Library Catalogue")

    st.write(
        "Search by title, author, publisher or keyword. "
        "Arabic and English text are supported."
    )

    query = st.text_input(
        "Catalogue Search",
        placeholder=(
            "Enter book title, author, "
            "publisher or keyword..."
        ),
    )

    if query.strip():

        results = search_books(
            query,
            rows,
        )

        if results:

            st.subheader(
                f"{len(results)} Matching Record(s)"
            )

            for book in results:

                # IMPORTANT:
                # No HTML is used here.
                # Streamlit displays the text safely.

                with st.container(
                    border=True
                ):

                    st.subheader(
                        str(book["title"])
                    )

                    st.write(
                        f"**Author:** "
                        f"{book['author'] or '—'}"
                    )

                    st.write(
                        f"**Publisher:** "
                        f"{book['publisher'] or '—'}"
                    )

                    st.write(
                        f"**Language:** "
                        f"{book['language'] or '—'}"
                    )

                    st.caption(
                        f"Match: "
                        f"{book['reason']} "
                        f"({book['score']}%)"
                    )

        else:

            st.info(
                "No matching books found. "
                "Try another title, author, "
                "publisher or keyword."
            )

    else:

        st.subheader("Catalogue Overview")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "Books",
                f"{total_books:,}",
            )

        with c2:
            st.metric(
                "Authors",
                f"{len(authors):,}",
            )

        with c3:
            st.metric(
                "Publishers",
                f"{len(publishers):,}",
            )

        with c4:
            st.metric(
                "Languages",
                f"{len(languages):,}",
            )


# ============================================================
# MANAGEMENT
# ============================================================

with management_tab:

    st.header("Catalogue Management")

    st.write(
        "Upload your monthly Excel catalogue. "
        "Importing a new catalogue automatically "
        "replaces the previous catalogue."
    )

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    st.subheader("🗑️ Delete Current Catalogue")

    st.warning(
        "This permanently removes all books currently "
        "stored in library.db."
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
                "All catalogue data has been deleted."
            )

            st.rerun()

        except Exception as exc:

            st.error(
                f"Could not delete catalogue: {exc}"
            )

    st.divider()

    # --------------------------------------------------------
    # EXCEL
    # --------------------------------------------------------

    st.subheader(
        "📊 Upload Monthly Excel Catalogue"
    )

    st.write(
        "Required column: **Title**. "
        "Optional columns: **Author**, "
        "**Publisher**, **Language**."
    )

    uploaded_file = st.file_uploader(
        "Upload Excel catalogue",
        type=[
            "xlsx",
            "xls",
        ],
    )

    if uploaded_file:

        dataframe, error = process_excel(
            uploaded_file
        )

        if error:

            st.error(error)

        else:

            st.success(
                f"{len(dataframe):,} "
                "valid book records detected."
            )

            st.subheader("Preview")

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

            st.warning(
                "This will replace the existing "
                f"{total_books:,} books with the "
                f"{len(dataframe):,} books in this Excel file."
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

st.divider()

st.subheader("System Information")

info1, info2, info3, info4 = st.columns(4)

with info1:
    st.write("**Database**")
    st.write(DATABASE_FILE.name)

with info2:
    st.write("**Database Location**")
    st.code(str(DATABASE_FILE))

with info3:
    st.write("**Books Indexed**")
    st.write(f"{total_books:,}")

with info4:
    st.write("**Search Engine**")
    st.write("Exact + Token + Fuzzy")
