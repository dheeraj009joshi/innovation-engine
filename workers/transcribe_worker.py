import whisper
import sys

video_path = sys.argv[1]
model = whisper.load_model("tiny", device="cpu")

try:
    result = model.transcribe(video_path, fp16=False)
    print(result.get("text", ""))
except Exception as e:
    print(f"[Error] {e}", file=sys.stderr)
    sys.exit(1)