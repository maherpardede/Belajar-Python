import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.dates as mdates

# =========================
# 1. SET FOLDER & FILE
# =========================
folder_path = Path(r"G:\Dukono\RSAM")
file_path = folder_path / "RSAM_DKB_10min.csv"

# --- CUSTOMIZATION PARAMETERS ---
interval_minor = 2
# Menentukan rentang highlight kuning
start_highlight = "2026-01-17"
end_highlight = "2026-03-15"
# --------------------------------

print(f"Mengecek file: {file_path}")

# =========================
# 2. BACA FILE CSV
# =========================
try:
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['rsam'] = pd.to_numeric(df['rsam'], errors='coerce')
    df = df.dropna(subset=['timestamp', 'rsam'])
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
except Exception as e:
    print(f"❌ Gagal: {e}")
    exit()

# =========================
# 3. RESAMPLE HARIAN
# =========================
daily_mean = df['rsam'].resample('D').mean()

# =========================
# 4. PLOT
# =========================
plt.figure(figsize=(20, 7))
ax = plt.gca()

# --- TAMBAHKAN HIGHLIGHT KUNING ---
# Menambahkan latar belakang kuning sesuai rentang tanggal yang diminta
ax.axvspan(pd.to_datetime(start_highlight),
           pd.to_datetime(end_highlight),
           color='yellow',
           alpha=0.5,
           label='Carrier OFF')

# Plot Scatter & Line
plt.scatter(df.index, df['rsam'], facecolors='none', edgecolors='black', s=5, alpha=0.3, label='RSAM (10-min)')
plt.plot(daily_mean.index, daily_mean, color='red', linewidth=2, label='Daily Mean')

# --- KUSTOMISASI SUMBU ---
# Pas kan margin sesuai data
ax.set_xlim(df.index.min(), df.index.max())

# Format Tanggal
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y'))
ax.xaxis.set_minor_locator(mdates.DayLocator(interval=2))

plt.xticks(rotation=90)
plt.xlabel('Waktu')
plt.ylabel('RSAM (count)')
plt.ylim(0, 750)
plt.title('RSAM Gunung Dukono - Stasiun DKB', size=20, pad=20)

# Taruh legenda di luar atau posisi yang tidak tertutup highlight jika perlu
plt.legend(loc='upper left')

# Grid
ax.grid(True, which='major', linestyle='-', color='gray', alpha=0.6)
ax.grid(True, which='minor', linestyle=':', alpha=0.4)

plt.tight_layout()
plt.show()
