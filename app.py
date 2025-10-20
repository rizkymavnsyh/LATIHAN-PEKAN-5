import os
import math
from datetime import datetime
import pytz
from flask import Flask, jsonify, render_template, request

# --- 1. Konfigurasi Aplikasi ---
# Konfigurasi ini ditempatkan di atas agar mudah diubah.
TOTAL_SLOTS = 5
RATE_PER_HOUR = 3000
TIMEZONE_STR = 'Asia/Jakarta'
TIMEZONE = pytz.timezone(TIMEZONE_STR)

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# --- 2. Manajemen Data (In-Memory) ---
# Kita gunakan dictionary untuk menyimpan tiket aktif dan variabel untuk counter.
active_tickets = {}  # Key: ticket_id, Value: dict data tiket
occupied_slots = 0
next_ticket_id = 1
# List untuk melacak nomor slot mana yang tersedia
available_slot_numbers = list(range(1, TOTAL_SLOTS + 1))


# --- 3. Fungsi Helper (Logika Bisnis) ---

def get_now():
    """Mengembalikan datetime saat ini dalam zona waktu Asia/Jakarta."""
    return datetime.now(TIMEZONE)

def format_datetime_iso(dt):
    """Mengubah objek datetime menjadi string format ISO 8601 dengan timezone."""
    return dt.isoformat()

def generate_ticket_id():
    """Membuat ID tiket baru yang berurutan (misal: T0001, T0002)."""
    global next_ticket_id
    ticket_id = f"T{next_ticket_id:04d}"
    next_ticket_id += 1
    return ticket_id

def calculate_parking_fee(entry_time, exit_time):
    """
    Menghitung durasi parkir (dibulatkan ke atas) dan total biaya.
    Durasi minimum adalah 1 jam.
    """
    duration_seconds = (exit_time - entry_time).total_seconds()
    
    # Hitung jam, bulatkan ke atas
    duration_hours = math.ceil(duration_seconds / 3600)
    
    # Terapkan durasi minimum 1 jam
    if duration_hours < 1:
        duration_hours = 1
        
    cost = duration_hours * RATE_PER_HOUR
    return int(duration_hours), int(cost)

# --- 4. Inisialisasi Data Awal ---

def setup_initial_data():
    """Mengisi data awal dengan 3 mobil sesuai spesifikasi."""
    global occupied_slots, next_ticket_id, available_slot_numbers, active_tickets
    
    # Data awal (17 Oktober 2025)
    initial_entries = [
        {"plate_number": "B1234AA", "entry_time": TIMEZONE.localize(datetime(2025, 10, 17, 8, 5))},
        {"plate_number": "D4567BB", "entry_time": TIMEZONE.localize(datetime(2025, 10, 17, 9, 30))},
        {"plate_number": "F7890CC", "entry_time": TIMEZONE.localize(datetime(2025, 10, 17, 10, 15))},
    ]

    for entry in initial_entries:
        if occupied_slots < TOTAL_SLOTS:
            ticket_id = generate_ticket_id()
            slot_number = available_slot_numbers.pop(0) # Ambil slot pertama yang tersedia
            
            active_tickets[ticket_id] = {
                "plate_number": entry["plate_number"],
                "entry_time": entry["entry_time"],
                "slot_number": slot_number
            }
            occupied_slots += 1
        else:
            print("Peringatan: Parkir penuh, data awal tidak dapat dimuat semua.")
            break
            
    print(f"Aplikasi dimulai dengan {occupied_slots} mobil terparkir.")
    print(f"Tiket aktif: {list(active_tickets.keys())}")
    print(f"Slot tersedia: {available_slot_numbers}")


# --- 5. Endpoint API ---

@app.route('/api/slots/available', methods=['GET'])
def get_available_slots():
    """API untuk mendapatkan informasi ketersediaan slot."""
    available = TOTAL_SLOTS - occupied_slots
    return jsonify({
        "total_slots": TOTAL_SLOTS,
        "occupied_slots": occupied_slots,
        "available_slots": available
    }), 200

