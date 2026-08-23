import html
import re
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF
import streamlit as st
from rapidfuzz import fuzz


# ============================================================
# CONFIG
# ============================================================

APP_TITLE = "Dar Makkah International"
APP_SUBTITLE = "Library Catalogue Management System"

DATABASE_FILE = Path("library.db")

MAX_RESULTS = 50


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

st.html(
    """
    <style>

    :root {
        --navy: #173B57;
        --navy-dark: #102A43;
        --teal: #167D8D;
        --teal-light: #E8F6F7;
        --gold: #B58A24;
        --bg: #F5F7FA;
        --card: #FFFFFF;
        --border: #E2E8F0;
        --text: #172033;
        --muted: #667085;
        --success: #238636;
        --danger: #C62828;
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
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

    /* HEADER */

    .library-header {
        background: linear-gradient(
            135deg,
            #173B57 0%,
            #214D6B 100%
        );

        padding: 2rem 2rem 1.8rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.8rem;

        box-shadow:
            0 8px 25px rgba(23, 59, 87, 0.15);
    }

    .main-heading {
        color: white;
        font-size: 2.35rem;
        font-weight: 800;
        letter-spacing: .3px;
        margin: 0;
    }

    .sub-heading {
        color: #D9EEF2;
        font-size: 1.05rem;
        margin-top: .45rem;
    }

    .header-line {
        width: 70px;
        height: 4px;
        background: #D4AD45;
        border-radius: 5px;
        margin-top: 1rem;
    }

    /* SECTION */

    .section-heading {
        color: var(--navy);
        font-size: 1.35rem;
        font-weight: 750;
        margin-top: 1.5rem;
        margin-bottom: .5rem;
    }

    .section-description {
        color: var(--muted);
        font-size: .92rem;
        margin-bottom: 1rem;
    }

    /* DASHBOARD */

    .dashboard-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.25rem;
        min-height: 120px;

        box-shadow:
            0 4px 15px rgba(15, 23, 42, .05);
    }

    .dashboard-number {
        color: var(--navy);
        font-size: 2rem;
        font-weight: 800;
    }

    .dashboard-label {
        color: var(--muted);
        font-size: .85rem;
        margin-top: .3rem;
    }

    /* SEARCH */

    .stTextInput > div > div > input {
        background: white !important;
        color: var(--text) !important;

        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;

        padding: 13px !important;
        font-size: 1rem !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--teal) !important;

        box-shadow:
            0 0 0 1px var(--teal) !important;
    }

    .stTextInput label {
        color: var(--text) !important;
        font-weight: 650 !important;
    }

    /* UPLOAD */

    .upload-card {
        background: white;
        border: 2px dashed #9CCDD2;
        border-radius: 14px;
        padding: 1.4rem;
        margin-top: .8rem;

        box-shadow:
            0 4px 15px rgba(15, 23, 42, .04);
    }

    .upload-title {
        color: var(--navy);
        font-size: 1.1rem;
        font-weight: 750;
    }

    .upload-description {
        color: var(--muted);
        font-size: .9rem;
        margin-top: .25rem;
    }

    /* BOOK */

    .book-card {
        background: white;

        border: 1px solid var(--border);
        border-left: 4px solid var(--teal);

        border-radius: 12px;

        padding: 1.2rem 1.35rem;
        margin: .8rem 0;

        box-shadow:
            0 4px 15px rgba(15, 23, 42, .05);
    }

    .book-title {
        color: var(--navy);
        font-size: 1.25rem;
        font-weight: 750;
        line-height: 1.4;
        margin-bottom: .7rem;
    }

    .book-badge {
        display: inline-block;

        background: #F1F5F9;
        color: #475569;

        border: 1px solid #E2E8F0;
        border-radius: 6px;

        padding: 4px 9px;
        margin-right: 5px;

        font-size: .78rem;
        font-weight: 600;
    }

    .match-badge {
        display: inline-block;

        background: #E8F6F7;
        color: #12616B;

        border-radius: 6px;

        padding: 4px 9px;

        font-size: .78rem;
        font-weight: 650;
    }

    /* INFO */

    .info-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-top: 1rem;
    }

    .info-title {
        color: var(--navy);
        font-weight: 750;
        margin-bottom: .5rem;
    }

    .info-row {
        display: flex;
        justify-content: space-between;

        border-bottom: 1px solid #EEF2F6;
        padding: .55rem 0;

        font-size: .9rem;
    }

    .info-row:last-child {
        border-bottom: none;
    }

    .info-key {
        color: var(--muted);
    }

    .info-value {
        color: var(--text);
        font-weight: 650;
    }

    /* BUTTONS */

    .stButton > button {
        background: var(--navy);
        color: white;

        border: none;
        border-radius: 8px;

        font-weight: 650;

        padding: .55rem 1rem;
    }

    .stButton > button:hover {
        background: var(--teal);
        color: white;
    }

    /* DATAFRAME */

    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 10px;
    }

    hr {
        border-color: #E2E8F0 !important;
    }

    </style>
    """
)


