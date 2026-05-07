import os
import logging
import time
from obspy import read, UTCDateTime

# =================================================================
# 1. KONFIGURASI UTAMA (Ubah di Sini)
# =================================================================

# Jalur Folder
INPUT_FOLDER = r"D:\DATA\IL\ILTN"        # Folder berisi file MiniSEED asli
SDS_ROOT = r"D:\DATA\IL\SDS"             # Folder tujuan format SDS

# Header Baru
NEW_NETWORK = "VG"  # Ubah Kode Network (Misal: VG)
NEW_STATION = "ILTN"  # Ubah Nama Stasiun secara massal
FORCE_LOCATION = "00"  # Paksa kode lokasi (Misal: 00 atau "")

# Mapping
STATION_MAP = {
    "005369": "ANYR",  # Ubah stasiun spesifik jika ditemukan kode tertentu
}

CHANNEL_MAP = {
    "SHZ": "HHZ",  # Ubah tipe channel (Short-period ke Broadband)
    "SHN": "HHN",
    "SHE": "HHE"
}

# Filter: Hanya channel dalam list ini yang akan diproses
ALLOWED_CHANNELS = ["HHZ", "HHN", "HHE"]

# File Log
LOG_FILE = "process_sds.log"

# =================================================================
# 2. SISTEM LOGGING
# =================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()


# =================================================================
# 3. FUNGSI
# =================================================================

def write_trace_to_sds(tr, sds_root):
    """Menulis trace ke dalam struktur folder SDS: YYYY/NET/STA/CHA.D/filename"""
    net = tr.stats.network
    sta = tr.stats.station
    loc = tr.stats.location if tr.stats.location else ""
    cha = tr.stats.channel

    start = tr.stats.starttime
    end = tr.stats.endtime

    # Loop untuk membagi data jika melewati pergantian hari (Julian Day)
    current_time = UTCDateTime(start.date)
    while current_time <= end:
        year = current_time.year
        doy = current_time.julday

        day_start = UTCDateTime(year=year, julday=doy)
        day_end = day_start + 86400

        # Potong data sesuai hari yang sedang diproses
        tr_day = tr.copy().trim(day_start, day_end, pad=False)

        if len(tr_day.data) == 0:
            current_time += 86400
            continue

        # Susun path SDS
        sds_path = os.path.join(sds_root, f"{year}", net, sta, f"{cha}.D")
        os.makedirs(sds_path, exist_ok=True)

        # Susun nama file standar SDS
        filename = f"{net}.{sta}.{loc}.{cha}.D.{year}.{doy:03d}"
        full_path = os.path.join(sds_path, filename)

        # Simpan file (Append jika file hari yang sama sudah ada)
        tr_day.write(full_path, format="MSEED", append=os.path.exists(full_path))
        logger.info(f"Berhasil: {filename}")

        current_time += 86400


def process_file(file_path, sds_root):
    """Membaca file tunggal, mengedit header, dan mengirim ke penulis SDS"""
    try:
        st = read(file_path)
        if len(st) == 0: return

        for tr in st:
            # 1. Normalisasi teks channel
            cha = tr.stats.channel.strip().upper()

            # 2. Simpan ID lama untuk log
            old_id = f"{tr.stats.network}.{tr.stats.station}.{tr.stats.location}.{cha}"

            # 3. Update Header berdasarkan konfigurasi
            if NEW_NETWORK:    tr.stats.network = NEW_NETWORK
            if NEW_STATION:    tr.stats.station = NEW_STATION
            if FORCE_LOCATION: tr.stats.location = FORCE_LOCATION

            # 4. Station Mapping khusus
            if tr.stats.station in STATION_MAP:
                tr.stats.station = STATION_MAP[tr.stats.station]

            # 5. Channel Mapping
            if cha in CHANNEL_MAP:
                tr.stats.channel = CHANNEL_MAP[cha]
                cha = tr.stats.channel

            # 6. Filter Channel
            if cha not in ALLOWED_CHANNELS:
                logger.info(f"Skip: {old_id} (Bukan channel target)")
                continue

            new_id = f"{tr.stats.network}.{tr.stats.station}.{tr.stats.location}.{tr.stats.channel}"
            logger.info(f"Update: {old_id} -> {new_id}")

            write_trace_to_sds(tr, sds_root)

    except Exception as e:
        logger.error(f"Gagal memproses {file_path}: {e}")


# =================================================================
# 4. EKSEKUSI BATCH
# =================================================================

if __name__ == "__main__":
    start_bench = time.time()
    logger.info("=== MEMULAI KONVERSI SDS ===")

    success_count = 0
    total_count = 0

    # Cari file mseed di semua subfolder
    for root, dirs, files in os.walk(INPUT_FOLDER):
        for file in files:
            if file.lower().endswith((".mseed", ".msd", ".miniseed")):
                total_count += 1
                full_path = os.path.join(root, file)
                process_file(full_path, SDS_ROOT)
                success_count += 1

    # Summary Akhir
    duration = time.time() - start_bench
    logger.info("=" * 30)
    logger.info("PROSES SELESAI")
    logger.info(f"Total File Ditemukan : {total_count}")
    logger.info(f"Berhasil Diproses    : {success_count}")
    logger.info(f"Total Waktu          : {duration:.2f} detik")
    logger.info("=" * 30)
#modifikasi dari Batch_Certimus2SDS_editSCNL.py Bu Sulistiyani