@app.route('/api/entries', methods=['POST'])
def handle_check_in():
    """API untuk check-in mobil baru."""
    global occupied_slots, active_tickets
    
    # 1. Cek jika parkir penuh
    if occupied_slots >= TOTAL_SLOTS:
        return jsonify({"error": "Maaf, parkir sudah penuh."}), 400
        
    data = request.json
    if not data or 'plate_number' not in data or not data['plate_number'].strip():
        return jsonify({"error": "Nomor plat diperlukan."}), 400
        
    plate_number = data['plate_number'].upper().strip()
    
    # Cek jika plat sudah terparkir (opsional, tapi bagus)
    for ticket in active_tickets.values():
        if ticket['plate_number'] == plate_number:
            return jsonify({"error": f"Mobil dengan plat {plate_number} sudah terparkir."}), 400

    # 2. Buat tiket baru
    ticket_id = generate_ticket_id()
    entry_time = get_now()
    slot_number = available_slot_numbers.pop(0) # Ambil slot tersedia
    
    new_ticket = {
        "plate_number": plate_number,
        "entry_time": entry_time,
        "slot_number": slot_number
    }
    
    active_tickets[ticket_id] = new_ticket
    occupied_slots += 1
    
    # 3. Kembalikan data tiket baru
    return jsonify({
        "ticket_id": ticket_id,
        "plate_number": new_ticket["plate_number"],
        "slot_number": new_ticket["slot_number"],
        "entry_time": format_datetime_iso(new_ticket["entry_time"]),
        "available_slots": TOTAL_SLOTS - occupied_slots
    }), 201 # 201 Created

@app.route('/api/exits', methods=['POST'])
def handle_check_out():
    """API untuk check-out mobil dan menghitung biaya."""
    global occupied_slots, active_tickets
    
    data = request.json
    if not data or 'ticket_id' not in data:
        return jsonify({"error": "ID Tiket diperlukan."}), 400

    ticket_id = data['ticket_id']
    
    # 1. Cari tiket
    if ticket_id not in active_tickets:
        return jsonify({"error": "Tiket tidak ditemukan."}), 404 # 404 Not Found
        
    # 2. Ambil data tiket dan hitung biaya
    ticket = active_tickets[ticket_id]
    exit_time = get_now()
    
    duration_hours, cost = calculate_parking_fee(ticket["entry_time"], exit_time)
    
    # 4. Hapus tiket dari data aktif
    slot_number = ticket["slot_number"]
    del active_tickets[ticket_id]
    
    # 5. Bebaskan slot
    occupied_slots -= 1
    available_slot_numbers.append(slot_number)
    available_slot_numbers.sort() # Jaga agar list slot tetap terurut

    # 5. Kembalikan rincian biaya
    return jsonify({
        "ticket_id": ticket_id,
        "plate_number": ticket["plate_number"],
        "duration_hours": duration_hours,
        "cost": cost,
        "entry_time": format_datetime_iso(ticket["entry_time"]),
        "exit_time": format_datetime_iso(exit_time)
    }), 200


# Endpoint simulasi (sesuai spesifikasi)
@app.route('/api/webhooks/slot-1', methods=['GET'])
def webhook_slot_minus():
    global occupied_slots
    if occupied_slots > 0:
        occupied_slots -= 1
    return jsonify({"message": "OK", "occupied_slots": occupied_slots}), 200

@app.route('/api/webhooks/slot+1', methods=['GET'])
def webhook_slot_plus():
    global occupied_slots
    if occupied_slots < TOTAL_SLOTS:
        occupied_slots += 1
    return jsonify({"message": "OK", "occupied_slots": occupied_slots}), 200


# --- 6. Route Dashboard Web (UI) ---

@app.route('/', methods=['GET'])
def dashboard():
    """Menampilkan halaman dashboard utama."""
    
    # Siapkan data untuk ditampilkan di tabel
    now = get_now()
    tickets_list = []
    
    # Urutkan tiket berdasarkan waktu masuk
    sorted_ticket_ids = sorted(active_tickets.keys(), key=lambda tid: active_tickets[tid]['entry_time'])

    for ticket_id in sorted_ticket_ids:
        ticket = active_tickets[ticket_id]
        
        # Hitung biaya parkir saat ini (real-time)
        current_duration, current_cost = calculate_parking_fee(ticket["entry_time"], now)
        
        tickets_list.append({
            "ticket_id": ticket_id,
            "plate_number": ticket["plate_number"],
            "slot_number": ticket["slot_number"],
            "entry_time_str": format_datetime_iso(ticket["entry_time"]),
            "current_cost_str": f"Rp {current_cost:,}"
        })

    return render_template(
        "index.html",
        total_slots=TOTAL_SLOTS,
        occupied_slots=occupied_slots,
        available_slots=TOTAL_SLOTS - occupied_slots,
        tickets=tickets_list
    )

# --- 7. Menjalankan Aplikasi ---

if __name__ == '__main__':
    # Pastikan data awal dimuat hanya sekali saat aplikasi dimulai
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        setup_initial_data()
    
    # Menjalankan aplikasi
    # Gunakan host='0.0.0.0' jika ingin diakses dari jaringan
    app.run(debug=True, port=5000)