# ============================================================
# HELPERS
# ============================================================

def safe(value):
    return html.escape(str(value or ""))


def normalize_text(text):
    if not text:
        return ""

    text = str(text).strip()

    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )

    arabic_diacritics = re.compile(
        r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
    )

    text = arabic_diacritics.sub("", text)

    text = text.translate(
        str.maketrans(
            {
                "أ": "ا",
                "إ": "ا",
                "آ": "ا",
                "ٱ": "ا",
                "ى": "ي",
                "ئ": "ي",
                "ؤ": "و",
                "ـ": "",
            }
        )
    )

    text = text.lower()

    text = re.sub(
        r"[^\w\u0600-\u06FF]+",
        " ",
        text,
        flags=re.UNICODE,
    )

    return " ".join(text.split())


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


def initialize_database():

    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,
            author TEXT DEFAULT '',
            publisher TEXT DEFAULT '',
            language TEXT DEFAULT '',
            category TEXT DEFAULT '',
            isbn TEXT DEFAULT '',
            catalogue_number TEXT DEFAULT '',

            source_pdf TEXT DEFAULT '',
            imported_at TEXT DEFAULT '',

            UNIQUE(
                title,
                author,
                publisher
            )
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            filename TEXT,
            uploaded_at TEXT,
            books_found INTEGER DEFAULT 0,
            books_added INTEGER DEFAULT 0,
            books_updated INTEGER DEFAULT 0,
            status TEXT
        )
        """
    )

    connection.commit()
    connection.close()


initialize_database()


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(uploaded_file):

    pdf_bytes = uploaded_file.getvalue()

    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf",
    )

    pages = []

    for page in document:

        text = page.get_text(
            "text"
        )

        if text:
            pages.append(text)

    document.close()

    return "\n".join(pages)


# ============================================================
# BOOK EXTRACTION
#
# This parser supports common catalogue labels.
# We can make it exact once you provide your PDF.
# ============================================================

def extract_books_from_text(text):

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    books = []

    current = {
        "title": "",
        "author": "",
        "publisher": "",
        "language": "",
        "category": "",
        "isbn": "",
        "catalogue_number": "",
    }

    current_field = None

    field_patterns = {
        "title": r"^(title|book\s*title|العنوان)\s*[:\-]\s*(.*)$",
        "author": r"^(author|authors|المؤلف|المؤلفون)\s*[:\-]\s*(.*)$",
        "publisher": r"^(publisher|الناشر)\s*[:\-]\s*(.*)$",
        "language": r"^(language|lang|اللغة)\s*[:\-]\s*(.*)$",
        "category": r"^(category|subject|التصنيف|الموضوع)\s*[:\-]\s*(.*)$",
        "isbn": r"^(isbn)\s*[:\-]?\s*(.*)$",
        "catalogue_number": (
            r"^(catalogue\s*(number|no)?|"
            r"catalog\s*(number|no)?)\s*[:\-]\s*(.*)$"
        ),
    }

    def save_current():

        if not current["title"]:
            return

        book = {
            key: value.strip()
            for key, value in current.items()
        }

        books.append(book)

    for line in lines:

        matched = False

        for field, pattern in field_patterns.items():

            match = re.match(
                pattern,
                line,
                flags=re.IGNORECASE,
            )

            if match:

                current[field] = match.groups()[-1].strip()

                current_field = field

                matched = True

                break

        if matched:
            continue

        # Blank/new record indicators
        if re.match(
            r"^(book|record|item)\s*#?\s*\d+",
            line,
            flags=re.IGNORECASE,
        ):

            if current["title"]:
                save_current()

            current = {
                "title": "",
                "author": "",
                "publisher": "",
                "language": "",
                "category": "",
                "isbn": "",
                "catalogue_number": "",
            }

            current_field = None

            continue

        # Continue previous field
        if current_field and current[current_field]:

            # Avoid making very long accidental fields.
            if len(current[current_field]) < 500:

                current[current_field] += " " + line

    save_current()

    return books


# ============================================================
# DATABASE IMPORT
# ============================================================

def import_books(
    books,
    filename,
):

    connection = get_connection()

    added = 0
    updated = 0

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    for book in books:

        title = book["title"].strip()

        if not title:
            continue

        existing = connection.execute(
            """
            SELECT id
            FROM books
            WHERE title = ?
              AND author = ?
              AND publisher = ?
            """,
            (
                title,
                book["author"],
                book["publisher"],
            ),
        ).fetchone()

        if existing:

            connection.execute(
                """
                UPDATE books

                SET language = ?,
                    category = ?,
                    isbn = ?,
                    catalogue_number = ?,
                    source_pdf = ?,
                    imported_at = ?

                WHERE id = ?
                """,
                (
                    book["language"],
                    book["category"],
                    book["isbn"],
                    book["catalogue_number"],
                    filename,
                    now,
                    existing["id"],
                ),
            )

            updated += 1

        else:

            connection.execute(
                """
                INSERT INTO books (
                    title,
                    author,
                    publisher,
                    language,
                    category,
                    isbn,
                    catalogue_number,
                    source_pdf,
                    imported_at
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    book["author"],
                    book["publisher"],
                    book["language"],
                    book["category"],
                    book["isbn"],
                    book["catalogue_number"],
                    filename,
                    now,
                ),
            )

            added += 1

    connection.execute(
        """
        INSERT INTO imports (
            filename,
            uploaded_at,
            books_found,
            books_added,
            books_updated,
            status
        )

        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            filename,
            now,
            len(books),
            added,
            updated,
            "Completed",
        ),
    )

    connection.commit()
    connection.close()

    return added, updated


# ============================================================
# SEARCH
# ============================================================

def search_books(query):

    query_normalized = normalize_text(query)

    if not query_normalized:
        return []

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            title,
            author,
            publisher,
            language,
            category,
            isbn,
            catalogue_number
        FROM books
        """
    ).fetchall()

    connection.close()

    results = []

    for row in rows:

        title = normalize_text(
            row["title"]
        )

        author = normalize_text(
            row["author"]
        )

        publisher = normalize_text(
            row["publisher"]
        )

        title_score = max(
            fuzz.ratio(query_normalized, title),
            fuzz.partial_ratio(query_normalized, title),
            fuzz.token_set_ratio(
                query_normalized,
                title,
            ),
        )

        author_score = max(
            fuzz.ratio(query_normalized, author),
            fuzz.partial_ratio(query_normalized, author),
            fuzz.token_set_ratio(
                query_normalized,
                author,
            ),
        ) if author else 0

        publisher_score = max(
            fuzz.ratio(
                query_normalized,
                publisher,
            ),
            fuzz.partial_ratio(
                query_normalized,
                publisher,
            ),
            fuzz.token_set_ratio(
                query_normalized,
                publisher,
            ),
        ) if publisher else 0

        # Exact title
        if query_normalized == title:

            score = 100
            reason = "Exact Title Match"

        # Query appears in title
        elif query_normalized in title:

            score = 98
            reason = "Title Match"

        # Strong title
        elif title_score >= 72:

            score = title_score
            reason = "Title Match"

        # Author
        elif author_score >= 78:

            score = author_score * 0.96
            reason = "Author Match"

        # Publisher
        elif publisher_score >= 82:

            score = publisher_score * 0.94
            reason = "Publisher Match"

        else:
            continue

        results.append(
            {
                "id": row["id"],
                "title": row["title"],
                "author": row["author"],
                "publisher": row["publisher"],
                "language": row["language"],
                "category": row["category"],
                "isbn": row["isbn"],
                "catalogue_number": row[
                    "catalogue_number"
                ],
                "score": round(score, 1),
                "reason": reason,
            }
        )

    results.sort(
        key=lambda x: (
            -x["score"],
            normalize_text(x["title"]),
        )
    )

    return results[:MAX_RESULTS]


