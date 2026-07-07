#!/usr/bin/env python3
"""
Istar Voice Changer - RVC ONNX inference engine (MIT)
=====================================================

A self-contained, dependency-light voice-conversion engine built on RVC
(Retrieval-based Voice Conversion) exported to ONNX. It uses:

  * ContentVec-768 (HuBERT) ONNX  -> content/pitch-discarded features
  * net_g (voice generator) ONNX  -> target-voice audio synthesis
  * Yin (librosa)                 -> F0 / pitch (no extra model needed)

No PyTorch, no fairseq, no C++ build step. Only onnxruntime + librosa + numpy
+ soundfile. This keeps the distributable small and the license MIT-friendly.

The engine supports two modes:
  * offline file conversion  (convert_file)
  * real-time streaming       (open_stream / process_chunk) driven by PyAudio

Model sources (all MIT):
  * ContentVec-768 ONNX: TigreGotico/voiceclonnx-rvc (Hubert export)
  * Voice models:      community RVC v2 .pth exported to ONNX (e.g. via
                       rvc-onnx-web / EchoRVC). The bundled default voice is
                       Cycl0/voice-changer-models rvc_full.onnx.
"""

from __future__ import annotations

import numpy as np
import onnxruntime as ort
import librosa
import soundfile as sf

# RVC generator runs at 40 kHz with a 512-sample hop (matches the ONNX export).
RVC_SR = 40000
RVC_HOP = 512
CONTENT_SR = 16000  # HuBERT / ContentVec operates at 16 kHz

F0_MIN = 50.0
F0_MAX = 1100.0


class RVCEngine:
    def __init__(self, contentvec_path: str, voice_model_path: str,
                 device: str = "cpu", n_fft: int = 2048):
        self.device = device
        providers = ["CPUExecutionProvider"] if device in ("cpu", None) else \
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
        self.vec = ort.InferenceSession(contentvec_path, providers=providers)
        self.net = ort.InferenceSession(voice_model_path, providers=providers)
        self.n_fft = n_fft
        # Pre-compute the F0 -> RVC pitch-index mapping constants.
        self._f0_mel_min = 1127.0 * np.log(1.0 + F0_MIN / 700.0)
        self._f0_mel_max = 1127.0 * np.log(1.0 + F0_MAX / 700.0)

    # -------------------------------------------------------------- helpers
    def _content_features(self, wav16k: np.ndarray) -> np.ndarray:
        """Return ContentVec features shaped [1, seq, 768]."""
        feats = wav16k.mean(-1) if wav16k.ndim == 2 else wav16k
        inp = np.expand_dims(feats.astype(np.float32), 0)  # [1, seq]
        mask = np.ones(inp.shape, dtype=np.int64)
        out = self.vec.run(None, {"input_values": inp, "attention_mask": mask})[0]
        return out.astype(np.float32)  # already [1, seq, 768]

    def _pitch(self, wav40k: np.ndarray, seq_len: int) -> tuple[np.ndarray, np.ndarray]:
        """Compute RVC pitch index and continuous pitchf, resampled to seq_len."""
        f0 = librosa.yin(
            wav40k.astype(np.float32), fmin=F0_MIN, fmax=F0_MAX,
            sr=RVC_SR, frame_length=self.n_fft, hop_length=RVC_HOP,
        )
        # Map to seq_len frames (ContentVec frame rate == generator frame rate).
        idx = np.linspace(0, len(f0) - 1, seq_len).astype(int)
        p = f0[idx]
        p[np.isnan(p)] = 0.0
        f0_mel = 1127.0 * np.log(1.0 + p / 700.0)
        f0_mel[p > 0] = (f0_mel[p > 0] - self._f0_mel_min) * 254.0 / \
                        (self._f0_mel_max - self._f0_mel_min) + 1.0
        f0_mel[p <= 0] = 1.0
        f0_mel = np.clip(f0_mel, 1.0, 255.0)
        pitch = np.rint(f0_mel).astype(np.int64).reshape(1, seq_len)
        pitchf = p.astype(np.float32).reshape(1, seq_len)
        return pitch, pitchf

    def _generate(self, phone: np.ndarray, pitch: np.ndarray,
                  pitchf: np.ndarray) -> np.ndarray:
        out = self.net.run(
            None,
            {"phone": phone, "pitch": pitch, "pitchf": pitchf},
        )[0]
        # Output is int16-ish scaled; bring back to float audio.
        return (out.squeeze() / 32768.0).astype(np.float32)

    # -------------------------------------------------------------- offline
    def convert_file(self, in_path: str, out_path: str,
                     pitch_shift: int = 0) -> None:
        wav, _ = librosa.load(in_path, sr=RVC_SR)
        out = self.convert_array(wav, pitch_shift=pitch_shift)
        sf.write(out_path, out, RVC_SR)

    def convert_array(self, wav40k: np.ndarray, pitch_shift: int = 0) -> np.ndarray:
        wav16k = librosa.resample(wav40k, orig_sr=RVC_SR, target_sr=CONTENT_SR)
        phone = self._content_features(wav16k)
        seq = phone.shape[1]
        pitch, pitchf = self._pitch(wav40k, seq)
        if pitch_shift:
            pitchf = pitchf * (2.0 ** (pitch_shift / 12.0))
        audio = self._generate(phone, pitch, pitchf)
        # Trim the generator's padding tail to match input length.
        target = len(wav40k)
        if len(audio) > target:
            audio = audio[:target]
        return audio

    # -------------------------------------------------------------- streaming
    def open_stream(self, chunk_samples: int = RVC_HOP * 8):
        """Prepare a streaming context. Returns a state object for process_chunk."""
        return {"chunk": chunk_samples, "buf": np.zeros(0, dtype=np.float32)}

    def process_chunk(self, state: dict, chunk: np.ndarray,
                      pitch_shift: int = 0) -> np.ndarray:
        """Convert a streaming audio chunk (float32, RVC_SR). Returns audio."""
        # Accumulate so we always feed a decent window to ContentVec/Yin.
        buf = np.concatenate([state["buf"], chunk.astype(np.float32)])
        # Process in windows of at least 0.5 s to stabilise pitch.
        win = max(state["chunk"], int(0.5 * RVC_SR))
        if len(buf) < win:
            state["buf"] = buf
            return np.zeros(0, dtype=np.float32)
        to_proc, state["buf"] = buf[:win], buf[win:]
        return self.convert_array(to_proc, pitch_shift=pitch_shift)


def list_voice_models(voices_dir: str) -> list[str]:
    """Return available .onnx voice model names (without extension)."""
    from pathlib import Path
    d = Path(voices_dir)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.onnx"))
