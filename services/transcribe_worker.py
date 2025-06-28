# services/workers/whisper_worker.py
import whisper
import traceback
from multiprocessing import Process, Queue

def whisper_worker(task_queue: Queue, result_queue: Queue):
    model = whisper.load_model("tiny", device="cpu")
    print("🔁 Whisper model loaded once and ready")

    while True:
        task = task_queue.get()
        if task == "STOP":
            print("🛑 Worker shutting down")
            break

        idx, video_path = task
        try:
            result = model.transcribe(video_path, fp16=False)
            result_queue.put((idx, result.get("text", "")))
        except Exception as e:
            traceback.print_exc()
            result_queue.put((idx, None))
