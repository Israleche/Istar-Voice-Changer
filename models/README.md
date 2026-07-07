# Voice Models (Istar Voice Changer)

This folder holds the ONNX models used by the RVC engine. All models here are
**MIT-licensed** exports — no PyTorch, no fairseq, no CUDA build required.

## Files

| File | What it is | License | Source |
|------|------------|---------|--------|
| `contentvec.onnx` | ContentVec-768 (HuBERT) feature extractor, 360 MB | MIT | [TigreGotico/voiceclonnx-rvc](https://huggingface.co/TigreGotico/voiceclonnx-rvc) (Hubert export, parity vs torch) |
| `voices/default.onnx` | Example RVC v2 voice generator (net_g), 105 MB | MIT | [Cycl0/voice-changer-models](https://huggingface.co/Cycl0/voice-changer-models) `rvc_full.onnx` |

## Adding your own voices

Drop any RVC v2 voice exported to ONNX into `voices/`. The launcher lists every
`*.onnx` in this folder automatically.

To convert a community `.pth` voice model to ONNX (the 3-input `phone, pitch,
pitchf` format used here), use a browser-based converter such as
[rvc-onnx-web](https://huggingface.co/spaces/...) or export from Applio. The
resulting `your_voice.onnx` works out of the box.

## Licensing note

RVC is originally by [RVC-Project](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)
(MIT). Community voice models are trained by third parties and may carry their
own terms — use only lawfully-obtained, appropriately-licensed weights, and
respect the non-commercial / attribution terms of each model you add.
