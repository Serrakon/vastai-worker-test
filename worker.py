"""
Vast.ai PyWorker configuration for generic model server.

This is the PYWORKER_REPO entry point — cloned and run by Vast.ai's start_server.sh.
It proxies HTTP requests to a FastAPI model server running on localhost.

Environment variables:
    MODEL_SERVER_PORT   — port of the local model server (default: 18000)
    MAX_QUEUE_TIME      — max seconds a request can wait in queue (default: 800)
    BENCHMARK_SONG_URL  — URL of the song file for benchmarking
    BENCHMARK_VOICE_URL — URL of the voice reference file for benchmarking
"""
import os
import uuid

from vastai import BenchmarkConfig, HandlerConfig, LogActionConfig, Worker, WorkerConfig

MODEL_SERVER_PORT = int(os.environ.get("MODEL_SERVER_PORT", "18000"))
MAX_QUEUE_TIME = float(os.environ.get("MAX_QUEUE_TIME", "800"))

BENCHMARK_SONG_URL = os.environ.get(
    "BENCHMARK_SONG_URL",
    "https://storage.googleapis.com/img.aiartgen.cc/cover/aria-danil/aria_song_long.mp3",
)
BENCHMARK_VOICE_URL = os.environ.get(
    "BENCHMARK_VOICE_URL",
    "https://storage.googleapis.com/img.aiartgen.cc/cover/aria-danil/voice.mp4",
)


def _benchmark_payload():
    """Generate a real covers payload for benchmarking /process throughput."""
    # return {
    #     "request_id": f"benchmark-{uuid.uuid4()}",
    #     "user_id": "benchmark",
    #     "file_path": BENCHMARK_SONG_URL,
    #     "voice_ref_path": BENCHMARK_VOICE_URL,
    #     "ts": 0,
    #     "deadline": 0,
    #     "params": {
    #         "keep_files": "false",
    #         "output_format": "mp3",
    #     },
    # }
    return {"sleep": 10}


worker_config = WorkerConfig(
    model_server_url="http://127.0.0.1",
    model_server_port=MODEL_SERVER_PORT,
    model_log_file="/var/log/model/server.log",
    handlers=[
        HandlerConfig(
            route="/process",
            allow_parallel_requests=False,
            max_queue_time=MAX_QUEUE_TIME,
            workload_calculator=lambda payload: 250 if payload.get("sleep") else 10000,
            benchmark_config=BenchmarkConfig(
                generator=_benchmark_payload,
                runs=1,
                concurrency=1,
                do_warmup=False,
            ),
        ),
    ],
    log_action_config=LogActionConfig(
        on_load=["Application startup complete."],
        on_error=[
            "CUDA error:",
            "error from cudaGetDeviceCount",
            "RuntimeError:",
            "Traceback (most recent call last):",
        ],
        on_info=[
            "Loading model:",
            "Running load_models()",
            "METRICS - Voice noise reduction completed",
            "METRICS - Voice conversion completed",
            "METRICS - Audio mixing completed",
            "METRICS - Input conversion completed",
            "PIPELINE TIMING REPORT",
        ],
    ),
)

if __name__ == "__main__":
    Worker(worker_config).run()

