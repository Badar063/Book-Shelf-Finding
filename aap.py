import html
import sqlite3
from pathlib import Path

import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

APP_TITLE = "Dar Makkah International"
APP_SUBTITLE = "Library Catalogue Search System"

DATABASE_FILE = Path("library.db")
LOGO_PATH = Path("a.jpg")


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
# PROFESSIONAL UI / UX
# ============================================================

st.html(
    """
    <style>

    /* ========================================================
       COLOUR SYSTEM
       ======================================================== */

    :root {
        --navy-950: #07111F;
        --navy-900: #0B1728;
        --navy-800: #101F33;
        --navy-700: #172A43;

        --gold: #D4AF37;
        --gold-light: #E8CC70;
        --gold-dark: #A98518;

        --white: #F8FAFC;
        --text: #E2E8F0;
        --muted: #94A3B8;

        --border: #263B55;
        --success: #22C55E;
    }


    /* ========================================================
       GLOBAL
       ======================================================== */

    .stApp {
        background:
            radial-gradient(
                circle at 50% -10%,
                rgba(212, 175, 55, 0.08),
                transparent 35%
            ),
            var(--navy-950);

        color: var(--white);
    }

    .main .block-container {
        max-width: 1250px;
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

    .library-header {
        text-align: center;
        padding: 1.5rem 0 2rem 0;
        margin-bottom: 1.5rem;

        border-bottom: 1px solid var(--border);
    }

    .logo-wrapper {
        display: flex;
        justify-content: center;
        margin-bottom: 1rem;
    }

    .library-logo {
        width: 170px;
        max-height: 115px;
        object-fit: contain;
        border-radius: 12px;
    }

    .brand-title {
        color: var(--white);
        font-size: 2.45rem;
        font-weight: 800;
        letter-spacing: 0.8px;
        line-height: 1.15;
        margin: 0;
    }

    .brand-subtitle {
        color: var(--gold-light);
        font-size: 1.05rem;
        font-weight: 500;
        margin-top: 0.55rem;
        letter-spacing: 0.3px;
    }

    .brand-line {
        width: 80px;
        height: 3px;
        background: var(--gold);
        margin: 1rem auto 0 auto;
        border-radius: 5px;
    }


    /* ========================================================
       WELCOME
       ======================================================== */

    .welcome-title {
        color: var(--white);
        font-size: 1.55rem;
        font-weight: 750;
        margin-bottom: 0.35rem;
    }

    .welcome-text {
        color: var(--muted);
        font-size: 0.96rem;
        margin-bottom: 1.1rem;
    }


    /* ========================================================
       SEARCH AREA
       ======================================================== */

    .search-container {
        background:
            linear-gradient(
                145deg,
                rgba(23, 42, 67, 0.95),
                rgba(16, 31, 51, 0.95)
            );

        border: 1px solid var(--border);
        border-radius: 16px;

        padding: 1.35rem;

        box-shadow:
            0 12px 35px rgba(0, 0, 0, 0.22);
    }

    .search-label {
        color: var(--white);
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .search-hint {
        color: var(--muted);
        font-size: 0.78rem;
        margin-top: 0.45rem;
    }

    .stTextInput > div > div > input {
        background: var(--navy-900) !important;
        color: var(--white) !important;

        border: 1px solid #344B68 !important;
        border-radius: 10px !important;

        min-height: 50px;
        padding: 12px 14px !important;

        font-size: 1rem !important;

        transition:
            border-color 0.2s ease,
            box-shadow 0.2s ease;
    }

    .stTextInput > div > div > input:hover {
        border-color: #58708E !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--gold) !important;

        box-shadow:
            0 0 0 1px var(--gold),
            0 0 15px rgba(212, 175, 55, 0.15) !important;
    }

    .stTextInput label {
        color: var(--white) !important;
        font-weight: 600 !important;
    }


    /* ========================================================
       DASHBOARD STATISTICS
       ======================================================== */

    .stats-heading {
        color: var(--white);
        font-size: 1.25rem;
        font-weight: 750;

        margin-top: 1.7rem;
        margin-bottom: 0.9rem;
    }

    .stat-card {
        background:
            linear-gradient(
                145deg,
                #111F32,
                #0E1A2B
            );

        border: 1px solid var(--border);
        border-radius: 14px;

        padding: 1.15rem 1rem;

        min-height: 115px;

        box-shadow:
            0 7px 22px rgba(0, 0, 0, 0.18);

        transition:
            transform 0.2s ease,
            border-color 0.2s ease;
    }

    .stat-card:hover {
        transform: translateY(-2px);
        border-color: #49627F;
    }

    .stat-icon {
        font-size: 1.15rem;
        margin-bottom: 0.25rem;
    }

    .stat-number {
        color: var(--gold-light);
        font-size: 1.8rem;
        font-weight: 800;
        line-height: 1.1;
    }

    .stat-label {
        color: var(--muted);
        font-size: 0.78rem;
        margin-top: 0.35rem;
    }


    /* ========================================================
       QUICK SEARCH
       ======================================================== */

    .section-title {
        color: var(--white);

        font-size: 1.25rem;
        font-weight: 750;

        margin-top: 1.8rem;
        margin-bottom: 0.75rem;

        padding-left: 0.7rem;

        border-left: 3px solid var(--gold);
    }

    .section-description {
        color: var(--muted);
        font-size: 0.88rem;
        margin-bottom: 0.9rem;
    }

    .quick-card {
        background: var(--navy-800);

        border: 1px solid var(--border);
        border-radius: 10px;

        padding: 0.85rem 1rem;

        color: var(--text);
        text-align: center;

        font-size: 0.86rem;
        font-weight: 600;
    }


    /* ========================================================
       DATABASE STATUS
       ======================================================== */

    .status-card {
        background: #0E1B2C;

        border: 1px solid var(--border);
        border-radius: 12px;

        padding: 1rem 1.15rem;

        margin-top: 1.8rem;
    }

    .status-title {
        color: var(--gold-light);
        font-size: 0.95rem;
        font-weight: 750;

        margin-bottom: 0.7rem;
    }

    .status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;

        padding: 0.45rem 0;

        border-bottom: 1px solid rgba(38, 59, 85, 0.7);

        font-size: 0.84rem;
    }

    .status-row:last-child {
        border-bottom: none;
    }

    .status-key {
        color: var(--muted);
    }

    .status-value {
        color: var(--text);
        font-weight: 650;
    }

    .status-connected {
        color: var(--success);
    }


    /* ========================================================
       EMPTY SEARCH STATE
       ======================================================== */

    .empty-state {
        background: var(--navy-800);

        border: 1px solid var(--border);
        border-radius: 14px;

        padding: 2.5rem 1.5rem;

        margin-top: 1rem;

        text-align: center;
    }

    .empty-icon {
        font-size: 2.4rem;
        margin-bottom: 0.4rem;
    }

    .empty-title {
        color: var(--white);
        font-size: 1.15rem;
        font-weight: 750;
    }

    .empty-text {
        color: var(--muted);
        font-size: 0.88rem;
        margin-top: 0.4rem;
    }


    /* ========================================================
       MOBILE
       ======================================================== */

    @media (max-width: 768px) {

        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1rem;
        }

        .brand-title {
            font-size: 1.75rem;
        }

        .brand-subtitle {
            font-size: 0.9rem;
        }

        .library-logo {
            width: 135px;
        }

    }

    </style>
    """
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


def initialise_database():
    """
    Creates the database and books table if they don't exist.

    The database can therefore start completely empty.
    """

    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shelf TEXT,
            title TEXT,
            author TEXT,
            publisher TEXT,
            language TEXT
        )
        """
    )

    connection.commit()
    connection.close()


initialise_database()


# ============================================================
# DATABASE STATISTICS
# ============================================================

def get_statistics():

    connection = get_connection()

    total_books = connection.execute(
        "SELECT COUNT(*) FROM books"
    ).fetchone()[0]

    total_authors = connection.execute(
        """
        SELECT COUNT(DISTINCT author)
        FROM books
        WHERE author IS NOT NULL
          AND TRIM(author) != ''
        """
    ).fetchone()[0]

    total_publishers = connection.execute(
        """
        SELECT COUNT(DISTINCT publisher)
        FROM books
        WHERE publisher IS NOT NULL
          AND TRIM(publisher) != ''
        """
    ).fetchone()[0]

    total_languages = connection.execute(
        """
        SELECT COUNT(DISTINCT language)
        FROM books
        WHERE language IS NOT NULL
          AND TRIM(language) != ''
        """
    ).fetchone()[0]

    connection.close()

    return (
        total_books,
        total_authors,
        total_publishers,
        total_languages,
    )


(
    total_books,
    total_authors,
    total_publishers,
    total_languages,
) = get_statistics()


# ============================================================
# LOGO
# ============================================================

logo_html = ""

if LOGO_PATH.exists():

    import base64

    try:

        image_bytes = LOGO_PATH.read_bytes()

        encoded = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        logo_html = f"""
        <div class="logo-wrapper">
            <img
                class="library-logo"
                src="data:image/jpeg;base64,{encoded}"
                alt="Dar Makkah International"
            >
        </div>
        """

    except Exception:
        logo_html = ""


# ============================================================
# HEADER
# ============================================================

st.html(
    f"""
    <div class="library-header">

        {logo_html}

        <div class="brand-title">
            {html.escape(APP_TITLE)}
        </div>

        <div class="brand-subtitle">
            {html.escape(APP_SUBTITLE)}
        </div>

        <div class="brand-line"></div>

    </div>
    """
)


# ============================================================
# WELCOME
# ============================================================

st.html(
    """
    <div class="welcome-title">
        Welcome to the Library Catalogue
    </div>

    <div class="welcome-text">
        Search the catalogue by book title, author,
        publisher, or keyword.
    </div>
    """
)


# ============================================================
# SEARCH
# ============================================================

st.html(
    """
    <div class="search-container">
        <div class="search-label">
            🔎 Search Catalogue
        </div>
    </div>
    """
)

search_query = st.text_input(
    "Search Catalogue",
    placeholder="Enter a book title, author, publisher or keyword...",
    label_visibility="collapsed",
)

st.caption(
    "Supports English and Arabic catalogue searches."
)


# ============================================================
# SEARCH RESULTS
# ============================================================

if search_query.strip():

    # Search functionality will be connected here.
    # We will bring your existing fuzzy/Arabic search
    # engine into this section in the next stage.

    st.html(
        """
        <div class="empty-state">

            <div class="empty-icon">
                🔎
            </div>

            <div class="empty-title">
                Search engine ready
            </div>

            <div class="empty-text">
                Your existing Arabic normalization and
                fuzzy-search system will be connected here.
            </div>

        </div>
        """
    )


# ============================================================
# DASHBOARD
# ============================================================

else:

    st.html(
        """
        <div class="stats-heading">
            Catalogue Overview
        </div>
        """
    )

    stat1, stat2, stat3, stat4 = st.columns(4)

    with stat1:
        st.html(
            f"""
            <div class="stat-card">
                <div class="stat-icon">📚</div>
                <div class="stat-number">{total_books:,}</div>
                <div class="stat-label">Books in Catalogue</div>
            </div>
            """
        )

    with stat2:
        st.html(
            f"""
            <div class="stat-card">
                <div class="stat-icon">👤</div>
                <div class="stat-number">{total_authors:,}</div>
                <div class="stat-label">Authors</div>
            </div>
            """
        )

    with stat3:
        st.html(
            f"""
            <div class="stat-card">
                <div class="stat-icon">🏢</div>
                <div class="stat-number">{total_publishers:,}</div>
                <div class="stat-label">Publishers</div>
            </div>
            """
        )

    with stat4:
        st.html(
            f"""
            <div class="stat-card">
                <div class="stat-icon">🌐</div>
                <div class="stat-number">{total_languages:,}</div>
                <div class="stat-label">Languages</div>
            </div>
            """
        )


    # ========================================================
    # QUICK SEARCH
    # ========================================================

    st.html(
        """
        <div class="section-title">
            Quick Search
        </div>

        <div class="section-description">
            You can search using a complete title,
            author's name, publisher, or individual keywords.
        </div>
        """
    )

    q1, q2, q3, q4 = st.columns(4)

    with q1:
        st.html(
            """
            <div class="quick-card">
                📖 Book Titles
            </div>
            """
        )

    with q2:
        st.html(
            """
            <div class="quick-card">
                👤 Authors
            </div>
            """
        )

    with q3:
        st.html(
            """
            <div class="quick-card">
                🏢 Publishers
            </div>
            """
        )

    with q4:
        st.html(
            """
            <div class="quick-card">
                🌐 Languages
            </div>
            """
        )


# ============================================================
# CATALOGUE STATUS
# ============================================================

database_status = (
    "Ready"
    if DATABASE_FILE.exists()
    else "Unavailable"
)

st.html(
    f"""
    <div class="status-card">

        <div class="status-title">
            Catalogue System Status
        </div>

        <div class="status-row">
            <span class="status-key">
                Database
            </span>

            <span class="status-value status-connected">
                ● {html.escape(database_status)}
            </span>
        </div>

        <div class="status-row">
            <span class="status-key">
                Database File
            </span>

            <span class="status-value">
                {html.escape(DATABASE_FILE.name)}
            </span>
        </div>

        <div class="status-row">
            <span class="status-key">
                Books Indexed
            </span>

            <span class="status-value">
                {total_books:,}
            </span>
        </div>

        <div class="status-row">
            <span class="status-key">
                Search
            </span>

            <span class="status-value">
                Arabic + English
            </span>
        </div>

    </div>
    """
)
