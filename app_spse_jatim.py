import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 1. Konfigurasi Halaman Web
st.set_page_config(
    page_title="Monitor SPSE Jawa Timur Real-Time",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard Pemantau SPSE se-Jawa Timur")
st.markdown("Memantau paket pekerjaan terbaru dari berbagai portal SPSE di Jawa Timur secara terpusat.")

# 2. Daftar URL SPSE Target (Bisa diperluas hingga 39 Kab/Kota se-Jatim)
SPSE_SOURCES = {
    "Kab. Bojonegoro": "https://spse.inaproc.id/bojonegorokab/lelang",
    "Kab. Tuban": "https://spse.inaproc.id/tubankab/lelang",
    "Kob. Blora": "https://spse.inaproc.id/blorakab/lelang
}

# 3. Fungsi untuk Mengambil Data dari SPSE
@st.cache_data(ttl=300) # Cache data selama 5 menit agar tidak membebani server SPSE
def fetch_spse_data():
    all_packages = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }

    for region, url in SPSE_SOURCES.items():
        try:
            # Catatan: SPSE modern menggunakan AJAX Datatables. 
            # Pada implementasi skala penuh, gunakan endpoint API JSON (/eproc4/dt/lelang) untuk penarikan ribuan data.
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                rows = soup.find_all('tr', class_=['odd', 'even'])
                
                for row in rows[:10]: # Mengambil 10 paket terbaru per wilayah
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        nama_paket = cols[1].text.strip()
                        tahapan = cols[3].text.strip() if len(cols) > 3 else "Aktif"
                        
                        all_packages.append({
                            "Wilayah / SPSE": region,
                            "Nama Paket Pekerjaan": nama_paket,
                            "Tahapan Saat Ini": tahapan,
                            "Link Portal": url
                        })
        except Exception:
            continue
            
    return pd.DataFrame(all_packages)

# 4. Tombol Refresh & Indikator Status
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 Refresh Data Sekarang"):
        st.cache_data.clear()
with col2:
    st.caption(f"Terakhir diperbarui: {time.strftime('%H:%M:%S')} WIB (Otomatis diperbarui setiap 5 menit)")

# 5. Load Data
with st.spinner("Sedang menarik data terbaru dari server SPSE se-Jawa Timur..."):
    df = fetch_spse_data()

# 6. Fitur Filter & Pencarian
if not df.empty:
    st.subheader("🔍 Filter & Cari Paket")
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        selected_region = st.multiselect(
            "Pilih Wilayah SPSE:", 
            options=df["Wilayah / SPSE"].unique(),
            default=df["Wilayah / SPSE"].unique()
        )
        
    with col_filter2:
        search_keyword = st.text_input("Cari Kata Kunci Paket (contoh: Jalan, Gedung, Obat, Konsultansi):", "")
    
    # Terapkan Filter
    filtered_df = df[df["Wilayah / SPSE"].isin(selected_region)]
    if search_keyword:
        filtered_df = filtered_df[filtered_df["Nama Paket Pekerjaan"].str.contains(search_keyword, case=False, na=False)]
    
    # 7. Tampilkan Tabel Data
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )
    
    # 8. Download Data ke Excel/CSV
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data (CSV)",
        data=csv,
        file_name='paket_spse_jatim.csv',
        mime='text/csv',
    )
else:
    st.warning("Data belum berhasil ditarik. Pastikan koneksi internet stabil atau coba tekan tombol Refresh.")
