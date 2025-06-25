# ─────────────────────────────────────────────────────────────
#  dashboard.py
#  Vollständig deutschsprachiges Executive‑Dashboard
# ─────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import plotly.express as px
from statistics import median
from company_data import ANBIETER

# optionale Pakete
try:
    from st_aggrid import AgGrid, GridOptionsBuilder
    AGGRID_VORHANDEN = True
except ImportError:
    AGGRID_VORHANDEN = False

try:
    import openpyxl  # noqa: F401
    EXCEL_VORHANDEN = True
except ImportError:
    EXCEL_VORHANDEN = False

# ────────────── Grundeinstellungen ──────────────
st.set_page_config(page_title="KI‑Transkriptionsanbieter DE",
                   page_icon="🤖", layout="wide")

# ────────────── Styling ──────────────
st.markdown("""
<style>
body,.stApp{background:#F5F7FA;color:#0F0F0F;}
h1.kopf{font-size:2.6rem;
  background:linear-gradient(90deg,#0062FF 0%,#00C6FF 60%,#A8EBFF 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.card{background:rgba(255,255,255,.6);backdrop-filter:blur(6px);
  border-radius:1rem;padding:1.2rem 1.5rem;box-shadow:0 8px 32px rgba(0,0,0,.08);}
#MainMenu,footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ────────────── Daten laden ──────────────
df_alle = pd.DataFrame(ANBIETER)
PREIS_SPALTE = "preis_eur_min"

# ────────────── Sidebar‑Filter ──────────────
st.sidebar.header("🔧 Filter")

# Preis‑Slider
preisse = df_alle[PREIS_SPALTE].dropna()
preis_min, preis_max = (float(preisse.min()), float(preisse.max())) if not preisse.empty else (0.0, 0.0)

preisbereich = st.sidebar.slider(
    "Preisbereich (€/min)",
    min_value=0.0,
    max_value=preis_max if preis_max else 1.0,
    value=(preis_min, preis_max),
    step=0.01,
)

# Suche
suchtext = st.sidebar.text_input("Suche (Name oder Kunde)")

# Filter anwenden
maske_preis = df_alle[PREIS_SPALTE].fillna(preisbereich[1]).between(*preisbereich)
maske_suche = df_alle["name"].str.contains(suchtext, case=False, na=False) | \
              df_alle["kunden"].str.contains(suchtext, case=False, na=False)
df_gefiltert = df_alle[maske_preis & maske_suche].copy()

# Sidebar‑Radio
st.sidebar.markdown("---")
if df_gefiltert.empty:
    st.sidebar.info("Kein Anbieter entspricht den Filtern.")
    ausgewaehlter_name = None
else:
    ausgewaehlter_name = st.sidebar.radio(
        "Anbieter auswählen",
        options=df_gefiltert["name"].tolist(),
        index=0,
    )

# ────────────── Kopf/KPIs ──────────────
st.markdown('<h1 class="kopf">🤖 KI‑Transkriptionsanbieter – Deutschland</h1>',
            unsafe_allow_html=True)
st.caption("Stand 24 Jun 2025 • Netto‑Preise • Angaben ohne Gewähr")

k1, k2, k3 = st.columns(3, gap="large")
k1.metric("Gefilterte Anbieter", len(df_gefiltert))

preise_gefiltert = df_gefiltert[PREIS_SPALTE].dropna()
if not preise_gefiltert.empty:
    k2.metric("Günstigster Preis", f"{preise_gefiltert.min():.3f} € / min")
    k3.metric("Median‑Preis", f"{median(preise_gefiltert):.3f} € / min")
else:
    k2.metric("Günstigster Preis", "—")
    k3.metric("Median‑Preis", "—")

st.markdown("")

# ────────────── Tabs ──────────────
tab_markt, tab_details, tab_tabelle, tab_donut = st.tabs(
    ["📊 Markt‑Überblick", "🔍 Anbieter‑Details",
     "📑 Vergleichstabelle", "📈 Preis­kategorien"]
)

# ───── Markt‑Überblick ─────
with tab_markt:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Preis‑Benchmark (€/Min.)")

    if preise_gefiltert.empty:
        st.info("Keine Preisangaben unter den aktuellen Filtern.")
    else:
        df_balken = df_gefiltert.dropna(subset=[PREIS_SPALTE]).sort_values(PREIS_SPALTE)
        fig_balken = px.bar(df_balken, x="name", y=PREIS_SPALTE, text=PREIS_SPALTE,
                            labels={"name": "", PREIS_SPALTE: "€/min"})
        fig_balken.update_traces(texttemplate="%{text:.3f}", textposition="outside")
        fig_balken.update_layout(yaxis_title="Preis",
                                 xaxis_tickangle=-25,
                                 showlegend=False,
                                 margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig_balken, use_container_width=True)

        fig_box = px.box(preise_gefiltert, points="all", labels={"value": "€/min"})
        fig_box.update_layout(showlegend=False, margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig_box, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ───── Anbieter‑Details ─────
with tab_details:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Anbieter‑Details")

    if ausgewaehlter_name is None:
        st.info("Wähle einen Anbieter in der Sidebar.")
    else:
        daten = df_gefiltert.set_index("name").loc[ausgewaehlter_name]

        links, rechts = st.columns([2, 1], gap="large")
        with links:
            st.markdown(f"**📍 Firmensitz**\n\n{daten['sitz']}")
            st.markdown("---")
            st.markdown(f"**👥 Kunden / Referenzen**\n\n{daten['kunden']}")
            st.markdown("---")
            st.markdown(f"**💶 Preise & Modelle**\n\n{daten['preise']}")
        with rechts:
            preis_wert = daten[PREIS_SPALTE]
            st.metric("Preis ab", f"{preis_wert:.3f} € / min" if pd.notna(preis_wert) else "—")
    st.markdown("</div>", unsafe_allow_html=True)

# ───── Vergleichstabelle ─────
with tab_tabelle:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Vergleichstabelle")

    if df_gefiltert.empty:
        st.info("Keine Datensätze für die aktuellen Filter.")
    else:
        spalten_auswahl = st.multiselect(
            "Spalten auswählen",
            df_gefiltert.columns.tolist(),
            default=df_gefiltert.columns.tolist(),
        )
        df_tabelle = df_gefiltert[spalten_auswahl]

        if AGGRID_VORHANDEN:
            builder = GridOptionsBuilder.from_dataframe(df_tabelle)
            builder.configure_pagination()
            builder.configure_default_column(filter=True, sortable=True, resizable=True)
            grid = AgGrid(df_tabelle, gridOptions=builder.build(),
                          theme="alpine", fit_columns_on_grid_load=True,
                          height=420)
            df_export = pd.DataFrame(grid["data"])
        else:
            st.dataframe(df_tabelle, use_container_width=True)
            df_export = df_tabelle

        csv_bytes = df_export.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV herunterladen", csv_bytes,
                           "anbieter.csv", "text/csv")

        if EXCEL_VORHANDEN:
            xlsx_bytes = df_export.to_excel(index=False, engine="openpyxl")
            st.download_button("📥 Excel herunterladen", xlsx_bytes,
                               "anbieter.xlsx",
                               mime=("application/vnd.openxmlformats-officedocument."
                                     "spreadsheetml.sheet"))
    st.markdown("</div>", unsafe_allow_html=True)

# ───── Preis­kategorien ─────
with tab_donut:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Preis­kategorien")

    if preise_gefiltert.empty:
        st.info("Keine Preisangaben vorhanden.")
    else:
        eps = 0.01
        maximum = float(preise_gefiltert.max())
        kanten  = [1, 2, 5]
        bins    = [0] + [k for k in kanten if k < maximum] + [maximum + eps]

        etiketten = [f"{bins[i]}–{bins[i+1]} €" for i in range(len(bins)-2)]
        etiketten.append(f"> {bins[-2]} €")

        kategorien = pd.cut(preise_gefiltert, bins=bins, labels=etiketten,
                            include_lowest=True, duplicates="drop")
        df_donut = kategorien.value_counts().rename_axis("Kategorie").reset_index(name="Anzahl")

        fig_donut = px.pie(df_donut, values="Anzahl", names="Kategorie",
                           hole=0.55,
                           color_discrete_sequence=px.colors.sequential.Blues_r)
        fig_donut.update_traces(textposition="inside", textinfo="percent+label")
        fig_donut.update_layout(showlegend=False, margin=dict(t=10,l=10,r=10,b=10))
        st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ────────────── Footer ──────────────
st.markdown(
    '<div style="text-align:center;color:gray;font-size:0.8rem;padding:1rem 0;">'
    '© 2025 • Executive Dashboard – Feel free to extend'
    '</div>',
    unsafe_allow_html=True)