# ============================================================
# STATISTICS
# ============================================================

def get_statistics():

    connection = get_connection()

    books = connection.execute(
        "SELECT COUNT(*) FROM books"
    ).fetchone()[0]

    authors = connection.execute(
        """
        SELECT COUNT(DISTINCT author)
        FROM books
        WHERE author != ''
        """
    ).fetchone()[0]

    publishers = connection.execute(
        """
        SELECT COUNT(DISTINCT publisher)
        FROM books
        WHERE publisher != ''
        """
    ).fetchone()[0]

    last_import = connection.execute(
        """
        SELECT filename, uploaded_at
        FROM imports
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    connection.close()

    return (
        books,
        authors,
        publishers,
        last_import,
    )


# ============================================================
# HEADER
# ============================================================

st.html(
    f"""
    <div class="library-header">

        <div class="main-heading">
            📚 {safe(APP_TITLE)}
        </div>

        <div class="sub-heading">
            {safe(APP_SUBTITLE)}
        </div>

        <div class="header-line"></div>

    </div>
    """
)


# ============================================================
# DASHBOARD
# ============================================================

(
    total_books,
    total_authors,
    total_publishers,
    last_import,
) = get_statistics()


st.html(
    """
    <div class="section-heading">
        Library Overview
    </div>

    <div class="section-description">
        Manage, import and search the Dar Makkah International
        library catalogue.
    </div>
    """
)


metric1, metric2, metric3 = st.columns(3)


with metric1:

    st.html(
        f"""
        <div class="dashboard-card">

            <div class="dashboard-number">
                {total_books:,}
            </div>

            <div class="dashboard-label">
                Total Books
            </div>

        </div>
        """
    )


with metric2:

    st.html(
        f"""
        <div class="dashboard-card">

            <div class="dashboard-number">
                {total_authors:,}
            </div>

            <div class="dashboard-label">
                Authors
            </div>

        </div>
        """
    )


with metric3:

    st.html(
        f"""
        <div class="dashboard-card">

            <div class="dashboard-number">
                {total_publishers:,}
            </div>

            <div class="dashboard-label">
                Publishers
            </div>

        </div>
        """
    )


# ============================================================
# PDF IMPORT
# ============================================================

st.html(
    """
    <div class="section-heading">
        📄 Import Catalogue
    </div>

    <div class="section-description">
        Upload your PDF catalogue. The system will extract the
        book information and prepare it for import into the
        library database.
    </div>
    """
)


st.html(
    """
    <div class="upload-card">

        <div class="upload-title">
            Upload PDF Catalogue
        </div>

        <div class="upload-description">
            Supported format: PDF
        </div>

    </div>
    """
)


uploaded_pdf = st.file_uploader(
    "Choose your catalogue PDF",
    type=["pdf"],
    label_visibility="collapsed",
)


if uploaded_pdf:

    st.success(
        f"PDF selected: {uploaded_pdf.name}"
    )

    with st.spinner(
        "Reading PDF and extracting catalogue data..."
    ):

        pdf_text = extract_pdf_text(
            uploaded_pdf
        )

    if not pdf_text.strip():

        st.error(
            "No readable text was found in this PDF. "
            "The PDF may be scanned or image-based."
        )

    else:

        extracted_books = (
            extract_books_from_text(
                pdf_text
            )
        )

        st.html(
            f"""
            <div class="info-card">

                <div class="info-title">
                    Extraction Result
                </div>

                <div class="info-row">
                    <span class="info-key">
                        PDF
                    </span>

                    <span class="info-value">
                        {safe(uploaded_pdf.name)}
                    </span>
                </div>

                <div class="info-row">
                    <span class="info-key">
                        Text extracted
                    </span>

                    <span class="info-value">
                        {len(pdf_text):,} characters
                    </span>
                </div>

                <div class="info-row">
                    <span class="info-key">
                        Books detected
                    </span>

                    <span class="info-value">
                        {len(extracted_books):,}
                    </span>
                </div>

            </div>
            """
        )

        if extracted_books:

            st.subheader(
                "Preview Extracted Books"
            )

            st.dataframe(
                extracted_books,
                use_container_width=True,
                hide_index=True,
            )

            st.warning(
                "Please check the preview before importing "
                "the records into the database."
            )

            if st.button(
                "📥 Import Books into Library",
                type="primary",
                use_container_width=True,
            ):

                with st.spinner(
                    "Importing books into library.db..."
                ):

                    added, updated = import_books(
                        extracted_books,
                        uploaded_pdf.name,
                    )

                st.success(
                    f"Import completed successfully. "
                    f"{added} new books added and "
                    f"{updated} existing books updated."
                )

                st.cache_data.clear()

                st.rerun()

        else:

            st.error(
                "The PDF text was read successfully, "
                "but no book records could be detected. "
                "The catalogue format needs to be configured."
            )


# ============================================================
# SEARCH
# ============================================================

st.html(
    """
    <div class="section-heading">
        🔎 Search Library
    </div>

    <div class="section-description">
        Search by title, author, publisher or keyword.
    </div>
    """
)


search_query = st.text_input(
    "Search Catalogue",
    placeholder=(
        "Enter book title, author, publisher or keyword..."
    ),
)


if search_query.strip():

    results = search_books(
        search_query
    )

    if results:

        st.caption(
            f"{len(results)} matching record(s)"
        )

        for book in results:

            st.html(
                f"""
                <div class="book-card">

                    <div class="book-title">
                        {safe(book["title"])}
                    </div>

                    <div>

                        <span class="book-badge">
                            Author:
                            {safe(book["author"] or "—")}
                        </span>

                        <span class="book-badge">
                            Publisher:
                            {safe(book["publisher"] or "—")}
                        </span>

                        <span class="book-badge">
                            Language:
                            {safe(book["language"] or "—")}
                        </span>

                        <span class="match-badge">
                            {safe(book["reason"])}
                            · {book["score"]}%
                        </span>

                    </div>

                </div>
                """
            )

            details1, details2 = st.columns(2)

            with details1:

                if book["category"]:
                    st.markdown(
                        f"**Category:** "
                        f"{book['category']}"
                    )

                if book["isbn"]:
                    st.markdown(
                        f"**ISBN:** "
                        f"{book['isbn']}"
                    )

            with details2:

                if book["catalogue_number"]:
                    st.markdown(
                        f"**Catalogue Number:** "
                        f"{book['catalogue_number']}"
                    )

            st.divider()

    else:

        st.info(
            "No matching books found. "
            "Try another title, author or keyword."
        )


# ============================================================
# LAST IMPORT
# ============================================================

if last_import:

    st.html(
        f"""
        <div class="info-card">

            <div class="info-title">
                Latest Catalogue Import
            </div>

            <div class="info-row">
                <span class="info-key">
                    File
                </span>

                <span class="info-value">
                    {safe(last_import["filename"])}
                </span>
            </div>

            <div class="info-row">
                <span class="info-key">
                    Imported
                </span>

                <span class="info-value">
                    {safe(last_import["uploaded_at"])}
                </span>
            </div>

        </div>
        """
    )
