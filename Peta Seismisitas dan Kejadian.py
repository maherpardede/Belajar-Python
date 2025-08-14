import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
from matplotlib.gridspec import GridSpec

# Baca CSV
df = pd.read_csv("datagempantt.csv")
df.columns = df.columns.str.strip()
df["time"] = pd.to_datetime(df["time"])

lon = df["longitude"]
lat = df["latitude"]
mag = df["mag"]
depth = df["depth"]

# --- Kategori kedalaman ---
def kategori_kedalaman(d):
    if d < 60:
        return "Dangkal"
    elif 60 <= d <= 300:
        return "Menengah"
    else:
        return "Dalam"

df["depth_cat"] = df["depth"].apply(kategori_kedalaman)

# Warna untuk tiap kategori kedalaman
warna_kedalaman = {
    "Dangkal": "yellow",
    "Menengah": "orange",
    "Dalam": "red"
}

# --- Kategori Magnitude ---
def kategori_magnitude(m):
    if m < 3:
        return "<3"
    elif 3 <= m < 4:
        return "3-4"
    elif 4 <= m < 5:
        return "4-5"
    elif 5 <= m < 6:
        return "5-6"
    else:
        return ">6"

df["mag_cat"] = df["mag"].apply(kategori_magnitude)

# Ukuran lingkaran sesuai kategori magnitude
ukuran_mag = {
    "<3": 8,
    "3-4": 20,
    "4-5": 70,
    "5-6": 200,
    ">6": 400
}

# --- Hitung jumlah per tahun ---
df["year"] = df["time"].dt.year
gempa_per_tahun = df.groupby("year").size().reset_index(name="count")

# --- Plot ---
fig = plt.figure(figsize=(10, 12), dpi=200)

# ======================================================================
# --- PERUBAHAN DI SINI ---
# Ubah rasio tinggi untuk membuat grafik bawah lebih besar.
# Awal: [2, 0.1, 1]
# Baru: [2, 0.1, 1.5] -> Grafik batang akan 1.5 kali lebih tinggi dari sebelumnya
gs = GridSpec(3, 1, height_ratios=[2, 0.1, 1], figure=fig)
# ======================================================================


# ====== PETA GEMPA ======
tiler = cimgt.GoogleTiles(style="satellite")
ax1 = fig.add_subplot(gs[0, 0], projection=ccrs.PlateCarree())
ax1.set_title("PETA SEISMISITAS NUSA TENGGARA TIMUR (Tahun 2000-2025)", fontsize=16, fontweight="bold")
ax1.add_image(tiler, 6)

# Plot per kategori kedalaman dan magnitude
for kedalaman in warna_kedalaman.keys():
    subset = df[df["depth_cat"] == kedalaman]
    ax1.scatter(
        subset["longitude"],
        subset["latitude"],
        s=subset["mag_cat"].map(ukuran_mag),
        c=warna_kedalaman[kedalaman],
        alpha=0.6,
        edgecolors="black",
        linewidth=0.5,
        label=kedalaman,
        transform=ccrs.PlateCarree()
    )

# Zoom sesuai titik gempa
margin_lon = 0.4
margin_lat = 0.1
ax1.set_extent([
    lon.min() - margin_lon, lon.max() + margin_lon,
    lat.min() - margin_lat, lat.max() + margin_lat
])

# Gridlines
gl = ax1.gridlines(draw_labels=True, linewidth=0.5, color='white', alpha=0.7, linestyle='--')
gl.top_labels = False
gl.right_labels = False

# === LEGEND WARNA (Kedalaman) ===
legend_kedalaman = ax1.legend(
    title="Kedalaman",
    loc="lower left",
    frameon=True
)

# === LEGEND UKURAN (Magnitude) ===
handles_mag = [
    plt.Line2D([], [], marker='o', color='w', markerfacecolor='gray',
               markersize=(size**0.5), label=f"M {label}", markeredgecolor='black')
    for label, size in ukuran_mag.items()
]
legend_magnitude = ax1.legend(
    handles=handles_mag,
    title="Magnitude",
    loc="lower right",
    frameon=True
)

ax1.add_artist(legend_kedalaman)
ax1.add_artist(legend_magnitude)

# ====== GRAFIK PER TAHUN ======
ax2 = fig.add_subplot(gs[2, 0])
ax2.set_title("Jumlah Kejadian Gempa per Tahun", fontsize=14)
ax2.bar(gempa_per_tahun["year"], gempa_per_tahun["count"], color="steelblue", edgecolor="black")
ax2.set_xlabel("Tahun")
ax2.set_ylabel("Jumlah Gempa")
ax2.set_xticks(gempa_per_tahun["year"])
ax2.tick_params(axis='x', rotation=45) # Tambahan agar label tahun tidak tumpang tindih
ax2.grid(axis='y', linestyle='--', alpha=0.7) # Tambahan grid untuk keterbacaan

plt.tight_layout(pad=1.0) # Sesuaikan padding agar judul tidak tumpang tindih
plt.show()