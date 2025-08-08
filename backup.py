import os
import subprocess
import datetime

# 🔧 Konfigurasi
REPO_PATH = r"F:\DOKUMEN\BACKUP"
REMOTE_URL = "https://whayoe:ghp_11BUTQVLY0YEsyD9GuqxIw_efjcl2sraVfwwC4rQbmtVC3lqhdCxOZCP3U05EfVy0VYVHACPG7zLQdtslc@github.com/whayoe/new-backup.git"
BRANCH = "main"

def run_command(command):
    result = subprocess.run(command, cwd=REPO_PATH, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def backup():
    print(f"📅 Mulai backup: {datetime.datetime.now()}")
    
    if not os.path.exists(REPO_PATH):
        print(f"❌ Folder tidak ditemukan: {REPO_PATH}")
        return
    
    os.chdir(REPO_PATH)

    # Tambahkan semua perubahan
    if not run_command("git add ."):
        return

    # Cek apakah ada perubahan
    result = subprocess.run(
        "git status --porcelain", 
        cwd=REPO_PATH, 
        shell=True, 
        capture_output=True, 
        text=True
    )
    if not result.stdout.strip():
        print("✅ Tidak ada perubahan. Tidak perlu commit.")
        return

    # Buat commit
    commit_msg = f"Auto-backup: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    if not run_command(f'git commit -m "{commit_msg}"'):
        return

    # Push ke GitHub
    print("📤 Sedang push ke GitHub...")
    if run_command(f"git push {REMOTE_URL} {BRANCH}"):
        print("✅ Backup berhasil!")
    else:
        print("❌ Gagal push ke GitHub.")

if __name__ == "__main__":
    backup()