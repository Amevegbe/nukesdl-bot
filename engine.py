from yt_dlp import YoutubeDL
import cowsay


# ----------------------------
# CORE ENGINE (single source of truth)
# ----------------------------
def download_video(url, platform="general"):
    try:
        ydl_opts = {
            "format": "best",
            "outtmpl": f"downloads/{platform}_%(title)s.%(ext)s"
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print("✅ Download completed successfully")

    except Exception as e:
        print("❌ Download failed")
        print("Error:", e)


# ----------------------------
# INPUT HANDLER
# ----------------------------
def get_url(prompt="Enter URL: "):
    return input(prompt)


# ----------------------------
# PLATFORM FUNCTIONS (thin wrappers)
# ----------------------------
def youtube():
    print("\n=== YOUTUBE DOWNLOADER ===")
    url = get_url()
    download_video(url, "youtube")


def tiktok():
    print("\n=== TIKTOK DOWNLOADER ===")
    url = get_url()
    download_video(url, "tiktok")


def instagram():
    print("\n=== INSTAGRAM DOWNLOADER ===")
    url = get_url()
    download_video(url, "instagram")


def facebook():
    print("\n=== FACEBOOK DOWNLOADER ===")
    url = get_url()
    download_video(url, "facebook")


def pinterest_video():
    print("\n=== PINTEREST VIDEO DOWNLOADER ===")
    url = get_url()
    download_video(url, "pinterest_video")


# ----------------------------
# MENU SYSTEM
# ----------------------------
def menu():
    print("\n==========================")
    print("   DOWNLOADER SYSTEM")
    print("==========================")
    print("1. YouTube")
    print("2. TikTok")
    print("3. Instagram")
    print("4. Facebook")
    print("5. Pinterest Video")
    print("0. Exit")


# ----------------------------
# MAIN LOOP
# ----------------------------
def main():
    while True:
        menu()

        try:
            choice = int(input("Enter choice: "))
        except ValueError:
            cowsay.cow("Invalid input")
            continue

        if choice == 0:
            print("Goodbye 👋")
            break

        elif choice == 1:
            youtube()
        elif choice == 2:
            tiktok()
        elif choice == 3:
            instagram()
        elif choice == 4:
            facebook()
        elif choice == 5:
            pinterest_video()
        else:
            print("Invalid option")


# ----------------------------
# RUN PROGRAM
# ----------------------------
if __name__ == "__main__":
    import os
    os.makedirs("downloads", exist_ok=True)

    main()