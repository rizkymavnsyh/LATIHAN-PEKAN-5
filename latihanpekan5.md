**Spesifikasi Proyek: Parking Lot System**

**1. Tujuan Utama:**
Buat aplikasi web Flask untuk mengelola area parkir dengan 5 slot. Aplikasi ini harus memiliki API untuk operasi check-in/check-out dan juga dashboard web sederhana untuk interaksi pengguna.

**2. Logika Bisnis & Konfigurasi:**
*   **Total Slot:** 5 slot parkir.
*   **Tarif:** Rp 3.000 per jam.
*   **Perhitungan Durasi:** Durasi parkir dibulatkan ke atas ke jam terdekat (contoh: 1 jam 10 menit dihitung sebagai 2 jam). Durasi minimum adalah 1 jam.
*   **Zona Waktu:** Seluruh timestamp harus menggunakan zona waktu `Asia/Jakarta` (UTC+7). Asumsikan input tanpa zona waktu adalah WIB.
*   **Konfigurasi:** Buatlah total slot dan tarif parkir mudah diubah di bagian atas file kode (misalnya, dalam variabel konstanta).

**3. Manajemen Data:**
*   **Penyimpanan:** Gunakan dictionary dalam memori (in-memory) untuk menyimpan data tiket aktif. Tidak perlu database eksternal.
*   **Data Awal:** Saat aplikasi dimulai, isi dengan 3 mobil yang sudah parkir. Gunakan waktu masuk yang bervariasi pada tanggal **17 Oktober 2025**.
*   **ID Tiket (`ticket_id`):**
    *   Dihasilkan secara berurutan, dimulai dari `T0001`.
    *   Harus unik.
    *   Formatnya harus memenuhi regex `^T\d{4}$`.
*   **Nomor Plat (`plate_number`):** Otomatis diubah menjadi huruf besar sebelum disimpan.

**4. Endpoint API:**
Buat endpoint API berikut dengan menggunakan Flask. Pastikan untuk mengembalikan respons dalam format JSON dan menggunakan kode status HTTP yang tepat (200, 201, 404, 400).

*   `GET /api/slots/available`
    *   **Respons:** JSON object yang menampilkan `total_slots`, `occupied_slots`, dan `available_slots`.
*   `POST /api/entries`
    *   **Request Body (JSON):** `{"plate_number": "AB123CD"}`
    *   **Logika:**
        1. Cek jika ada slot kosong. Jika tidak, kembalikan error 400.
        2. Buat tiket baru dengan `ticket_id` unik, `plate_number`, `entry_time` (waktu saat ini, WIB), dan `slot_number`.
        3. Kembalikan data tiket yang baru dibuat.
    *   **Respons (JSON, Status 201):** `{"ticket_id": "T0004", "plate_number": "AB123CD", "slot_number": 4, "entry_time": "2025-10-17T10:00:00+07:00", "available_slots": 1}`
*   `POST /api/exits`
    *   **Request Body (JSON):** `{"ticket_id": "T0001"}`
    *   **Logika:**
        1. Cari tiket berdasarkan `ticket_id`. Jika tidak ditemukan, kembalikan error 404.
        2. Hitung durasi parkir (dibulatkan ke atas).
        3. Hitung total biaya.
        4. Hapus tiket dari data aktif (bebaskan slot).
        5. Kembalikan rincian biaya.
    *   **Respons (JSON):** `{"ticket_id": "T0001", "plate_number": "B4567EF", "duration_hours": 3, "cost": 9000}`
*   `GET /api/webhooks/slot-1`
    *   **Logika:** Endpoint sederhana yang mengurangi `occupied_slots` sebesar 1 (untuk simulasi event).
    *   **Respons:** Pesan sukses.
*   `GET /api/webhooks/slot+1`
    *   **Logika:** Endpoint sederhana yang menambah `occupied_slots` sebesar 1 (untuk simulasi event).
    *   **Respons:** Pesan sukses.

**5. Dashboard Web (UI):**
*   **Route:** `/`
*   **Template:** Gunakan template HTML (dengan Jinja2) untuk menampilkan halaman.
*   **Konten Halaman:**
    1.  **Informasi Slot:** Tampilkan total slot, slot terisi, dan slot tersedia.
    2.  **Daftar Tiket Aktif:** Tabel yang menampilkan semua tiket aktif (`ticket_id`, `plate_number`, `entry_time`, `slot_number`,current price).
    3.  **Form Check-in ("New Entry"):** Formulir dengan input `plate_number` dan tombol untuk submit (mengirim request ke `POST /api/entries`). Gunakan JavaScript (`fetch`) untuk mengirimkan data dan memperbarui tampilan tanpa reload halaman penuh.
    4.  **Form Check-out ("Settle Ticket"):** Formulir dengan input `ticket_id` dan tombol untuk submit (mengirim request ke `POST /api/exits`). Juga gunakan JavaScript (`fetch`) untuk menampilkan rincian biaya (biaya dan durasi) dan memperbarui daftar tiket.

**6. Struktur Kode & Instruksi Tambahan:**
*   **File:** Hasilkan seluruh aplikasi dalam satu file bernama `app.py`.
*   **Keterbacaan:** Berikan komentar yang jelas dalam kode untuk menjelaskan logika penting.
*   **Styling:** Gunakan CSS sederhana (bisa inline atau dalam tag `<style>`) agar dashboard terlihat rapi dan mudah dibaca. Tidak perlu framework CSS yang kompleks.
*   **Error Handling:** Pastikan API dan dashboard menangani error dengan baik (misalnya, menampilkan pesan error jika check-in gagal karena parkir penuh).

**Tugas Akhir:**
Hasilkan kode Python lengkap untuk `app.py` yang memenuhi semua persyaratan di atas. Sertakan juga contoh kode untuk template HTML (`index.html`). Pastikan aplikasi dapat dijalankan dengan `flask run`.