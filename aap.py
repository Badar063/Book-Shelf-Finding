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

# Always use the same folder as app.py
DATABASE_FILE = Path(__file__).resolve().parent / "library.db"

MAX_RESULTS = 100

# Much stricter search settings
MIN_TITLE_SCORE = 82
MIN_AUTHOR_SCORE = 88
MIN_PUBLISHER_SCORE = 92


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

        # IMPORTANT:
        # Shelf No. has been added.
        #
        # If an old database already exists without shelf_no,
        # we automatically add the column.

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

        # Check existing columns
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
# DELETE ALL CATALOGUE DATA
# ============================================================

def delete_all_books():

    connection = get_connection()

    try:

        connection.execute(
            "DELETE FROM books"
        )

        # Reset ID counter
        try:

            connection.execute(
                """
                DELETE FROM sqlite_sequence
                WHERE name = 'books'
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

        # ----------------------------------------------------
        # DELETE OLD CATALOGUE
        # ----------------------------------------------------

        connection.execute(
            "DELETE FROM books"
        )

        # ----------------------------------------------------
        # RESET ID
        # ----------------------------------------------------

        try:

            connection.execute(
                """
                DELETE FROM sqlite_sequence
                WHERE name = 'books'
                """
            )

        except sqlite3.OperationalError:
            pass

        # ----------------------------------------------------
        # INSERT NEW CATALOGUE
        # ----------------------------------------------------

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

    return (
        value.split()
        if value
        else []
    )


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

    # For very short searches we do NOT use
    # partial_ratio because it creates too many
    # irrelevant matches.
    if len(q) < 4:
        return fuzz.ratio(q, f)

    return max(
        fuzz.ratio(q, f),
        fuzz.token_set_ratio(q, f),
        fuzz.WRatio(q, f),
    )


# ============================================================
# STRICT SEARCH
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

    title_n = normalize_text(title)
    author_n = normalize_text(author)
    publisher_n = normalize_text(publisher)

    query_tokens = tokenize(q)

    # ========================================================
    # 1. EXACT TITLE
    # ========================================================

    if q == title_n:

        return (
            "Exact Title Match",
            100,
        )

    # ========================================================
    # 2. TITLE PHRASE
    # ========================================================

    if phrase_contains(q, title_n):

        return (
            "Title Match",
            98,
        )

    # ========================================================
    # 3. TITLE WORD MATCH
    #
    # All query words must appear in title.
    # ========================================================

    if query_tokens:

        title_tokens = set(
            tokenize(title_n)
        )

        if all(
            token in title_tokens
            for token in query_tokens
        ):

            return (
                "Title Keyword Match",
                96,
            )

    # ========================================================
    # 4. FUZZY TITLE
    #
    # Only allow fuzzy title matches for queries
    # of 4+ characters.
    # ========================================================

    if len(q) >= 4:

        score = fuzz.WRatio(
            q,
            title_n,
        )

        # Long queries need stronger matching.
        if len(q) >= 8:

            threshold = 85

        else:

            threshold = MIN_TITLE_SCORE

        if score >= threshold:

            return (
                "Strong Title Match",
                score,
            )

    # ========================================================
    # 5. EXACT AUTHOR PHRASE
    # ========================================================

    if author_n:

        if q == author_n:

            return (
                "Exact Author Match",
                100,
            )

        if phrase_contains(
            q,
            author_n,
        ):

            return (
                "Author Match",
                94,
            )

        author_tokens = set(
            tokenize(author_n)
        )

        if query_tokens and all(
            token in author_tokens
            for token in query_tokens
        ):

            return (
                "Author Keyword Match",
                92,
            )

    # ========================================================
    # 6. FUZZY AUTHOR
    # ========================================================

    if author_n and len(q) >= 5:

        score = fuzz.WRatio(
            q,
            author_n,
        )

        if score >= MIN_AUTHOR_SCORE:

            return (
                "Author Match",
                score,
            )

    # ========================================================
    # 7. PUBLISHER
    #
    # Publisher fuzzy matching is intentionally strict.
    # ========================================================

    if publisher_n:

        if q == publisher_n:

            return (
                "Exact Publisher Match",
                100,
            )

        if phrase_contains(
            q,
            publisher_n,
        ):

            return (
                "Publisher Match",
                91,
            )

        publisher_tokens = set(
            tokenize(publisher_n)
        )

        if query_tokens and all(
            token in publisher_tokens
            for token in query_tokens
        ):

            return (
                "Publisher Keyword Match",
                89,
            )

    # ========================================================
    # 8. FUZZY PUBLISHER
    # ========================================================

    if publisher_n and len(q) >= 6:

        score = fuzz.WRatio(
            q,
            publisher_n,
        )

        if score >= MIN_PUBLISHER_SCORE:

            return (
                "Publisher Match",
                score,
            )

    return None, 0


# ============================================================
# SEARCH BOOKS
# ============================================================

def search_books(query, rows):

    query_normalized = normalize_text(
        query
    )

    if not query_normalized:

        return []

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
            query_normalized,
            title,
            author,
            publisher,
        )

        if reason is None:

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

    # Best matches first
    priority = {

        "Exact Title Match": 0,

        "Title Match": 1,

        "Title Keyword Match": 2,

        "Strong Title Match": 3,

        "Exact Author Match": 4,

        "Author Match": 5,

        "Author Keyword Match": 6,

        "Exact Publisher Match": 7,

        "Publisher Match": 8,

        "Publisher Keyword Match": 9,
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

    return results[
        :MAX_RESULTS
    ]


# ============================================================
# EXCEL COLUMN FINDER
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

        if (
            normalized_name
            in normalized_columns
        ):

            return normalized_columns[
                normalized_name
            ]

    return None


# ============================================================
# PROCESS EXCEL
# ============================================================

def process_excel(
    uploaded_file,
):

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

        return (
            None,
            "The Excel file is empty.",
        )

    dataframe = dataframe.dropna(
        axis=1,
        how="all",
    )

    # ========================================================
    # TITLE
    # ========================================================

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

    # ========================================================
    # AUTHOR
    # ========================================================

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

    # ========================================================
    # PUBLISHER
    # ========================================================

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

    # ========================================================
    # LANGUAGE
    # ========================================================

    language_column = find_column(
        dataframe.columns,
        [
            "language",
            "lang",
            "اللغة",
        ],
    )

    # ========================================================
    # SHELF NUMBER
    # ========================================================

    shelf_column = find_column(
        dataframe.columns,
        [
            "shelf no",
            "shelf no.",
            "shelf number",
            "shelf",
            "shelf_no",
            "shelfno",
            "location",
            "call number",
            "call no",
            "call no.",
            "رف",
            "رقم الرف",
            "رقم الرفوف",
            "موقع الرف",
        ],
    )

    if title_column is None:

        return (
            None,
            "Could not find a Title column. "
            "Please make sure your Excel file has "
            "a column named Title or Book Title.",
        )

    if shelf_column is None:

        return (
            None,
            "Could not find the Shelf No. column. "
            "Please name it 'Shelf No', "
            "'Shelf No.', 'Shelf Number', "
            "'Shelf' or 'رقم الرف'.",
        )

    # ========================================================
    # CLEAN DATA
    # ========================================================

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

    # ========================================================
    # SHELF NUMBER
    # ========================================================

    clean["shelf_no"] = (
        dataframe[shelf_column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # ========================================================
    # REMOVE EMPTY TITLES
    # ========================================================

    clean = clean[
        clean["title"].str.strip() != ""
    ]

    # ========================================================
    # REMOVE DUPLICATES
    #
    # Include shelf number because two physical copies
    # can legitimately have different shelf locations.
    # ========================================================

    clean["_key"] = (
        clean["title"].map(normalize_text)
        + "|"
        + clean["author"].map(normalize_text)
        + "|"
        + clean["publisher"].map(normalize_text)
        + "|"
        + clean["language"].map(normalize_text)
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

        return (
            None,
            "No valid book records were found.",
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

shelves = {
    normalize_text(row[5])
    for row in rows
    if normalize_text(row[5])
}


# ============================================================
# HEADER
# ============================================================

st.title(APP_TITLE)

st.caption(
    APP_SUBTITLE
)

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
# SEARCH TAB
# ============================================================

with search_tab:

    st.header(
        "Search the Library Catalogue"
    )

    st.write(
        "Search by book title, author or publisher. "
        "Arabic and English text are supported."
    )

    query = st.text_input(
        "Catalogue Search",
        placeholder=(
            "Enter book title, author or publisher..."
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

                with st.container(
                    border=True
                ):

                    # -------------------------------
                    # TITLE
                    # -------------------------------

                    st.subheader(
                        str(book["title"])
                    )

                    # -------------------------------
                    # SHELF NUMBER
                    # -------------------------------

                    shelf_value = (
                        book["shelf_no"]
                        or "Not specified"
                    )

                    st.write(
                        f"📍 **Shelf No.:** "
                        f"{shelf_value}"
                    )

                    # -------------------------------
                    # AUTHOR
                    # -------------------------------

                    st.write(
                        f"**Author:** "
                        f"{book['author'] or '—'}"
                    )

                    # -------------------------------
                    # PUBLISHER
                    # -------------------------------

                    st.write(
                        f"**Publisher:** "
                        f"{book['publisher'] or '—'}"
                    )

                    # -------------------------------
                    # LANGUAGE
                    # -------------------------------

                    st.write(
                        f"**Language:** "
                        f"{book['language'] or '—'}"
                    )

                    # -------------------------------
                    # MATCH
                    # -------------------------------

                    st.caption(
                        f"Match: "
                        f"{book['reason']} "
                        f"({book['score']}%)"
                    )

        else:

            st.info(
                "No matching books found. "
                "Try the complete book title, "
                "author name or publisher."
            )

    else:

        st.subheader(
            "Catalogue Overview"
        )

        c1, c2, c3, c4, c5 = st.columns(5)

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

        with c5:

            st.metric(
                "Shelf Locations",
                f"{len(shelves):,}",
            )


# ============================================================
# MANAGEMENT TAB
# ============================================================

with management_tab:

    st.header(
        "Catalogue Management"
    )

    st.write(
        "Upload your monthly Excel catalogue. "
        "The new Excel file completely replaces "
        "the existing catalogue."
    )

    # ========================================================
    # DELETE
    # ========================================================

    st.subheader(
        "🗑️ Delete Current Catalogue"
    )

    st.warning(
        "This will permanently remove every book "
        "currently stored in library.db. "
        "The database itself will remain available "
        "so you can import a new catalogue."
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
                "All catalogue data has been deleted. "
                "The database is now empty."
            )

            st.rerun()

        except Exception as exc:

            st.error(
                f"Could not delete catalogue: {exc}"
            )

    st.divider()

    # ========================================================
    # EXCEL UPLOAD
    # ========================================================

    st.subheader(
        "📊 Upload Monthly Excel Catalogue"
    )

    st.write(
        "Required columns:"
    )

    st.info(
        "Title + Shelf No."
    )

    st.write(
        "Optional columns: "
        "Author, Publisher and Language."
    )

    uploaded_file = st.file_uploader(
        "Upload Excel catalogue",
        type=[
            "xlsx",
            "xls",
        ],
        help=(
            "Upload the monthly library catalogue."
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
                f"{len(dataframe):,} "
                "valid book records detected."
            )

            # ------------------------------------------------
            # DETECTED COLUMNS
            # ------------------------------------------------

            st.subheader(
                "Imported Catalogue"
            )

            st.dataframe(
                dataframe.head(20),
                use_container_width=True,
                hide_index=True,
            )

            # ------------------------------------------------
            # METRICS
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

            # ------------------------------------------------
            # REPLACE WARNING
            # ------------------------------------------------

            st.warning(
                f"This will replace the existing "
                f"{total_books:,} books with the "
                f"{len(dataframe):,} books from this "
                "Excel file."
            )

            # ------------------------------------------------
            # IMPORT
            # ------------------------------------------------

            if st.button(
                "💾 Replace Catalogue With This Excel File",
                type="primary",
                use_container_width=True,
            ):

                try:

                    replace_database(
                        dataframe
                    )

                    st.success(
                        "Catalogue successfully replaced. "
                        "The old catalogue has been removed "
                        "and the new Excel catalogue is now active."
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

st.subheader(
    "System Information"
)

info1, info2, info3, info4 = st.columns(4)

with info1:

    st.write(
        "**Database**"
    )

    st.write(
        DATABASE_FILE.name
    )


with info2:

    st.write(
        "**Database Location**"
    )

    st.code(
        str(DATABASE_FILE)
    )


with info3:

    st.write(
        "**Books Indexed**"
    )

    st.write(
        f"{total_books:,}"
    )


with info4:

    st.write(
        "**Search Engine**"
    )

    st.write(
        "Exact + Strict Fuzzy"
    )
