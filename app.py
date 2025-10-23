import os
import math
from datetime import datetime
import pytz
from flask import Flask, jsonify, render_template, request

TOTAL_SLOTS = 5
RATE_PER_HOUR = 3000
TIMEZONE_STR = 'Asia/Jakarta'
TIMEZONE = pytz.timezone(TIMEZONE_STR)

app = Flask(__name__)

active_tickets = {}
occupied_slots = 0
next_ticket_id = 1
available_slot_numbers = list(range(1, TOTAL_SLOTS + 1))


def get_now():
    return datetime.now(TIMEZONE)

def format_datetime_iso(dt):
    return dt.isoformat()

def generate_ticket_id():
    global next_ticket_id
    ticket_id = f"T{next_ticket_id:04d}"
    next_ticket_id += 1
    return ticket_id

def calculate_parking_fee(entry_time, exit_time):
    duration_seconds = (exit_time - entry_time).total_seconds()
    
    duration_hours = math.ceil(duration_seconds / 3600)
    
    if duration_hours < 1:
        duration_hours = 1
        
    cost = duration_hours * RATE_PER_HOUR
    return int(duration_hours), int(cost)

def setup_initial_data():
    global occupied_slots, next_ticket_id, available_slot_numbers, active_tickets
    
    initial_entries = [
        {"plate_number": "B1234AA", "entry_time": TIMEZONE.localize(datetime(2025, 10, 17, 8, 5))},
        {"plate_number": "D4567BB", "entry_time": TIMEZONE.localize(datetime(2025, 10, 17, 9, 30))},
        {"plate_number": "F7890CC", "entry_time": TIMEZONE.localize(datetime(2025, 10, 17, 10, 15))},
    ]

    for entry in initial_entries:
        if occupied_slots < TOTAL_SLOTS:
            ticket_id = generate_ticket_id()
            slot_number = available_slot_numbers.pop(0)
            
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


@app.route('/api/slots/available', methods=['GET'])
def get_available_slots():
    available = TOTAL_SLOTS - occupied_slots
    return jsonify({
        "total_slots": TOTAL_SLOTS,
        "occupied_slots": occupied_slots,
        "available_slots": available
    }), 200

@app.route('/api/entries', methods=['POST'])
def handle_check_in():
    global occupied_slots, active_tickets
    
    if occupied_slots >= TOTAL_SLOTS:
        return jsonify({"error": "Maaf, parkir sudah penuh."}), 400
        
    data = request.json
    if not data or 'plate_number' not in data or not data['plate_number'].strip():
        return jsonify({"error": "Nomor plat diperlukan."}), 400
        
    plate_number = data['plate_number'].upper().strip()
    
    for ticket in active_tickets.values():
        if ticket['plate_number'] == plate_number:
            return jsonify({"error": f"Mobil dengan plat {plate_number} sudah terparkir."}), 400

    ticket_id = generate_ticket_id()
    entry_time = get_now()
    slot_number = available_slot_numbers.pop(0)
    
    new_ticket = {
        "plate_number": plate_number,
        "entry_time": entry_time,
        "slot_number": slot_number
    }
    
    active_tickets[ticket_id] = new_ticket
    occupied_slots += 1
    
    return jsonify({
        "ticket_id": ticket_id,
        "plate_number": new_ticket["plate_number"],
        "slot_number": new_ticket["slot_number"],
        "entry_time": format_datetime_iso(new_ticket["entry_time"]),
        "available_slots": TOTAL_SLOTS - occupied_slots
    }), 201

@app.route('/api/exits', methods=['POST'])
def handle_check_out():
    global occupied_slots, active_tickets
    
    data = request.json
    if not data or 'ticket_id' not in data:
        return jsonify({"error": "ID Tiket diperlukan."}), 400

    ticket_id = data['ticket_id']
    
    if ticket_id not in active_tickets:
        return jsonify({"error": "Tiket tidak ditemukan."}), 404
        
    ticket = active_tickets[ticket_id]
    exit_time = get_now()
    
    duration_hours, cost = calculate_parking_fee(ticket["entry_time"], exit_time)
    
    slot_number = ticket["slot_number"]
    del active_tickets[ticket_id]
    
    occupied_slots -= 1
    available_slot_numbers.append(slot_number)
    available_slot_numbers.sort()

    return jsonify({
        "ticket_id": ticket_id,
        "plate_number": ticket["plate_number"],
        "duration_hours": duration_hours,
        "cost": cost,
        "entry_time": format_datetime_iso(ticket["entry_time"]),
        "exit_time": format_datetime_iso(exit_time)
    }), 200


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


@app.route('/', methods=['GET'])
def dashboard():
    now = get_now()
    tickets_list = []
    
    sorted_ticket_ids = sorted(active_tickets.keys(), key=lambda tid: active_tickets[tid]['entry_time'])

    for ticket_id in sorted_ticket_ids:
        ticket = active_tickets[ticket_id]
        
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

if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    setup_initial_data()
    
if __name__ == '__main__':
    app.run(debug=True, port=5000)