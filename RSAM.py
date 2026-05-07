import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from obspy.clients.filesystem.sds import Client
from obspy import UTCDateTime
import logging
import time  # Untuk menghitung durasi eksekusi

# =================================================================
# ========================= KONFIGURASI ===========================
# =================================================================
sds_root = r"G:\Dukono\Converted\SDS"                  # Jalur folder data SDS
output_dir = r"G:\Dukono\RSAM"                         # Folder hasil output

# Parameter Waktu & Metadata
INTERVAL_SEC = 600                                     # Interval RSAM (600 detik = 10 menit)
start_total = UTCDateTime("2026-01-01")                # Tanggal mulai data
end_total = UTCDateTime("2026-04-18")                  # Tanggal akhir data

network = "VG"                                         # Kode Network
station = "DKB"                                        # Kode Stasiun 
location = "00"                                        # Kode Lokasi
channel = "EHZ"                                        # Kode Channel (Vertical) HHZ,HHE, dll

# Penamaan file output otomatis
output_csv = os.path.join(output_dir, f"RSAM_{station_code}_10min.csv")

# Buat folder output jika belum ada
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Pengaturan log untuk memantau proses
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# =================================================================

if __name__ == "__main__":
    start_time_bench = time.time()  # Catat waktu mulai script
    client = Client(sds_root)  # Inisialisasi pembaca SDS (1x untuk efisiensi)

    # 1. CEK DATA LAMA (INCREMENTAL LOADING)
    existing_timestamps = set()
    if os.path.exists(output_csv):
        df_existing = pd.read_csv(output_csv, usecols=['timestamp'])
        existing_timestamps = set(df_existing['timestamp'].astype(str).tolist())
        logging.info(f"Cache ditemukan: {len(existing_timestamps)} data sudah ada.")

    # 2. HITUNG TOTAL HARI UNTUK PROGRESS BAR
    total_days = int((end_total - start_total) / 86400) + 1
    current_day = UTCDateTime(start_total.date)
    processed_count = 0

    logging.info(f"Memulai pemrosesan total {total_days} hari untuk stasiun {station_code}...")

    # 3. LOOPING UTAMA PER HARI (BATCH I/O)
    while current_day <= end_total:
        processed_count += 1
        percent = (processed_count / total_days) * 100
        day_str = current_day.strftime("%Y-%m-%d")

        try:
            # Baca data 1 hari sekaligus dari disk
            st = client.get_waveforms(network, station, location, channel, current_day, current_day + 86400)

            if len(st) > 0:
                logging.info(f"[{percent:.2f}%] Memproses {day_str}...")

                st.merge(fill_value=0)  # Gabungkan jika data terputus
                st.detrend("demean")  # Hilangkan offset sinyal

                new_results = []

                # Potong data harian di memori (RAM) menjadi segmen 10 menit
                for stream_slice in st.slide(window_length=INTERVAL_SEC, step=INTERVAL_SEC):
                    trace = stream_slice[0]  # Ambil objek Trace pertama dari stream slice
                    t_start = trace.stats.starttime

                    # Simpan hanya jika timestamp belum ada di CSV
                    if str(t_start) not in existing_timestamps:
                        # RUMUS RSAM: Mean of Absolute Values
                        rsam_value = np.mean(np.abs(trace.data))

                        new_results.append({
                            "timestamp": str(t_start),
                            "rsam": rsam_value
                        })

                # Tulis hasil ke CSV (Mode Append)
                if new_results:
                    df_new = pd.DataFrame(new_results)
                    file_exists = os.path.isfile(output_csv)
                    df_new.to_csv(output_csv, mode='a', index=False, header=not file_exists)
            else:
                logging.warning(f"[{percent:.2f}%] Data kosong pada {day_str}")

        except Exception as e:
            logging.error(f"[{percent:.2f}%] Error pada {day_str}: {e}")

        current_day += 86400  # Lanjut ke hari berikutnya

    # 4. LAPORAN TOTAL WAKTU PROCESSING
    end_time_bench = time.time()
    duration = end_time_bench - start_time_bench
    m, s = divmod(duration, 60)
    h, m = divmod(m, 60)

    print("-" * 60)
    print(f"PEMROSESAN SELESAI!")
    print(f"Total Waktu: {int(h)} jam, {int(m)} menit, {s:.2f} detik")
    print("-" * 60)

    # 5. VISUALISASI HASIL (SCATTER PLOT)
    if os.path.exists(output_csv):
        logging.info("Membuat grafik RSAM (Scatter Mode)...")
        df_plot = pd.read_csv(output_csv)
        df_plot['timestamp'] = pd.to_datetime(df_plot['timestamp'], utc=True)
        df_plot = df_plot.sort_values('timestamp')
        df_plot = df_plot[df_plot['rsam'] > 0]  # Abaikan nilai nol

        plt.figure(figsize=(15, 7))
        plt.scatter(df_plot['timestamp'], df_plot['rsam'],
                    color='blue', s=2, alpha=0.4, label=f'RSAM {station_code}')

        plt.title(f'RSAM Scatter Plot - Station {station_code} (10-Min Interval)', fontsize=14)
        plt.xlabel('Tanggal')
        plt.ylabel('RSAM (counts)')
        plt.ylim(bottom=0)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend(loc='upper right', markerscale=5)
        plt.tight_layout()

        # Simpan gambar otomatis
        plt.savefig(os.path.join(output_dir, f"RSAM_{station_code}_Scatter.png"), dpi=300)
        plt.show()

