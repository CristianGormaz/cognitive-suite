from __future__ import annotations

import asyncio
import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, Protocol, Sequence

from core.iafa_auditor import IafaAuditor


ACOUSTIC_BRIDGE_VERSION = "acoustic-bridge.v1"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHUNK_SIZE = 4000
DEFAULT_PIPER_TIMEOUT_SECONDS = 30

TextRecognizedCallback = Callable[[str], Awaitable[None] | None]


class AcousticBridgeError(RuntimeError):
    """Base error for acoustic bridge failures."""


class AcousticInputUnavailableError(AcousticBridgeError):
    """Raised when audio input dependencies or microphone are unavailable."""


class BlockingSpeechRecognizer(Protocol):
    def recognize_forever(self, stop_event: threading.Event, emit_text: Callable[[str], None]) -> None:
        """Block while reading audio and call emit_text with finalized phrases."""


class ExecutorRunner(Protocol):
    async def __call__(self, function: Callable[..., Any], *args: Any) -> Any:
        """Run blocking work and return its result without blocking the event loop."""


class _VoskBlockingRecognizer:
    """
    Blocking STT adapter using Vosk + PyAudio.

    This class is intentionally sync so AcousticBridge can isolate it in an
    executor thread and keep the Qt/qasync event loop responsive.
    """

    def __init__(
        self,
        model_path: str,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        device_index: Optional[int] = None,
    ) -> None:
        if not isinstance(model_path, str) or not model_path.strip():
            raise ValueError("model_path must be a non-empty string")
        if sample_rate <= 0:
            raise ValueError("sample_rate must be greater than zero")
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        self.model_path = model_path.strip()
        self.sample_rate = int(sample_rate)
        self.chunk_size = int(chunk_size)
        self.device_index = device_index

    def recognize_forever(self, stop_event: threading.Event, emit_text: Callable[[str], None]) -> None:
        if not isinstance(stop_event, threading.Event):
            raise TypeError("stop_event must be a threading.Event")

        try:
            import pyaudio
        except ImportError as exc:
            raise AcousticInputUnavailableError("PyAudio is not installed") from exc

        try:
            from vosk import KaldiRecognizer, Model
        except ImportError as exc:
            raise AcousticInputUnavailableError("Vosk is not installed") from exc

        model_dir = Path(self.model_path)
        if not model_dir.exists():
            raise AcousticInputUnavailableError(f"Vosk model path not found: {model_dir}")

        try:
            model = Model(str(model_dir))
        except Exception as exc:
            raise AcousticInputUnavailableError(f"Failed to load Vosk model: {exc}") from exc

        audio_interface = pyaudio.PyAudio()
        stream = None
        try:
            try:
                stream = audio_interface.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=self.chunk_size,
                    input_device_index=self.device_index,
                )
            except Exception as exc:
                raise AcousticInputUnavailableError(f"Microphone is unavailable: {exc}") from exc

            recognizer = KaldiRecognizer(model, self.sample_rate)
            while not stop_event.is_set():
                try:
                    audio_chunk = stream.read(self.chunk_size, exception_on_overflow=False)
                except Exception as exc:
                    raise AcousticInputUnavailableError(f"Audio capture failed: {exc}") from exc

                if not audio_chunk:
                    continue

                if recognizer.AcceptWaveform(audio_chunk):
                    _emit_vosk_result_text(recognizer.Result(), emit_text)

            _emit_vosk_result_text(recognizer.FinalResult(), emit_text)
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                except Exception:
                    pass
                try:
                    stream.close()
                except Exception:
                    pass
            try:
                audio_interface.terminate()
            except Exception:
                pass


