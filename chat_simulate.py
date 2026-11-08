import sys
import time
from dotenv import load_dotenv

# Muat variabel konfigurasi dari file .env
load_dotenv()

from app.engine.conversational_agent import conversational_agent
from app.models.schemas import ChatRequest


def print_divider():
    print("-" * 70)


def run_chat_simulator():
    session_id = f"chat-sppg-{int(time.time())}"
    user_role = "Kepala SPPG"

    print("\n" + "=" * 70)
    print("  🤖 RESILIOAI: CONVERSATIONAL INCIDENT ASSISTANT")
    print(f"  Sesi ID: {session_id} | Pengguna: {user_role}")
    print("=" * 70)
    print("Selamat datang di asisten cerdas operasional SPPG.")
    print("Kemampuan utama yang dapat dicoba:")
    print("1. 🚨 Lapor Gangguan Pasokan: 'Ada kebakaran di gudang PT Berkah Unggas Jaya'")
    print("2. 📝 Onboarding Supplier: 'Daftarkan supplier baru CV Berkah Mandiri, ayam Rp 38.000, kapasitas 200kg, halal ID3211'")
    print("3. 🔄 Update Rekanan: 'Update harga PT Berkah Unggas Jaya menjadi Rp 36.500'")
    print("4. ⛔ Nonaktifkan Rekanan: 'Nonaktifkan supplier UD Ayam Murah Meriah'")
    print("5. 📦 Cek Inventaris: 'Cek stok gudang dan sisa kapasitas freezer'")
    print("(Ketik 'exit' atau 'keluar' untuk mengakhiri obrolan)")
    print_divider()

    while True:
        try:
            user_input = input(f"\n[{user_role}] > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSesi obrolan diakhiri.")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "keluar", "quit"]:
            print("\nTerima kasih telah menggunakan ResilioAI. Sesi ditutup.")
            break

        print("\n🤖 [ResilioAI Agent berpikir...]")
        time.sleep(0.3)

        request = ChatRequest(
            session_id=session_id,
            message=user_input,
            user_role=user_role,
        )

        response = conversational_agent.process_message(request)

        print("\n" + response.reply)
        print_divider()
        print(f"📌 Status Tindakan: [{response.action_required.value}] | Niat: [{response.intent.value}]")


if __name__ == "__main__":
    run_chat_simulator()

