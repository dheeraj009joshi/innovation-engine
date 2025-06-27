import requests
# import whisper
import pytesseract
from PIL import Image
from io import BytesIO

# ----------- Video Transcription from URL ----------- #
import requests

def download_tiktok_video(video_url: str, output_path: str = "tiktok_video.mp4"):
    try:
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        }

        cookies = {
            '_ttp': '2vTmKLk9iBm5lnaeFVqpV0gAG3K',
            'tt_chain_token': 'eEBaC8jwAcHDTJ4vZeC/AQ==',
            'cookie-consent': '{"optional":true,"ga":true,"af":true,"fbp":true,"lip":true,"bing":true,"ttads":true,"reddit":true,"hubspot":true,"version":"v10"}',
            'passport_csrf_token': 'a0cfd54199855fca04319a1f7c7871e6',
            'passport_csrf_token_default': 'a0cfd54199855fca04319a1f7c7871e6',
            'multi_sids': '6707624914918704134:cba68271b977fbd689884e698bc07acb',
            'cmpl_token': 'AgQQAPPdF-RO0o0oq_XceN0_8kRsn5TcP5QTYN_FQQ',
            'passport_auth_status': 'f1c5d901b974f4725c0966c92fcb7ecf,',
            'passport_auth_status_ss': 'f1c5d901b974f4725c0966c92fcb7ecf,',
            'uid_tt': 'e1ec7b6f72b2db8386dfa7253fa6e913fee84e7449a59d9b1d59e565df13ee82',
            'uid_tt_ss': 'e1ec7b6f72b2db8386dfa7253fa6e913fee84e7449a59d9b1d59e565df13ee82',
            'sid_tt': 'cba68271b977fbd689884e698bc07acb',
            'sessionid': 'cba68271b977fbd689884e698bc07acb',
            'sessionid_ss': 'cba68271b977fbd689884e698bc07acb',
            'store-idc': 'alisg',
            'store-country-code': 'in',
            'store-country-code-src': 'uid',
            'tt-target-idc': 'alisg',
            'tt-target-idc-sign': 'AgHkoRrvUaevh7GpDT5tMLZl_j-e2TvzJ0GpZh85PSndfpzgF0pBJf6wiuCC0zIKp0PIgGzSNPW1hrRLGF13BSBv3qRuUmZF3-2dPn-Kf7Sq0D6vXfUZKaE69JHlKUMnrVLkEZaG_FDJwGBHauG5n3s9K2IAg9fxEQjm5R0Zd_S4OHt7I5gYS6H687ScIm-MhEGVeC2X0e3oWfZXqFPtS4HrxoLUWXE8nn0FXD7aWPl1tHNJQhuorrZ6FsZbdDKJCpF8bdR940T_bbaNte5KoU-tS8q82iwE8HBAUIww-UNmnBhbwwYWmpU0VwW6tJ0XCmt8txSoWHbLvTRAkgP_T_4PWa6xfLfG2lmrx8xp7rACfqo0QYNLa1D0bpeLEeNVt3tktQ-ty8rCJe0uL2ro79OzouytShx-q8wqd2telj7HSUi2HhgWDTnaj2d09wcamyGtnkdHiJB0lE9eWb7FinEqy4J9zjhKQx5A6tD9a6hZNZU1YYb5H8vvAfBSWuRq',
            'sid_guard': 'cba68271b977fbd689884e698bc07acb|1747318395|15551992|Tue,+11-Nov-2025+14:13:07+GMT',
            'sid_ucp_v1': '1.0.0-KGFiYmJlN2I2NmEzNDQyZGUwNjQ3ODdjNWQ5YjZmZmExMzk0MzRiYzkKGQiGiKiipaqRi10Q--yXwQYYsws4CEASSAQQAxoDc2cxIiBjYmE2ODI3MWI5NzdmYmQ2ODk4ODRlNjk4YmMwN2FjYg',
            'ssid_ucp_v1': '1.0.0-KGFiYmJlN2I2NmEzNDQyZGUwNjQ3ODdjNWQ5YjZmZmExMzk0MzRiYzkKGQiGiKiipaqRi10Q--yXwQYYsws4CEASSAQQAxoDc2cxIiBjYmE2ODI3MWI5NzdmYmQ2ODk4ODRlNjk4YmMwN2FjYg',
            'odin_tt': '9a4157c891e3def8ac66daf3ea329383be33ffa641fefc8cd5ce8290b8d8c4f35aa9c0c92dc7ec10f5d5b2a72ecb34a66e4f9c4855b080553ff78d6612d369817fb531aaddcb2777e57d2e05ebb30dc3',
            '_ga': 'GA1.1.1091366148.1747743965',
            'FPID': 'FPID2.2.RTIK0bQ0d+QIT0y3YydV/9hFYM+mF4MWCnYqc54+t3c=.1747743965',
            'FPAU': '1.2.2096691100.1747743965',
            '_fbp': 'fb.1.1747743964807.1995770234',
            '_ga_LWWPCY99PB': 'GS1.1.1747743964.1.1.1747744759.0.0.1024322831',
            'store-country-sign': 'MEIEDOQepyq5KJR4qP5B2gQgtzeld01L8CA3-KdxPo_NvsepbUN3fHYlAYK5DH0ZQA0EEDqpjUKf9lcwqiHayHWimYY',
            'ttwid': '1|tpcKJZiJUtRMWFXwOK6mpNIqHxeJeseBHrZfmHrHez4|1749057722|e71c7a12987e22cf50a068814188ce5f488b305a00face9b0fb18fd619c89369',
            'msToken': 'Nc4sPhltYIIzShPnNlZYw_yHxRUbml6gsQ2DLcmhKzXsLHaS4pPy5P-6kK5Q5U3mvsMN0tPtR0QvvYyhUBN0LkyEyUgcbj0_UeBBr8LOkEO4tiFpQfQQJsf9ZbMn'
        }

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
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")


def transcribe_with_whisper(video_path):
    try:
        print("Transcribing...")
        result = model.transcribe(video_path)
        return result["text"]
    except Exception as e:
        print("Error in transcribing video :- ",e)

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