class AcousticBridge:
    """
    Async acoustic bridge for Greys-v3 (perception-only).

    Responsibilities:
    - Consume blocking STT in an executor and forward recognized text to the
      async world via callback and/or queue.
    - Execute Piper TTS in an executor.
    - Degrade to mute mode when microphone access is unavailable.
    """

    def __init__(
        self,
        on_text_recognized_callback: Optional[TextRecognizedCallback] = None,
        recognized_text_queue: Optional[asyncio.Queue[str]] = None,
        auditor: Optional[IafaAuditor] = None,
        recognizer_backend: Optional[BlockingSpeechRecognizer] = None,
        vosk_model_path: Optional[str] = None,
        vosk_sample_rate: int = DEFAULT_SAMPLE_RATE,
        vosk_chunk_size: int = DEFAULT_CHUNK_SIZE,
        vosk_device_index: Optional[int] = None,
        piper_binary: str = "piper",
        piper_model_path: Optional[str] = None,
        piper_extra_args: Optional[Sequence[str]] = None,
        piper_timeout_seconds: int = DEFAULT_PIPER_TIMEOUT_SECONDS,
        executor_runner: Optional[ExecutorRunner] = None,
    ) -> None:
        if on_text_recognized_callback is not None and not callable(on_text_recognized_callback):
            raise TypeError("on_text_recognized_callback must be callable")
        if recognized_text_queue is not None and not isinstance(recognized_text_queue, asyncio.Queue):
            raise TypeError("recognized_text_queue must be an asyncio.Queue")
        if auditor is not None and not isinstance(auditor, IafaAuditor):
            raise TypeError("auditor must be an IafaAuditor")
        if not isinstance(piper_binary, str) or not piper_binary.strip():
            raise TypeError("piper_binary must be a non-empty string")
        if piper_model_path is not None and not isinstance(piper_model_path, str):
            raise TypeError("piper_model_path must be a string or None")
        if piper_timeout_seconds <= 0:
            raise ValueError("piper_timeout_seconds must be greater than zero")

        self.on_text_recognized_callback = on_text_recognized_callback
        self.recognized_text_queue = recognized_text_queue
        self.auditor = auditor
        self.piper_binary = piper_binary.strip()
        self.piper_model_path = piper_model_path.strip() if piper_model_path else None
        self.piper_extra_args = list(piper_extra_args or [])
        self.piper_timeout_seconds = int(piper_timeout_seconds)
        self._executor_runner = executor_runner

        if recognizer_backend is not None:
            self._recognizer_backend = recognizer_backend
        else:
            model_path = vosk_model_path or os.getenv("GREYS_VOSK_MODEL_PATH", "assets/models/vosk")
            self._recognizer_backend = _VoskBlockingRecognizer(
                model_path=model_path,
                sample_rate=vosk_sample_rate,
                chunk_size=vosk_chunk_size,
                device_index=vosk_device_index,
            )

        self._stop_event = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._listening = False
        self._mute_mode = False
        self._last_error: Optional[str] = None

    @property
    def is_listening(self) -> bool:
        return self._listening

    @property
    def is_muted(self) -> bool:
        return self._mute_mode

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def request_stop(self) -> None:
        self._stop_event.set()

    async def listen_continuously(self) -> None:
        if self._mute_mode:
            await self._audit_event(
                "acoustic_listen_skipped",
                {"reason": "bridge_muted", "last_error": self._last_error},
            )
            return

        if self._listening:
            return

        self._loop = asyncio.get_running_loop()
        self._stop_event.clear()
        self._listening = True
        try:
            await self._run_blocking(self._recognize_blocking_loop)
        except AcousticInputUnavailableError as exc:
            self._mute_mode = True
            self._last_error = str(exc)
            await self._audit_event(
                "acoustic_bridge_muted",
                {
                    "reason": "input_unavailable",
                    "error_type": exc.__class__.__name__,
                    "error": str(exc),
                },
            )
        except Exception as exc:
            self._mute_mode = True
            self._last_error = f"{exc.__class__.__name__}: {exc}"
            await self._audit_event(
                "acoustic_bridge_muted",
                {
                    "reason": "input_runtime_error",
                    "error_type": exc.__class__.__name__,
                    "error": str(exc),
                },
            )
        finally:
            self._listening = False

    async def speak(self, text: str) -> bool:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")

        if self._mute_mode:
            await self._audit_event(
                "acoustic_tts_skipped",
                {"reason": "bridge_muted", "text_length": len(text)},
            )
            return False

        try:
            await self._run_blocking(self._speak_blocking, text.strip())
            await self._audit_event(
                "acoustic_tts_completed",
                {"text_length": len(text.strip())},
            )
            return True
        except Exception as exc:
            self._last_error = f"{exc.__class__.__name__}: {exc}"
            await self._audit_event(
                "acoustic_tts_error",
                {
                    "error_type": exc.__class__.__name__,
                    "error": str(exc),
                    "text_length": len(text.strip()),
                },
            )
            return False

    def _recognize_blocking_loop(self) -> None:
        loop = self._loop
        if loop is None:
            raise AcousticBridgeError("listen_continuously must be called from an active event loop")

        def emit_text(text: str) -> None:
            normalized = text.strip()
            if not normalized:
                return
            if loop.is_closed():
                return
            loop.call_soon_threadsafe(self._handle_recognized_text, normalized)

        self._recognizer_backend.recognize_forever(self._stop_event, emit_text)

    def _handle_recognized_text(self, text: str) -> None:
        if self.recognized_text_queue is not None:
            try:
                self.recognized_text_queue.put_nowait(text)
            except asyncio.QueueFull:
                self._schedule_audit(
                    "acoustic_recognition_queue_full",
                    {"reason": "queue_full", "dropped_text_preview": text[:120]},
                )

        callback = self.on_text_recognized_callback
        if callback is None:
            return

        try:
            outcome = callback(text)
        except Exception as exc:
            self._schedule_audit(
                "acoustic_recognition_callback_error",
                {"error_type": exc.__class__.__name__, "error": str(exc)},
            )
            return

        if asyncio.iscoroutine(outcome):
            task = asyncio.create_task(outcome)
            task.add_done_callback(self._handle_callback_task_done)

    def _handle_callback_task_done(self, task: asyncio.Task[Any]) -> None:
        try:
            task.result()
        except Exception as exc:
            self._schedule_audit(
                "acoustic_recognition_callback_error",
                {"error_type": exc.__class__.__name__, "error": str(exc)},
            )

    def _speak_blocking(self, text: str) -> None:
        command = [self.piper_binary]
        if self.piper_model_path:
            command.extend(["--model", self.piper_model_path])
        command.extend(self.piper_extra_args)

        try:
            completed = subprocess.run(
                command,
                input=text.encode("utf-8"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=False,
                timeout=self.piper_timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise AcousticBridgeError(f"Piper binary not found: {self.piper_binary}") from exc
        except subprocess.TimeoutExpired as exc:
            raise AcousticBridgeError(f"Piper synthesis timed out: {exc}") from exc
        except OSError as exc:
            raise AcousticBridgeError(f"Piper invocation failed: {exc}") from exc

        if completed.returncode != 0:
            stderr_text = completed.stderr.decode("utf-8", errors="ignore").strip()
            reason = stderr_text if stderr_text else f"exit_code={completed.returncode}"
            raise AcousticBridgeError(f"Piper synthesis failed: {reason}")

    async def _audit_event(self, record_type: str, details: dict[str, Any]) -> None:
        if not self.auditor:
            return

        payload = {
            "timestamp": time.time(),
            "record_type": record_type,
            "acoustic_bridge_version": ACOUSTIC_BRIDGE_VERSION,
            "details": details,
        }
        try:
            await self.auditor.append_payload(payload)
        except Exception:
            return

    def _schedule_audit(self, record_type: str, details: dict[str, Any]) -> None:
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        loop.create_task(self._audit_event(record_type, details))

    async def _run_blocking(self, function: Callable[..., Any], *args: Any) -> Any:
        if self._executor_runner is not None:
            return await self._executor_runner(function, *args)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, function, *args)


def _emit_vosk_result_text(result_json: str, emit_text: Callable[[str], None]) -> None:
    try:
        payload = json.loads(result_json)
    except json.JSONDecodeError:
        return

    if not isinstance(payload, dict):
        return

    text = payload.get("text")
    if not isinstance(text, str):
        return

    normalized = text.strip()
    if normalized:
        emit_text(normalized)
