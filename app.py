
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# =====================================================
# TETAPAN DASHBOARD
# =====================================================

st.set_page_config(
    page_title="AI Fleet Intelligence",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 AI FLEET INTELLIGENCE")
st.caption("Dashboard Analisis Penggunaan dan Kos Kenderaan")

# =====================================================
# BACA DATA
# =====================================================

@st.cache_data
def load_data():
    fail = Path(__file__).parent / "fleet_data.csv"
    df = pd.read_csv(fail, encoding="utf-8-sig")

    # Bersihkan nama kolum
    df.columns = df.columns.str.strip()

    # Pastikan kolum penting wujud
    wajib = ["Kenderaan", "Tahun", "Bulan_No", "Jarak_KM"]
    for kolum in wajib:
        if kolum not in df.columns:
            raise ValueError(f"Kolum '{kolum}' tiada dalam fail CSV.")

    # Tukar jenis data
    df["Tahun"] = pd.to_numeric(df["Tahun"], errors="coerce")
    df["Bulan_No"] = pd.to_numeric(df["Bulan_No"], errors="coerce")

    numeric_cols = [
        "Jarak_KM", "Liter", "kWh", "Kos_Energi_RM",
        "KM_per_Liter", "KM_per_kWh", "Kos_per_KM"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Kenderaan", "Tahun", "Bulan_No"])
    df["Tahun"] = df["Tahun"].astype(int)
    df["Bulan_No"] = df["Bulan_No"].astype(int)

    nama_bulan = {
        1: "Januari", 2: "Februari", 3: "Mac",
        4: "April", 5: "Mei", 6: "Jun",
        7: "Julai", 8: "Ogos", 9: "September",
        10: "Oktober", 11: "November", 12: "Disember"
    }

    df["Bulan"] = df["Bulan_No"].map(nama_bulan)

    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"Ralat membaca data: {e}")
    st.stop()

# =====================================================
# SIDEBAR - PILIHAN PENAPIS
# =====================================================

st.sidebar.header("🔎 Penapis Data")

senarai_tahun = sorted(df["Tahun"].dropna().unique())
pilihan_tahun = st.sidebar.multiselect(
    "Pilih Tahun",
    senarai_tahun,
    default=senarai_tahun
)

df_tahun = df[df["Tahun"].isin(pilihan_tahun)]

senarai_kenderaan = sorted(df_tahun["Kenderaan"].dropna().unique())
pilihan_kenderaan = st.sidebar.multiselect(
    "Pilih Kenderaan",
    senarai_kenderaan,
    default=senarai_kenderaan
)

senarai_bulan = sorted(df_tahun["Bulan_No"].dropna().unique())
pilihan_bulan = st.sidebar.multiselect(
    "Pilih Bulan",
    senarai_bulan,
    default=senarai_bulan,
    format_func=lambda x: {
        1: "Januari", 2: "Februari", 3: "Mac",
        4: "April", 5: "Mei", 6: "Jun",
        7: "Julai", 8: "Ogos", 9: "September",
        10: "Oktober", 11: "November", 12: "Disember"
    }.get(x, str(x))
)

data = df_tahun[
    (df_tahun["Kenderaan"].isin(pilihan_kenderaan)) &
    (df_tahun["Bulan_No"].isin(pilihan_bulan))
].copy()

if data.empty:
    st.warning("Tiada data untuk pilihan penapis ini.")
    st.stop()

# =====================================================
# PENGIRAAN RINGKAS
# =====================================================

jarak = data["Jarak_KM"].sum()

kos = (
    data["Kos_Energi_RM"].sum()
    if "Kos_Energi_RM" in data.columns else 0
)

liter = (
    data["Liter"].sum(min_count=1)
    if "Liter" in data.columns else 0
)

kwh = (
    data["kWh"].sum(min_count=1)
    if "kWh" in data.columns else 0
)

rm_per_km = kos / jarak if jarak > 0 else 0
km_per_liter = jarak / liter if pd.notna(liter) and liter > 0 else None
km_per_kwh = jarak / kwh if pd.notna(kwh) and kwh > 0 else None

# =====================================================
# KPI
# =====================================================

st.subheader("📊 Ringkasan Prestasi")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Jumlah Jarak", f"{jarak:,.0f} KM")
k2.metric("Jumlah Kos Tenaga", f"RM {kos:,.2f}")
k3.metric("Kos Purata", f"RM {rm_per_km:.3f} / KM")
k4.metric("Bilangan Kenderaan", data["Kenderaan"].nunique())

st.divider()

# =====================================================
# CARTA BULANAN
# =====================================================

st.subheader("📈 Analisis Bulanan")

bulanan = (
    data.groupby(["Tahun", "Bulan_No", "Bulan", "Kenderaan"], as_index=False)
    .agg(
        Jumlah_Jarak=("Jarak_KM", "sum"),
        Jumlah_Kos=("Kos_Energi_RM", "sum")
    )
)

bulanan["Tempoh"] = (
    bulanan["Bulan"] + " " + bulanan["Tahun"].astype(str)
)

tab1, tab2 = st.tabs(["Jarak Perjalanan", "Kos Tenaga"])

with tab1:
    fig_jarak = px.bar(
        bulanan,
        x="Tempoh",
        y="Jumlah_Jarak",
        color="Kenderaan",
        barmode="group",
        title="Jarak Perjalanan Mengikut Bulan",
        labels={
            "Tempoh": "Bulan",
            "Jumlah_Jarak": "Jarak (KM)",
            "Kenderaan": "Kenderaan"
        }
    )
    st.plotly_chart(fig_jarak, use_container_width=True)

with tab2:
    fig_kos = px.bar(
        bulanan,
        x="Tempoh",
        y="Jumlah_Kos",
        color="Kenderaan",
        barmode="group",
        title="Kos Tenaga Mengikut Bulan",
        labels={
            "Tempoh": "Bulan",
            "Jumlah_Kos": "Kos (RM)",
            "Kenderaan": "Kenderaan"
        }
    )
    st.plotly_chart(fig_kos, use_container_width=True)

st.divider()

# =====================================================
# PERBANDINGAN KENDERAAN
# =====================================================

st.subheader("🚘 Perbandingan Kecekapan Kenderaan")

perbandingan = (
    data.groupby("Kenderaan", as_index=False)
    .agg(
        Jumlah_Jarak=("Jarak_KM", "sum"),
        Jumlah_Kos=("Kos_Energi_RM", "sum")
    )
)

perbandingan["RM_per_KM"] = (
    perbandingan["Jumlah_Kos"] /
    perbandingan["Jumlah_Jarak"].replace(0, pd.NA)
)

st.dataframe(
    perbandingan.round(3),
    use_container_width=True,
    hide_index=True
)

fig_perbandingan = px.bar(
    perbandingan,
    x="Kenderaan",
    y="RM_per_KM",
    color="Kenderaan",
    title="Kos Tenaga Bagi Setiap Kilometer",
    labels={
        "Kenderaan": "Kenderaan",
        "RM_per_KM": "Kos (RM/KM)"
    }
)
st.plotly_chart(fig_perbandingan, use_container_width=True)

st.divider()

# =====================================================
# AI FLEET ASSISTANT
# =====================================================

st.subheader("🤖 AI Fleet Assistant")
st.write("Tanya soalan ringkas tentang prestasi kenderaan anda.")

soalan = st.text_input(
    "Contoh: Antara City dan Innova, mana paling jimat?"
)

if st.button("Analisis Pertanyaan"):
    if not soalan.strip():
        st.warning("Sila masukkan pertanyaan.")
    else:
        perbandingan_ai = perbandingan.dropna(
            subset=["RM_per_KM"]
        ).sort_values("RM_per_KM")

        if len(perbandingan_ai) == 0:
            st.warning("Data kos bagi perbandingan tidak mencukupi.")
        else:
            terbaik = perbandingan_ai.iloc[0]
            st.success(
                f"Berdasarkan data yang dipilih, "
                f"{terbaik['Kenderaan']} mempunyai kos tenaga "
                f"terendah iaitu RM {terbaik['RM_per_KM']:.3f} bagi setiap KM."
            )
            st.caption(
                "Analisis ini menggunakan kos tenaga yang direkodkan "
                "dalam dataset dan merupakan pembantu berasaskan peraturan."
            )

# =====================================================
# JADUAL DATA
# =====================================================

st.divider()
st.subheader("📋 Rekod Data Terperinci")

st.dataframe(
    data,
    use_container_width=True,
    hide_index=True
)

st.caption("AI Fleet Intelligence | Analisis Data Penggunaan Kenderaan")
