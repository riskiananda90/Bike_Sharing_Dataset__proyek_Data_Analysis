import streamlit as st
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Pengaturan backend non-GUI
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# Konfigurasi halaman dengan tema yang lebih menarik
st.set_page_config(
    page_title="Dashboard Penyewaan Sepeda",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Menambahkan CSS untuk mempercantik tampilan
st.markdown("""
<style>
    .main-header {
        font-size: 36px;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #1E88E5;
    }
    .sub-header {
        font-size: 24px;
        font-weight: bold;
        color: #43A047;
        margin-top: 30px;
        margin-bottom: 15px;
    }
    .highlight {
        background-color: #f0f7ff;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #1E88E5;
    }
    .metric-card {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stPlotlyChart {
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        border-radius: 5px;
        padding: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Fungsi untuk memuat dan mempersiapkan data dengan caching
@st.cache_data
def load_data():
    """
    Fungsi untuk memuat dan mempersiapkan data.
    Menggunakan cache untuk meningkatkan performa.
    """
    # Baca data dari file CSV
    base_path = "Dashboard"
    day_df = pd.read_csv(os.path.join(base_path, "day_df.csv"))
    hour_df = pd.read_csv(os.path.join(base_path, "hour_df.csv"))
    
    # Hapus kolom yang tidak diperlukan
    for df in [day_df, hour_df]:
        df.drop(['workingday'], axis=1, inplace=True)
    
    # Ubah tipe data kolom kategori
    kategori_kolom = ['season', 'mnth', 'holiday', 'weekday', 'weathersit']
    for df in [day_df, hour_df]:
        for col in kategori_kolom:
            df[col] = df[col].astype("category")
    
    # Konversi kolom tanggal ke tipe datetime
    for df in [day_df, hour_df]:
        df['dteday'] = pd.to_datetime(df['dteday'])
    
    # Ganti nama kolom untuk meningkatkan keterbacaan
    rename_dict = {
        'yr': 'year',
        'mnth': 'month',
        'weekday': 'day_of_week',
        'weathersit': 'weather_situation',
        'windspeed': 'wind_speed',
        'cnt': 'total_rentals',
        'hum': 'humidity',
        'temp': 'temperature',
        'casual': 'casual_users',
        'registered': 'registered_users'
    }
    day_df.rename(columns=rename_dict, inplace=True)
    hour_df.rename(columns={**rename_dict, 'hr': 'hour'}, inplace=True)
    
    # Buat pemetaan untuk nilai kategori
    mapping_dict = {
        'season': {1: 'Spring', 2: 'Summer', 3: 'Fall', 4: 'Winter'},
        'month': {i: month for i, month in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)},
        'weather_situation': {1: 'Cerah', 2: 'Berkabut', 3: 'Hujan/Salju Ringan', 4: 'Hujan/Salju Lebat'},
        'day_of_week': {0: 'Minggu', 1: 'Senin', 2: 'Selasa', 3: 'Rabu',
                        4: 'Kamis', 5: 'Jumat', 6: 'Sabtu'},
        'year': {0: '2011', 1: '2012'},
        'holiday': {0: 'Hari Biasa', 1: 'Hari Libur'}
    }
    
    # Terapkan pemetaan ke data
    for col, mapping in mapping_dict.items():
        # Pastikan kolom bertipe kategori
        if col in day_df.columns:
            if not isinstance(day_df[col].dtype, pd.CategoricalDtype):
                day_df[col] = day_df[col].astype("category")
            day_df[col] = day_df[col].cat.rename_categories(mapping)

        if col in hour_df.columns:
            if not isinstance(hour_df[col].dtype, pd.CategoricalDtype):
                hour_df[col] = hour_df[col].astype("category")
            hour_df[col] = hour_df[col].cat.rename_categories(mapping)


    
    # Fungsi untuk mengkategorikan hari (Weekday/Weekend)
    def categorize_day(day):
        return "Akhir Pekan" if day in ["Sabtu", "Minggu"] else "Hari Kerja"
    
    # Terapkan kategorisasi hari
    for df in [day_df, hour_df]:
        df["day_category"] = df["day_of_week"].apply(categorize_day)
    
    # Fungsi untuk mengkategorikan kelembaban
    def categorize_humidity(hum):
        if hum < 45:
            return "Kering"
        elif hum < 65:
            return "Ideal"
        else:
            return "Lembab"
    
    # Terapkan kategorisasi kelembaban
    for df in [day_df, hour_df]:
        df["humidity_category"] = df["humidity"].apply(categorize_humidity)
    
    # Fungsi untuk mengkategorikan suhu
    def categorize_temperature(temp):
        # Mengkonversi suhu normalisasi ke Celsius (temp * 41)
        temp_celsius = temp * 41
        if temp_celsius < 15:
            return "Dingin"
        elif temp_celsius < 25:
            return "Nyaman"
        else:
            return "Panas"
    
    # Terapkan kategorisasi suhu
    for df in [day_df, hour_df]:
        df["temperature_category"] = df["temperature"].apply(categorize_temperature)
        # Menambahkan kolom suhu dalam Celsius untuk visualisasi yang lebih jelas
        df["temperature_celsius"] = df["temperature"] * 41
    
    return day_df, hour_df

# Muat data
day_df, hour_df = load_data()

# Sidebar untuk filter
st.sidebar.markdown("## 🔍 Filter Data")
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2972/2972185.png", width=100)
    
    # Filter tahun
    tahun = st.selectbox("Pilih Tahun", ['Semua', '2011', '2012'])
    filtered_day_df = day_df
    filtered_hour_df = hour_df
    
    if tahun != 'Semua':
        filtered_day_df = filtered_day_df[filtered_day_df['year'] == tahun]
        filtered_hour_df = filtered_hour_df[filtered_hour_df['year'] == tahun]
    
    # Filter musim
    musim = st.selectbox("Pilih Musim", ['Semua', 'Spring', 'Summer', 'Fall', 'Winter'])
    if musim != 'Semua':
        filtered_day_df = filtered_day_df[filtered_day_df['season'] == musim]
        filtered_hour_df = filtered_hour_df[filtered_hour_df['season'] == musim]
    
    # Filter tipe hari
    tipe_hari = st.selectbox("Pilih Tipe Hari", ['Semua', 'Hari Kerja', 'Akhir Pekan'])
    if tipe_hari != 'Semua':
        filtered_day_df = filtered_day_df[filtered_day_df['day_category'] == tipe_hari]
        filtered_hour_df = filtered_hour_df[filtered_hour_df['day_category'] == tipe_hari]
    
    # Filter cuaca
    cuaca = st.selectbox("Pilih Cuaca", ['Semua', 'Cerah', 'Berkabut', 'Hujan/Salju Ringan', 'Hujan/Salju Lebat'])
    if cuaca != 'Semua':
        filtered_day_df = filtered_day_df[filtered_day_df['weather_situation'] == cuaca]
        filtered_hour_df = filtered_hour_df[filtered_hour_df['weather_situation'] == cuaca]
    
    # Filter bulan
    bulan_options = ['Semua'] + sorted(day_df['month'].unique().tolist())
    bulan = st.selectbox("Pilih Bulan", bulan_options)
    if bulan != 'Semua':
        filtered_day_df = filtered_day_df[filtered_day_df['month'] == bulan]
        filtered_hour_df = filtered_hour_df[filtered_hour_df['month'] == bulan]
    
    # Tombol untuk mereset filter
    if st.button("Reset Filter"):
        tahun = 'Semua'
        musim = 'Semua'
        tipe_hari = 'Semua'
        cuaca = 'Semua'
        bulan = 'Semua'
        filtered_day_df = day_df
        filtered_hour_df = hour_df

# Judul utama dashboard
st.markdown('<div class="main-header">🚲 Dashboard Penyewaan Sepeda</div>', unsafe_allow_html=True)
st.markdown("""
<div class="highlight">
    <p>Analisis komprehensif data penyewaan sepeda berdasarkan berbagai faktor seperti musim, cuaca, waktu, dan kondisi lingkungan.</p>
</div>
""", unsafe_allow_html=True)

# Menampilkan periode data yang difilter
min_date = filtered_day_df['dteday'].min().strftime('%d %B %Y')
max_date = filtered_day_df['dteday'].max().strftime('%d %B %Y')
st.markdown(f"**Periode Data:** {min_date} - {max_date}")

# Metrik utama dalam kartu
st.markdown('<div class="sub-header">📊 Metrik Utama</div>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    total_rentals = filtered_day_df['total_rentals'].sum()
    st.metric("Total Penyewaan", f"{total_rentals:,}")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    daily_avg = filtered_day_df['total_rentals'].mean()
    st.metric("Rata-rata per Hari", f"{daily_avg:,.0f}")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    if not filtered_day_df.empty:
        max_day = filtered_day_df.loc[filtered_day_df['total_rentals'].idxmax()]
        st.metric("Penyewaan Tertinggi", f"{int(max_day['total_rentals']):,}", 
                  f"{max_day['dteday'].strftime('%d %b %Y')}")
    else:
        st.metric("Penyewaan Tertinggi", "Tidak ada data")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    if not filtered_day_df.empty:
        min_day = filtered_day_df.loc[filtered_day_df['total_rentals'].idxmin()]
        st.metric("Penyewaan Terendah", f"{int(min_day['total_rentals']):,}", 
                  f"{min_day['dteday'].strftime('%d %b %Y')}")
    else:
        st.metric("Penyewaan Terendah", "Tidak ada data")
    st.markdown('</div>', unsafe_allow_html=True)

# Tampilkan proporsi pengguna terdaftar vs casual
st.markdown('<div class="sub-header">👥 Proporsi Pengguna</div>', unsafe_allow_html=True)
if not filtered_day_df.empty:
    registered_sum = filtered_day_df['registered_users'].sum()
    casual_sum = filtered_day_df['casual_users'].sum()
    total_sum = registered_sum + casual_sum
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.pie([registered_sum, casual_sum], 
           labels=['Pengguna Terdaftar', 'Pengguna Casual'],
           autopct='%1.1f%%',
           colors=['#1E88E5', '#FFC107'],
           startangle=90,
           explode=(0.05, 0))
    ax.set_title('Proporsi Jenis Pengguna')
    st.pyplot(fig)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Pengguna Terdaftar", f"{registered_sum:,}", 
                 f"{registered_sum/total_sum:.1%}")
    with col2:
        st.metric("Total Pengguna Casual", f"{casual_sum:,}", 
                 f"{casual_sum/total_sum:.1%}")

# Grafik penyewaan berdasarkan jam
st.markdown('<div class="sub-header">⏰ Jumlah Penyewaan Berdasarkan Jam</div>', unsafe_allow_html=True)
if not filtered_hour_df.empty:
    hourly_count = filtered_hour_df.groupby('hour')['total_rentals'].sum().reset_index()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(x='hour', y='total_rentals', data=hourly_count, ax=ax, 
                marker='o', linewidth=3, color='#1E88E5')
    
    ax.set_xlabel("Jam", fontsize=12)
    ax.set_ylabel("Jumlah Penyewaan", fontsize=12)
    ax.set_title("Tren Penyewaan Sepeda Sepanjang Hari", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.fill_between(hourly_count['hour'], hourly_count['total_rentals'], alpha=0.3, color='#1E88E5')
    
    # Tambahkan penanda untuk jam tersibuk
    max_hour = hourly_count.loc[hourly_count['total_rentals'].idxmax()]
    ax.annotate(f'Jam tersibuk: {int(max_hour["hour"])}:00 ({int(max_hour["total_rentals"]):,})',
                xy=(max_hour['hour'], max_hour['total_rentals']),
                xytext=(max_hour['hour'], max_hour['total_rentals']*1.1),
                arrowprops=dict(facecolor='black', shrink=0.05, alpha=0.7),
                fontsize=10, ha='center')
    
    st.pyplot(fig)
    
    # Tampilkan insight tentang jam tersibuk
    st.markdown(f"""
    <div class="highlight">
        <p>💡 <strong>Insight:</strong> Jam tersibuk adalah pukul <strong>{int(max_hour["hour"])}:00</strong> dengan total penyewaan mencapai <strong>{int(max_hour["total_rentals"]):,}</strong> sepeda.</p>
    </div>
    """, unsafe_allow_html=True)

# Perbandingan hari kerja vs akhir pekan
st.markdown('<div class="sub-header">📌 Perbandingan Penyewaan: Hari Kerja vs Akhir Pekan</div>', unsafe_allow_html=True)
if not filtered_day_df.empty:
    # Analisis berdasarkan kategori hari
    day_category_count = filtered_day_df.groupby("day_category")["total_rentals"].sum().reset_index()
    
    # Hitung rata-rata per hari untuk perbandingan yang lebih adil
    day_category_avg = filtered_day_df.groupby("day_category").agg(
        total_rentals=('total_rentals', 'sum'),
        count=('dteday', 'count')
    ).reset_index()
    day_category_avg['avg_rentals'] = day_category_avg['total_rentals'] / day_category_avg['count']
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x="day_category", y="total_rentals", data=day_category_count, ax=ax, palette="coolwarm", hue="day_category", legend=False)
        ax.set_xlabel("Kategori Hari", fontsize=12)
        ax.set_ylabel("Total Penyewaan", fontsize=12)
        ax.set_title("Total Penyewaan Berdasarkan Kategori Hari", fontsize=14)
        
        # Tambahkan nilai di atas bar chart
        for p in ax.patches:
            ax.annotate(f'{int(p.get_height()):,}', 
                     (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha='center', va='bottom', fontsize=12)
        
        st.pyplot(fig)
    
    with col2:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.barplot(x="day_category", y="avg_rentals", data=day_category_avg, ax=ax, palette="viridis")
        ax.set_xlabel("Kategori Hari", fontsize=12)
        ax.set_ylabel("Rata-rata Penyewaan per Hari", fontsize=12)
        ax.set_title("Rata-rata Penyewaan per Kategori Hari", fontsize=14)
        
        # Tambahkan nilai di atas bar chart
        for p in ax.patches:
            ax.annotate(f'{int(p.get_height()):,}', 
                     (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha='center', va='bottom', fontsize=12)
        
        st.pyplot(fig)
    
    # Tampilkan insight berdasarkan data
    if len(day_category_count) > 1:
        weekday_rentals = day_category_count[day_category_count["day_category"] == "Hari Kerja"]["total_rentals"].values[0]
        weekend_rentals = day_category_count[day_category_count["day_category"] == "Akhir Pekan"]["total_rentals"].values[0]
        
        weekday_avg = day_category_avg[day_category_avg["day_category"] == "Hari Kerja"]["avg_rentals"].values[0]
        weekend_avg = day_category_avg[day_category_avg["day_category"] == "Akhir Pekan"]["avg_rentals"].values[0]
        
        if weekday_rentals > weekend_rentals:
            st.markdown(f"""
            <div class="highlight">
                <p>✅ <strong>Hasil:</strong> Total penyewaan lebih tinggi pada <strong>hari kerja ({weekday_rentals:,})</strong> dibandingkan akhir pekan ({weekend_rentals:,}).</p>
                <p>Namun, rata-rata penyewaan per hari {"lebih tinggi" if weekend_avg > weekday_avg else "lebih rendah"} pada <strong>akhir pekan ({weekend_avg:,.0f})</strong> dibandingkan hari kerja ({weekday_avg:,.0f}).</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="highlight">
                <p>✅ <strong>Hasil:</strong> Total penyewaan lebih tinggi pada <strong>akhir pekan ({weekend_rentals:,})</strong> dibandingkan hari kerja ({weekday_rentals:,}).</p>
                <p>Rata-rata penyewaan per hari juga {"lebih tinggi" if weekend_avg > weekday_avg else "lebih rendah"} pada <strong>akhir pekan ({weekend_avg:,.0f})</strong> dibandingkan hari kerja ({weekday_avg:,.0f}).</p>
            </div>
            """, unsafe_allow_html=True)

# Analisis berdasarkan musim
st.markdown('<div class="sub-header">🍂 Penyewaan Berdasarkan Musim</div>', unsafe_allow_html=True)
if not filtered_day_df.empty:
    # Mengelompokkan data berdasarkan musim
    season_rentals = filtered_day_df.groupby('season', observed=False)['total_rentals'].sum().reset_index()
    
    # Hitung rata-rata per hari untuk setiap musim
    season_avg = filtered_day_df.groupby('season').agg(
        total_rentals=('total_rentals', 'sum'),
        count=('dteday', 'count')
    ).reset_index()
    season_avg['avg_rentals'] = season_avg['total_rentals'] / season_avg['count']
    
    # Visualisasi
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Total rentals by season
    palette = {'Spring': '#78C850', 'Summer': '#F08030', 'Fall': '#F8D030', 'Winter': '#98D8D8'}
    sns.barplot(x='season', y='total_rentals', data=season_rentals, palette=palette, ax=axes[0])
    axes[0].set_title('Total Penyewaan Berdasarkan Musim', fontsize=14)
    axes[0].set_xlabel('Musim', fontsize=12)
    axes[0].set_ylabel('Total Penyewaan', fontsize=12)
    
    # Tambahkan nilai di atas bar chart
    for p in axes[0].patches:
        axes[0].annotate(f'{int(p.get_height()):,}', 
                     (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha='center', va='bottom', fontsize=10)
    
    # Average rentals by season
    sns.barplot(x='season', y='avg_rentals', data=season_avg, palette=palette, ax=axes[1])
    axes[1].set_title('Rata-rata Penyewaan Harian Berdasarkan Musim', fontsize=14)
    axes[1].set_xlabel('Musim', fontsize=12)
    axes[1].set_ylabel('Rata-rata Penyewaan per Hari', fontsize=12)
    
    # Tambahkan nilai di atas bar chart
    for p in axes[1].patches:
        axes[1].annotate(f'{int(p.get_height()):,}', 
                     (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Temukan musim dengan penyewaan tertinggi
    top_season = season_rentals.loc[season_rentals['total_rentals'].idxmax()]
    top_avg_season = season_avg.loc[season_avg['avg_rentals'].idxmax()]
    
    st.markdown(f"""
    <div class="highlight">
        <p>🌟 <strong>Insight:</strong> Musim dengan total penyewaan tertinggi adalah <strong>{top_season['season']}</strong> dengan total {int(top_season['total_rentals']):,} penyewaan.</p>
        <p>Musim dengan rata-rata penyewaan harian tertinggi adalah <strong>{top_avg_season['season']}</strong> dengan rata-rata {int(top_avg_season['avg_rentals']):,} penyewaan per hari.</p>
    </div>
    """, unsafe_allow_html=True)

# Analisis berdasarkan cuaca
st.markdown('<div class="sub-header">🌤️ Pengaruh Cuaca Terhadap Penyewaan</div>', unsafe_allow_html=True)
if not filtered_day_df.empty:
    # Mengelompokkan data berdasarkan situasi cuaca
    weather_rentals = filtered_day_df.groupby('weather_situation')['total_rentals'].mean().reset_index()
    weather_rentals = weather_rentals.sort_values('total_rentals', ascending=False)
    
    # Visualisasi
    fig, ax = plt.subplots(figsize=(10, 6))
    palette = {'Cerah': '#FFD700', 'Berkabut': '#A9A9A9', 'Hujan/Salju Ringan': '#87CEFA', 'Hujan/Salju Lebat': '#4169E1'}
    colors = [palette.get(weather, '#333333') for weather in weather_rentals['weather_situation']]
    
    bars = ax.bar(weather_rentals['weather_situation'], weather_rentals['total_rentals'], color=colors)
    ax.set_title('Rata-rata Penyewaan Berdasarkan Kondisi Cuaca', fontsize=14)
    ax.set_xlabel('Kondisi Cuaca', fontsize=12)
    ax.set_ylabel('Rata-rata Penyewaan', fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    
    # Tambahkan nilai di atas bar chart
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{int(height):,}', ha='center', va='bottom', fontsize=10)
    
    st.pyplot(fig)
    
    # Analisis korelasi cuaca dengan penyewaan
    best_weather = weather_rentals.iloc[0]
    worst_weather = weather_rentals.iloc[-1]
    
    st.markdown(f"""
    <div class="highlight">
        <p>☀️ <strong>Insight:</strong> Kondisi cuaca yang paling mendukung penyewaan sepeda adalah <strong>{best_weather['weather_situation']}</strong> dengan rata-rata {int(best_weather['total_rentals']):,} penyewaan.</p>
        <p>Sedangkan kondisi cuaca <strong>{worst_weather['weather_situation']}</strong> memiliki rata-rata penyewaan terendah ({int(worst_weather['total_rentals']):,} penyewaan).</p>
    </div>
    """, unsafe_allow_html=True)

# Analisis berdasarkan kelembaban
st.markdown('<div class="sub-header">💧 Pengaruh Kelembaban Terhadap Penyewaan</div>', unsafe_allow_html=True)
if not filtered_day_df.empty:
    # Mengelompokkan data berdasarkan kategori kelembaban
    humidity_rentals = filtered_day_df.groupby('humidity_category')['total_rentals'].mean().reset_index()
    
    # Visualisasi
    fig, ax = plt.subplots(figsize=(10, 6))
    palette = {'Kering': '#FFA07A', 'Ideal': '#98FB98', 'Lembab': '#87CEFA'}
    sns.barplot(x='humidity_category', y='total_rentals', data=humidity_rentals, palette=palette, ax=ax)
    ax.set_title('Rata-rata Penyewaan Berdasarkan Tingkat Kelembaban', fontsize=14)
    ax.set_xlabel('Kategori Kelembaban', fontsize=12)
    ax.set_ylabel('Rata-rata Penyewaan', fontsize=12)
    
    # Tambahkan nilai di atas bar chart
    for p in ax.patches:
        ax.annotate(f'{int(p.get_height()):,}', 
                 (p.get_x() + p.get_width() / 2., p.get_height()),
                 ha='center', va='bottom', fontsize=10)
    
    st.pyplot(fig)
    
    # Analisis korelasi kelembaban dengan penyewaan
    best_humidity = humidity_rentals.loc[humidity_rentals['total_rentals'].idxmax()]
    
    st.markdown(f"""
    <div class="highlight">
        <p>💧 <strong>Insight:</strong> Tingkat kelembaban <strong>{best_humidity['humidity_category']}</strong> adalah kondisi paling baik untuk penyewaan sepeda dengan rata-rata {int(best_humidity['total_rentals']):,} penyewaan.</p>
    </div>
    """, unsafe_allow_html=True)

# Tren penyewaan sepanjang waktu
# Tren penyewaan sepanjang waktu
st.markdown('<div class="sub-header">📈 Tren Penyewaan Sepanjang Waktu</div>', unsafe_allow_html=True)
if not filtered_day_df.empty:
    # Mengagregasi data berdasarkan tanggal
    daily_rentals = filtered_day_df.groupby('dteday')['total_rentals'].sum().reset_index()
    
    # Visualisasi tren penyewaan harian
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(daily_rentals['dteday'], daily_rentals['total_rentals'], marker='', linewidth=2, color='#1E88E5')
    ax.set_title('Tren Jumlah Penyewaan Sepeda Harian', fontsize=14)
    ax.set_xlabel('Tanggal', fontsize=12)
    ax.set_ylabel('Jumlah Penyewaan', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Tambahkan garis trend (moving average)
    ma_window = min(7, len(daily_rentals))  # Menggunakan moving average 7 hari jika data mencukupi
    if ma_window > 1:
        daily_rentals['moving_avg'] = daily_rentals['total_rentals'].rolling(window=ma_window).mean()
        ax.plot(daily_rentals['dteday'], daily_rentals['moving_avg'], color='red', linewidth=2, linestyle='--', label=f'Rata-rata Bergerak ({ma_window} hari)')
        ax.legend()
    
    # Format sumbu x untuk mengurangi kesesakan
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig)
    
    # Analisis trend
    if len(daily_rentals) > 10:
        first_half = daily_rentals.iloc[:len(daily_rentals)//2]['total_rentals'].mean()
        second_half = daily_rentals.iloc[len(daily_rentals)//2:]['total_rentals'].mean()
        trend_direction = "meningkat" if second_half > first_half else "menurun"
        trend_percentage = abs(second_half - first_half) / first_half * 100
        
        st.markdown(f"""
        <div class="highlight">
            <p>📊 <strong>Analisis Tren:</strong> Penyewaan sepeda menunjukkan tren yang <strong>{trend_direction}</strong> sebesar {trend_percentage:.1f}% selama periode yang dipilih.</p>
        </div>
        """, unsafe_allow_html=True)

# Analisis berdasarkan hari dalam seminggu
st.markdown('<div class="sub-header">📆 Penyewaan Berdasarkan Hari dalam Seminggu</div>', unsafe_allow_html=True)
if not filtered_day_df.empty:
    # Mengelompokkan data berdasarkan hari dalam seminggu
    weekday_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    weekday_rentals = filtered_day_df.groupby('day_of_week')['total_rentals'].mean().reset_index()
    
    # Mengkonversi DataFrame ke format yang diinginkan dengan urutan hari yang benar
    weekday_rentals['day_of_week'] = pd.Categorical(weekday_rentals['day_of_week'], categories=weekday_order, ordered=True)
    weekday_rentals = weekday_rentals.sort_values('day_of_week')
    
    # Visualisasi
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(weekday_rentals['day_of_week'], weekday_rentals['total_rentals'], 
             color=['#1E88E5' if day in ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat'] else '#FFC107' for day in weekday_rentals['day_of_week']])
    
    ax.set_title('Rata-rata Penyewaan Berdasarkan Hari dalam Seminggu', fontsize=14)
    ax.set_xlabel('Hari', fontsize=12)
    ax.set_ylabel('Rata-rata Penyewaan', fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    
    # Tambahkan nilai di atas bar chart
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{int(height):,}', ha='center', va='bottom', fontsize=10)
    
    st.pyplot(fig)
    
    # Analisis hari dengan penyewaan tertinggi dan terendah
    top_day = weekday_rentals.loc[weekday_rentals['total_rentals'].idxmax()]
    bottom_day = weekday_rentals.loc[weekday_rentals['total_rentals'].idxmin()]
    
    st.markdown(f"""
    <div class="highlight">
        <p>📌 <strong>Insight:</strong> Hari dengan rata-rata penyewaan tertinggi adalah <strong>{top_day['day_of_week']}</strong> ({int(top_day['total_rentals']):,} penyewaan).</p>
        <p>Sedangkan hari dengan rata-rata penyewaan terendah adalah <strong>{bottom_day['day_of_week']}</strong> ({int(bottom_day['total_rentals']):,} penyewaan).</p>
    </div>
    """, unsafe_allow_html=True)

# Analisis berdasarkan jam dan hari dalam seminggu
st.markdown('<div class="sub-header">🕒 Pola Penyewaan Berdasarkan Jam dan Hari</div>', unsafe_allow_html=True)
if not filtered_hour_df.empty:
    # Membuat pivot table untuk pola penyewaan berdasarkan jam dan hari
    heatmap_data = filtered_hour_df.pivot_table(observed=False,
        index='hour', 
        columns='day_of_week', 
        values='total_rentals', 
        aggfunc='mean'
    ).reindex(columns=weekday_order)
    
    # Visualisasi heatmap
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(heatmap_data, cmap='viridis', ax=ax, annot=False, fmt='.0f', cbar_kws={'label': 'Rata-rata Penyewaan'})
    ax.set_title('Pola Penyewaan Berdasarkan Jam dan Hari dalam Seminggu', fontsize=14)
    ax.set_xlabel('Hari', fontsize=12)
    ax.set_ylabel('Jam', fontsize=12)
    
    st.pyplot(fig)
    
    # Menentukan jam tersibuk untuk setiap hari
    busiest_hours = heatmap_data.idxmax()
    busiest_hours_df = pd.DataFrame({'Hari': busiest_hours.index, 'Jam Tersibuk': busiest_hours.values})
    
    st.markdown("""
    <div class="highlight">
        <p>⏰ <strong>Insight:</strong> Pola penyewaan sepeda menunjukkan tren yang jelas berdasarkan jam dan hari dalam seminggu.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tampilkan jam tersibuk untuk setiap hari
    st.write("##### Jam Tersibuk untuk Setiap Hari:")
    for day, hour in zip(busiest_hours.index, busiest_hours.values):
        st.markdown(f"* **{day}**: {int(hour)}:00 WIB")

# Analisis hubungan antara suhu dan penyewaan
st.markdown('<div class="sub-header">🌡️ Pengaruh Suhu Terhadap Penyewaan</div>', unsafe_allow_html=True)
if not filtered_day_df.empty:
    # Scatter plot untuk melihat hubungan antara suhu dan jumlah penyewaan
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(x='temperature_celsius', y='total_rentals', data=filtered_day_df, alpha=0.6, hue='season', ax=ax)
    
    # Tambahkan garis trend (regresi)
    sns.regplot(x='temperature_celsius', y='total_rentals', data=filtered_day_df, 
                scatter=False, ax=ax, line_kws={"color": "red", "alpha": 0.7, "lw": 2})
    
    ax.set_title('Hubungan Antara Suhu dan Jumlah Penyewaan', fontsize=14)
    ax.set_xlabel('Suhu (°C)', fontsize=12)
    ax.set_ylabel('Jumlah Penyewaan', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Hitung korelasi
    correlation = filtered_day_df['temperature_celsius'].corr(filtered_day_df['total_rentals'])
    
    st.pyplot(fig)
    
    # Analisis korelasi
    if correlation > 0.5:
        correlation_strength = "kuat positif"
    elif correlation > 0.3:
        correlation_strength = "sedang positif"
    elif correlation > 0:
        correlation_strength = "lemah positif"
    elif correlation > -0.3:
        correlation_strength = "lemah negatif"
    elif correlation > -0.5:
        correlation_strength = "sedang negatif"
    else:
        correlation_strength = "kuat negatif"
    
    st.markdown(f"""
    <div class="highlight">
        <p>🌡️ <strong>Insight:</strong> Terdapat korelasi <strong>{correlation_strength}</strong> antara suhu dan jumlah penyewaan sepeda (koefisien korelasi: {correlation:.2f}).</p>
        <p>Hal ini menunjukkan bahwa {"semakin tinggi suhu, semakin banyak penyewaan sepeda" if correlation > 0 else "semakin rendah suhu, semakin banyak penyewaan sepeda"}.</p>
    </div>
    """, unsafe_allow_html=True)

# Analisis perbandingan tahun
if 'year' in filtered_day_df.columns and len(filtered_day_df['year'].unique()) > 1:
    st.markdown('<div class="sub-header">📊 Perbandingan Penyewaan Antar Tahun</div>', unsafe_allow_html=True)
    
    # Mengelompokkan data berdasarkan tahun dan bulan
    yearly_monthly = filtered_day_df.groupby(['year', 'month'])['total_rentals'].sum().reset_index()
    
    # Pivot table untuk visualisasi yang lebih baik
    pivot_data = yearly_monthly.pivot(index='month', columns='year', values='total_rentals')
    
    # Visualisasi
    fig, ax = plt.subplots(figsize=(12, 6))
    pivot_data.plot(kind='bar', ax=ax)
    ax.set_title('Perbandingan Penyewaan Sepeda per Bulan Antar Tahun', fontsize=14)
    ax.set_xlabel('Bulan', fontsize=12)
    ax.set_ylabel('Total Penyewaan', fontsize=12)
    ax.legend(title='Tahun')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Analisis pertumbuhan
    growth_by_year = filtered_day_df.groupby('year')['total_rentals'].sum()
    if len(growth_by_year) > 1:
        years = growth_by_year.index.tolist()
        growth_rate = (growth_by_year[years[1]] - growth_by_year[years[0]]) / growth_by_year[years[0]] * 100
        
        st.markdown(f"""
        <div class="highlight">
            <p>📈 <strong>Insight:</strong> Terdapat {"pertumbuhan" if growth_rate > 0 else "penurunan"} sebesar <strong>{abs(growth_rate):.1f}%</strong> dalam jumlah penyewaan sepeda dari tahun {years[0]} ke tahun {years[1]}.</p>
        </div>
        """, unsafe_allow_html=True)

# Kesimpulan dan Rekomendasi
st.markdown('<div class="sub-header">🎯 Kesimpulan dan Rekomendasi</div>', unsafe_allow_html=True)

# Buat kesimpulan berdasarkan data yang telah dianalisis
import streamlit as st

import streamlit as st

# Tambahkan CSS ke dalam Streamlit
st.markdown("""
    <style>
        /* Gaya untuk kotak highlight */
        .highlight {
            background-color: #f9f9f9;
            color: #555;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #4CAF50;
            margin-bottom: 20px;
        }

        /* Gaya untuk judul kecil */
        h4 {
            color: #333;
            text-align: center;
        }

        /* Gaya untuk daftar */
        ol {
            padding-left: 20px;
        }

        /* Gaya untuk footer */
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            border-top: 2px solid #ccc;
            background-color: #f9f9f9;
            border-radius: 10px;
        }

        .footer p {
            margin: 5px;
            font-size: 14px;
            color: #555;
        }
    </style>
""", unsafe_allow_html=True)

# Gunakan class CSS di dalam HTML
st.markdown("""
<div class="highlight">
    <h4>Kesimpulan:</h4>
    <ol>
        <li>Pola penyewaan sepeda menunjukkan tren yang jelas berdasarkan waktu (jam dan hari), musim, dan kondisi cuaca.</li>
        <li>Faktor cuaca dan suhu memiliki pengaruh signifikan terhadap jumlah penyewaan sepeda.</li>
        <li>Terdapat perbedaan pola penyewaan antara hari kerja dan akhir pekan, yang menunjukkan perbedaan perilaku pengguna.</li>
    </ol>
</div>

<div class="highlight">
    <h4>Rekomendasi:</h4>
    <ol>
        <li><strong>Manajemen Armada:</strong> Sesuaikan jumlah sepeda yang tersedia berdasarkan jam sibuk dan hari dalam seminggu.</li>
        <li><strong>Promosi:</strong> Lakukan promosi khusus pada musim atau kondisi cuaca yang biasanya memiliki jumlah penyewaan rendah.</li>
        <li><strong>Perawatan:</strong> Jadwalkan pemeliharaan armada sepeda pada waktu-waktu dengan aktivitas penyewaan yang rendah.</li>
        <li><strong>Prediksi Permintaan:</strong> Gunakan data historis dan prakiraan cuaca untuk memprediksi permintaan di masa mendatang.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <p>📊 <strong>Dashboard Penyewaan Sepeda</strong> &copy; 2025</p>
    <p>Created with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
