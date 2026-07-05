import os
import calendar
import time
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Date, Numeric, DateTime, text, func
from sqlalchemy.orm import declarative_base, sessionmaker

# -----------------------------------------------------------------------------
# CONFIGURATION & STYLE (UI/UX EXPERT MODE)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Finances | Workspace",
    page_icon="✺",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_style():
    st.markdown(
        """
        <style>
            /* Typography & Variables - Zinc Palette */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            :root {
                --bg-base: #09090b;
                --bg-surface: #18181b;
                --border-color: #27272a;
                --text-main: #f4f4f5;
                --text-muted: #a1a1aa;
                --accent-blue: #3b82f6;
                --accent-green: #10b981;
                --accent-red: #ef4444;
            }

            /* Global Styles */
            body, .stApp, .main, [data-testid="stHeader"] {
                background-color: var(--bg-base) !important;
                color: var(--text-main) !important;
                font-family: 'Inter', -apple-system, sans-serif !important;
            }

            [data-testid="stSidebar"] {
                background-color: var(--bg-surface) !important;
                border-right: 1px solid var(--border-color) !important;
            }

            /* Bento Grid Cards (Streamlit Containers with borders) */
            [data-testid="stVerticalBlockBorderWrapper"] {
                background-color: var(--bg-surface) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 1rem !important; /* rounded-2xl */
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            
            /* Typography overrides */
            h1, h2, h3 { color: var(--text-main) !important; font-weight: 600 !important; tracking: -0.025em; }
            p { color: var(--text-muted) !important; }

            /* Buttons (Primary Action) */
            .stButton>button {
                background-color: var(--text-main);
                color: var(--bg-base);
                border-radius: 0.5rem;
                border: none;
                font-weight: 500;
                padding: 0.5rem 1rem;
                transition: opacity 0.2s;
            }
            .stButton>button:hover { opacity: 0.9; color: var(--bg-base); background-color: var(--text-main); }
            
            /* Inputs */
            .stTextInput>div>div>input, .stNumberInput>div>div>input, .stDateInput>div>div>input, .stSelectbox>div>div>div {
                background-color: var(--bg-base) !important;
                color: var(--text-main) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 0.5rem !important;
            }

            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 2rem;
                background-color: transparent;
            }
            .stTabs [data-baseweb="tab"] {
                color: var(--text-muted);
                padding-top: 1rem;
                padding-bottom: 1rem;
                border-bottom: 2px solid transparent;
            }
            .stTabs [aria-selected="true"] {
                color: var(--text-main) !important;
                border-bottom: 2px solid var(--text-main) !important;
            }

            /* Custom Transaction List Items */
            .tx-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0.75rem 0;
                border-bottom: 1px solid var(--border-color);
            }
            .tx-row:last-child { border-bottom: none; }
            .tx-left { display: flex; align-items: center; gap: 1rem; }
            .tx-icon-box {
                width: 40px; height: 40px;
                border-radius: 0.5rem;
                background-color: var(--bg-base);
                border: 1px solid var(--border-color);
                display: flex; align-items: center; justify-content: center;
            }
            .tx-info { display: flex; flex-direction: column; }
            .tx-title { font-weight: 500; color: var(--text-main); font-size: 0.95rem; }
            .tx-date { font-size: 0.8rem; color: var(--text-muted); }
            .tx-amount { font-weight: 600; font-variant-numeric: tabular-nums; }
            .tx-amount.gain { color: var(--accent-green); }
            .tx-amount.expense { color: var(--text-main); }
            
            /* Custom Metrics */
            [data-testid="stMetricValue"] { font-weight: 600 !important; color: var(--text-main) !important; }
            [data-testid="stMetricDelta"] svg { display: none; } /* Hide default arrows for cleaner look */
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_custom_style()

if "expense_categories" not in st.session_state:
    st.session_state["expense_categories"] = [
        "Alimentation",
        "Transport",
        "Logement",
        "Loisirs",
        "Santé",
        "Abonnements",
        "Autre"
    ]

if "income_categories" not in st.session_state:
    st.session_state["income_categories"] = [
        "Salaire",
        "Remboursement",
        "Cadeau",
        "Autre"
    ]

# -----------------------------------------------------------------------------
# SVG ICONS (Lucide Style)
# -----------------------------------------------------------------------------
ICONS = {
    "arrow-up-right": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7h10v10"/><path d="M7 17 17 7"/></svg>',
    "arrow-down-left": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a1a1aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 17H7V7"/><path d="M17 7 7 17"/></svg>',
    "wallet": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f4f4f5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg>'
}

# -----------------------------------------------------------------------------
# DATABASE SETUP
# -----------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///finance.db")

# Log database configuration (hide password)
db_display = DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('://')[-1] if '@' in DATABASE_URL else '', '***') if '@' in DATABASE_URL else DATABASE_URL
print(f"[DEBUG] Connecting to database: {db_display}")

try:
    engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True, echo=False)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base = declarative_base()
    
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("[DEBUG] Database connection successful ✓")
except Exception as e:
    print(f"[ERROR] Database connection failed: {str(e)}")
    st.error(f"❌ **Database Error**: {str(e)}")
    st.stop()

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    expense_date = Column(Date, nullable=False)
    expense_type = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    expense_type = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Income(Base):
    __tablename__ = "incomes"
    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    income_date = Column(Date, nullable=False)
    income_type = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    print("[DEBUG] Initializing database tables...")
    try:
        if DATABASE_URL.startswith("sqlite"):
            Base.metadata.create_all(bind=engine)
            print("[DEBUG] SQLite tables created ✓")
            return
        
        for attempt in range(30):
            try:
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                Base.metadata.create_all(bind=engine)
                print(f"[DEBUG] Database tables initialized on attempt {attempt + 1} ✓")
                return
            except Exception as e:
                if attempt == 29:
                    print(f"[ERROR] Failed to initialize database after 30 attempts: {str(e)}")
                    raise
                print(f"[DEBUG] Retry {attempt + 1}/30 - waiting for database...")
                time.sleep(2)
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {str(e)}")
        raise

init_db()

today = date.today()

# -----------------------------------------------------------------------------
# DATA LOGIC
# Database refresh mechanism to invalidate Streamlit cache
def invalidate_cache():
    """Force cache invalidation by clearing cached function"""
    if "last_refresh" in st.session_state:
        st.session_state["last_refresh"] = time.time()
    st.cache_data.clear()
    print(f"[DEBUG] Cache invalidated at {time.time()}")

# Initialize refresh token
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = 0

def format_currency(value: float) -> str:
    return f"{value:,.2f} €".replace(",", " ")

@st.cache_data(show_spinner=False, ttl=1)
def get_transactions_for_month(year: int, month: int, refresh: float = 0) -> pd.DataFrame:
    session = SessionLocal()
    try:
        month_start = date(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        month_end = date(year, month, last_day)
        
        print(f"[DEBUG] Fetching transactions for {year}-{month:02d} ({month_start} to {month_end})")

        rows = []
        # Incomes
        incomes = session.query(Income).filter(Income.income_date >= month_start, Income.income_date <= month_end).all()
        print(f"[DEBUG] Found {len(incomes)} incomes")
        for i in incomes:
            rows.append({
                "id": i.id,
                "source": "income",
                "type": "gain",
                "date": i.income_date,
                "nom": i.description,
                "montant": float(i.amount),
                "categorie": i.category,
                "sub_type": i.income_type,
                "end_date": None,
            })
        
        # One-time Expenses
        expenses = session.query(Expense).filter(Expense.expense_date >= month_start, Expense.expense_date <= month_end).all()
        print(f"[DEBUG] Found {len(expenses)} one-time expenses")
        for e in expenses:
            rows.append({
                "id": e.id,
                "source": "expense",
                "type": "depense",
                "date": e.expense_date,
                "nom": e.description,
                "montant": float(e.amount),
                "categorie": e.category,
                "sub_type": e.expense_type,
                "end_date": None,
            })
        
        # Recurring Expenses
        recurring = session.query(RecurringExpense).filter(RecurringExpense.start_date <= month_end).all()
        print(f"[DEBUG] Found {len(recurring)} recurring expenses (total, filtering active ones)")
        for r in recurring:
            if r.end_date is not None and r.end_date < month_start: continue
            rows.append({
                "id": r.id,
                "source": "recurring",
                "type": "depense",
                "date": date(year, month, 1),
                "nom": r.name,
                "montant": float(r.amount),
                "categorie": r.category,
                "sub_type": r.expense_type,
                "end_date": r.end_date,
            })

        df = pd.DataFrame(rows)
        print(f"[DEBUG] Total {len(df)} transactions loaded ✓")
        if df.empty: return pd.DataFrame(columns=["id", "type", "date", "nom", "montant", "categorie"])
        return df.sort_values(by=["date", "id"], ascending=[False, False]).reset_index(drop=True)
    except Exception as e:
        print(f"[ERROR] Failed to fetch transactions: {str(e)}")
        return pd.DataFrame(columns=["id", "type", "date", "nom", "montant", "categorie"])
    finally:
        session.close()

def get_monthly_kpis(year: int, month: int, refresh: float = 0) -> dict:
    df = get_transactions_for_month(year, month, refresh)
    if df.empty:
        return {"gains": 0.0, "depenses": 0.0, "solde": 0.0, "df": df}
    
    gains = df[df["type"] == "gain"]["montant"].sum()
    depenses = df[df["type"] == "depense"]["montant"].sum()
    return {"gains": gains, "depenses": depenses, "solde": gains - depenses, "df": df}


def get_transaction_record(source: str, tx_id: int):
    session = SessionLocal()
    try:
        if source == "income":
            return session.get(Income, tx_id)
        if source == "expense":
            return session.get(Expense, tx_id)
        if source == "recurring":
            return session.get(RecurringExpense, tx_id)
        return None
    finally:
        session.close()


def update_transaction_record(source: str, tx_id: int, description: str, amount: float, tx_date: date, tx_type: str, category: str, end_date: date | None = None):
    session = SessionLocal()
    try:
        print(f"[DEBUG] Updating {source} transaction ID {tx_id}...")
        
        if source == "income":
            record = session.get(Income, tx_id)
            if record is None:
                print(f"[ERROR] Income record {tx_id} not found")
                return False
            record.description = description
            record.amount = amount
            record.income_date = tx_date
            record.income_type = tx_type
            record.category = category
        elif source == "expense":
            record = session.get(Expense, tx_id)
            if record is None:
                print(f"[ERROR] Expense record {tx_id} not found")
                return False
            record.description = description
            record.amount = amount
            record.expense_date = tx_date
            record.expense_type = tx_type
            record.category = category
        elif source == "recurring":
            record = session.get(RecurringExpense, tx_id)
            if record is None:
                print(f"[ERROR] RecurringExpense record {tx_id} not found")
                return False
            record.name = description
            record.amount = amount
            record.start_date = tx_date
            record.end_date = end_date
            record.expense_type = tx_type
            record.category = category
        else:
            print(f"[ERROR] Unknown source: {source}")
            return False
            
        session.commit()
        print(f"[DEBUG] Transaction {source}#{tx_id} updated successfully ✓")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update transaction: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()


def clear_edit_session():
    for key in ["edit_tx_id", "edit_tx_source", "edit_tx_row_key", "edit_tx_type", "edit_tx_nom", "edit_tx_montant", "edit_tx_date", "edit_tx_categorie", "edit_tx_sub_type", "edit_tx_end_date"]:
        if key in st.session_state:
            del st.session_state[key]

# -----------------------------------------------------------------------------
# COMPONENTS
# -----------------------------------------------------------------------------
def render_transaction_row(tx):
    icon = ICONS["arrow-up-right"] if tx["type"] == "gain" else ICONS["arrow-down-left"]
    amount_class = "gain" if tx["type"] == "gain" else "expense"
    sign = "+" if tx["type"] == "gain" else "-"
    
    html = f"""
<div class="tx-row">
    <div class="tx-left">
        <div class="tx-icon-box">{icon}</div>
        <div class="tx-info">
            <span class="tx-title">{tx['nom']}</span>
            <span class="tx-date">{tx['date'].strftime('%d %b %Y')} • {tx['categorie']}</span>
        </div>
    </div>
    <div class="tx-amount {amount_class}">{sign}{tx['montant']:.2f} €</div>
</div>
"""
    return html.strip()


def render_transaction_item(tx, context_key: str = ""):
    row_key = f"{tx['source']}-{tx['id']}-{context_key}"
    cols = st.columns([10, 1])
    with cols[0]:
        st.markdown(render_transaction_row(tx), unsafe_allow_html=True)
    with cols[1]:
        if st.button("✎", key=f"edit-{row_key}"):
            st.session_state["edit_tx_id"] = tx["id"]
            st.session_state["edit_tx_source"] = tx["source"]
            st.session_state["edit_tx_row_key"] = row_key
            st.session_state["edit_tx_type"] = tx["sub_type"]
            st.session_state["edit_tx_nom"] = tx["nom"]
            st.session_state["edit_tx_montant"] = tx["montant"]
            st.session_state["edit_tx_date"] = tx["date"]
            st.session_state["edit_tx_categorie"] = tx["categorie"]
            st.session_state["edit_tx_sub_type"] = tx["sub_type"]
            st.session_state["edit_tx_end_date"] = tx.get("end_date")

    if st.session_state.get("edit_tx_row_key") == row_key:
        render_edit_transaction_panel()


def render_edit_transaction_panel():
    if "edit_tx_id" not in st.session_state:
        return

    source = st.session_state["edit_tx_source"]
    is_income = source == "income"
    is_recurring = source == "recurring"
    title = "Gain" if is_income else ("Dépense récurrente" if is_recurring else "Dépense ponctuelle")

    with st.expander(f"Modifier la transaction #{st.session_state['edit_tx_id']} ({title})", expanded=True):
        nom = st.text_input("Libellé", value=st.session_state.get("edit_tx_nom", ""), key="edit_nom")
        montant = st.number_input("Montant (€)", min_value=0.0, value=float(st.session_state.get("edit_tx_montant", 0.0)), step=1.0, key="edit_montant")
        date_tx = st.date_input("Date", value=st.session_state.get("edit_tx_date", date.today()), key="edit_date")

        if is_income:
            cat_list = st.session_state["income_categories"]
            tx_type_options = ["Salaire", "Remboursement", "Autre"]
        else:
            cat_list = st.session_state["expense_categories"]
            tx_type_options = ["Besoin", "Compulsif"]

        category = st.selectbox("Catégorie", cat_list, index=cat_list.index(st.session_state.get("edit_tx_categorie", cat_list[0])), key="edit_categorie")
        sub_type = st.selectbox("Classification", tx_type_options, index=tx_type_options.index(st.session_state.get("edit_tx_sub_type", tx_type_options[0])), key="edit_sub_type")

        end_date = None
        if is_recurring:
            end_date = st.date_input("Date de fin", value=st.session_state.get("edit_tx_end_date") or date.today(), key="edit_end_date")

        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("Sauvegarder", key="save_edit"):
                if not nom or montant <= 0:
                    st.error("Le libellé et le montant sont obligatoires.")
                else:
                    success = update_transaction_record(
                        source,
                        st.session_state["edit_tx_id"],
                        nom.strip(),
                        montant,
                        date_tx,
                        sub_type,
                        category.strip(),
                        end_date if is_recurring else None,
                    )
                    if success:
                        st.success("✓ Transaction modifiée.")
                        # Force cache invalidation
                        invalidate_cache()
                        st.rerun()
                    else:
                        st.error("Impossible de modifier la transaction.")
        with col_cancel:
            if st.button("Annuler", key="cancel_edit"):
                clear_edit_session()

@st.dialog("Nouvelle Transaction")
def add_transaction_modal():
    st.markdown("<p style='margin-bottom: 2rem;'>Enregistrez un flux entrant ou sortant.</p>", unsafe_allow_html=True)
    
    type_tx = st.radio("Type", ["Dépense ponctuelle", "Dépense récurrente", "Gain"], horizontal=True, label_visibility="collapsed")
    nom = st.text_input("Libellé", placeholder="Ex: Abonnement, Courses, Salaire...")
    montant = st.number_input("Montant (€)", min_value=0.0, step=1.0)
    
    col1, col2 = st.columns(2)
    with col1:
        date_tx = st.date_input("Date", value=date.today())
    with col2:
        if type_tx == "Gain":
            cat = st.selectbox("Catégorie", st.session_state["income_categories"])
            sub_type = st.selectbox("Classification", ["Salaire", "Remboursement", "Autre"])
        else:
            cat = st.selectbox("Catégorie", st.session_state["expense_categories"])
            sub_type = st.selectbox("Classification", ["Besoin", "Compulsif"])

        custom_cat = ""
        if cat == "Autre":
            custom_cat = st.text_input("Nouvelle catégorie", value="")

    end_date = None
    if type_tx == "Dépense récurrente":
        has_end = st.checkbox("Définir une date de fin")
        if has_end:
            end_date = st.date_input("Date de fin")

    if st.button("Enregistrer", use_container_width=True):
        if not nom or montant <= 0:
            st.error("Le libellé et le montant sont obligatoires.")
            return

        if cat == "Autre":
            if not custom_cat:
                st.error("Veuillez renseigner une catégorie personnalisée.")
                return
            category = custom_cat.strip()
            if category and category not in st.session_state["expense_categories"] and category not in st.session_state["income_categories"]:
                if type_tx == "Gain":
                    st.session_state["income_categories"].append(category)
                else:
                    st.session_state["expense_categories"].append(category)
        else:
            category = cat
            if not category:
                st.error("La catégorie est obligatoire.")
                return
            category = category.strip()

        session = SessionLocal()
        try:
            print(f"[DEBUG] Adding new transaction: {type_tx} - {nom} ({montant}€)")
            
            if type_tx == "Dépense ponctuelle":
                session.add(Expense(description=nom, amount=montant, expense_date=date_tx, expense_type=sub_type, category=category))
            elif type_tx == "Dépense récurrente":
                session.add(RecurringExpense(name=nom, amount=montant, start_date=date_tx, end_date=end_date, expense_type=sub_type, category=category))
            else:
                session.add(Income(description=nom, amount=montant, income_date=date_tx, income_type=sub_type, category=category))
            
            session.commit()
            print(f"[DEBUG] Transaction saved successfully ✓")
            
            # Force cache invalidation
            invalidate_cache()
            st.rerun()
            
        except Exception as e:
            print(f"[ERROR] Failed to save transaction: {str(e)}")
            session.rollback()
            st.error(f"❌ Erreur lors de l'enregistrement: {str(e)}")
        finally:
            session.close()

if st.button("➕ Nouvelle Transaction", use_container_width=True):
    add_transaction_modal()

st.markdown("<br><p style='font-size:0.8rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;'>Navigation</p>", unsafe_allow_html=True)
nav = st.radio("Aller à", ["Dashboard", "Transactions", "Statistiques"], label_visibility="collapsed")

st.markdown("<br><p style='font-size:0.8rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;'>Période</p>", unsafe_allow_html=True)
colA, colB = st.columns(2)
selected_month = colA.selectbox("Mois", list(range(1, 13)), index=today.month - 1, label_visibility="collapsed")
selected_year = colB.selectbox("Année", list(range(today.year - 2, today.year + 1)), index=2, label_visibility="collapsed")

refresh_token = st.session_state.get("transaction_refresh", 0)
kpis = get_monthly_kpis(selected_year, selected_month, refresh_token)

if nav == "Dashboard":
    # HERO SECTION
    st.markdown(f"<h1>Bonjour, voici votre situation.</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='margin-bottom:2rem;'>Résumé de {calendar.month_name[selected_month]} {selected_year}</p>", unsafe_allow_html=True)

    # BENTO GRID - ROW 1 (KPIs)
    col1, col2, col3 = st.columns(3)
    with col1.container(border=True):
        st.markdown("<p style='font-size:0.9rem; font-weight:500; color:var(--text-muted); margin-bottom:0.5rem;'>Solde Net</p>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='margin:0; font-variant-numeric: tabular-nums;'>{format_currency(kpis['solde'])}</h2>", unsafe_allow_html=True)
    with col2.container(border=True):
        st.markdown("<p style='font-size:0.9rem; font-weight:500; color:var(--text-muted); margin-bottom:0.5rem;'>Total Gains</p>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='margin:0; color:var(--accent-green); font-variant-numeric: tabular-nums;'>{format_currency(kpis['gains'])}</h2>", unsafe_allow_html=True)
    with col3.container(border=True):
        st.markdown("<p style='font-size:0.9rem; font-weight:500; color:var(--text-muted); margin-bottom:0.5rem;'>Total Dépenses</p>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='margin:0; color:var(--text-main); font-variant-numeric: tabular-nums;'>{format_currency(kpis['depenses'])}</h2>", unsafe_allow_html=True)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # BENTO GRID - ROW 2 (Chart & Latest TX)
    col_chart, col_list = st.columns([1.5, 1])
    
    with col_chart.container(border=True):
        st.markdown("<h3>Dépenses par catégorie</h3>", unsafe_allow_html=True)
        df_depenses = kpis['df'][kpis['df']['type'] == 'depense']
        if not df_depenses.empty:
            cat_df = df_depenses.groupby('categorie')['montant'].sum().reset_index()
            fig = px.bar(cat_df, x='montant', y='categorie', orientation='h', template='plotly_dark',
                         color_discrete_sequence=["#f4f4f5"])
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title=None, yaxis_title=None,
                showlegend=False,
                font=dict(family="Inter", color="#a1a1aa")
            )
            fig.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.markdown("<p style='text-align:center; padding: 2rem 0;'>Aucune dépense ce mois-ci.</p>", unsafe_allow_html=True)

    with col_list.container(border=True):
        st.markdown("<h3>Dernières transactions</h3>", unsafe_allow_html=True)
        df_recent = kpis['df'].head(5)
        if not df_recent.empty:
            for _, row in df_recent.iterrows():
                render_transaction_item(row, context_key="recent")
        else:
            st.markdown("<p style='text-align:center; padding: 2rem 0;'>Aucune transaction.</p>", unsafe_allow_html=True)

elif nav == "Transactions":
    st.markdown(f"<h1>Historique des transactions</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Toutes", "Gains", "Dépenses"])
    
    df_tx = kpis['df']
    
    def display_tx_list(df_filter, context_key: str):
        with st.container(border=True):
            if df_filter.empty:
                st.markdown("<p style='text-align:center; padding: 3rem 0;'>Aucune donnée pour cette sélection.</p>", unsafe_allow_html=True)
            else:
                for _, row in df_filter.iterrows():
                    render_transaction_item(row, context_key=context_key)

    with tab1: display_tx_list(df_tx, "all")
    with tab2: display_tx_list(df_tx[df_tx['type'] == 'gain'], "gain")
    with tab3: display_tx_list(df_tx[df_tx['type'] == 'depense'], "depense")

elif nav == "Statistiques":
    st.markdown("<h1>Statistiques avancées</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<p style='text-align:center; padding: 4rem 0; color:var(--text-muted);'>L'analyse annuelle et prédictive sera bientôt disponible dans cette vue.</p>", unsafe_allow_html=True)