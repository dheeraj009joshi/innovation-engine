import subprocess
import requests
import whisper
import pytesseract
from PIL import Image
from io import BytesIO

# ----------- Video Transcription from URL ----------- #
import requests

def download_tiktok_video(video_url: str, output_path: str = "tiktok_video.mp4"):
    try:
        headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-IN,en;q=0.9",
    "dnt": "1",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}

        cookies = { }

        print(f"Downloading video from: {video_url}")
        response = requests.get(video_url, headers=headers, cookies=cookies, stream=True)

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"✅ Video downloaded successfully: {output_path}")
            return output_path
        else:
            print(f"❌ Failed to download video. Status Code: {response.status_code}, Reason: {response.reason}")
    except Exception as e:
        print("Error in downloading video :- ",e)



import torchaudio
import os
model = whisper.load_model("tiny",device="cpu")



from multiprocessing import Queue, Process
from services.transcribe_worker import whisper_worker

class WhisperManager:
    def __init__(self):
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.worker = Process(target=whisper_worker, args=(self.task_queue, self.result_queue))
        self.worker.start()

    def transcribe(self, idx, video_path):
        self.task_queue.put((idx, video_path))
        return self.result_queue.get()  # (idx, transcript)

    def shutdown(self):
        self.task_queue.put("STOP")
        self.worker.join()




def is_valid_audio(file_path):
    try:
        audio, sr = torchaudio.load(file_path)
        return audio.numel() > 0
    except Exception as e:
        print(f"Invalid or unreadable audio in file: {file_path} ({e})")
        return False

def safe_transcribe(video_path):
    try:
        result = subprocess.run(
            ["python3", "workers/transcribe_worker.py", video_path],
            capture_output=True,
            text=True,
            timeout=120  # avoid hanging forever
        )

        if result.returncode != 0:
            print(f"❌ Subprocess failed: {result.stderr.strip()}")
            return None

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout while transcribing {video_path}")
        return None

    except Exception as e:
        print(f"⚠️ Unexpected error in subprocess: {e}")
        return None

# ----------- Image-to-Text from URL ----------- #
def extract_text_from_image(image_url):
    print("Extracting text from image...")
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    text = pytesseract.image_to_string(image)
    return text

# ----------- Example Usage ----------- #
# if __name__ == "__main__":
#     # 1. Transcribe video
#     video_url = "https://www.tiktok.com/aweme/v1/play/?faid=1988&file_id=73579d7ad4d74bc48fdad12a036392e2&is_play_url=1&item_id=7497635805213494535&line=0&ply_type=2&signaturev3=dmlkZW9faWQ7ZmlsZV9pZDtpdGVtX2lkLmQwMmQ2NDMxOTQ2NjBjOTlkMjliNGY5NDY1NzlkMTNm&tk=tt_chain_token&video_id=v14044g50000d06f6c7og65stluqa13g"
#     video_file = download_tiktok_video(video_url)
#     transcription = transcribe_with_whisper(video_file)
#     print("\n--- Video Transcription ---\n", transcription)

#     # 2. Extract text from image
#     image_url = "YOUR_IMAGE_URL_HERE"
#     image_text = extract_text_from_image(image_url)
#     print("\n--- Image Text Extraction ---\n", image_text)
