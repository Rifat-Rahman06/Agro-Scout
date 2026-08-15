# 🤖 Rover — Model Guide

The rover runs two **TensorFlow Lite** models onboard the Raspberry Pi. It only needs these two files in `models/`:

| File                   | Model        | Purpose                                 |
| ---------------------- | ------------ | --------------------------------------- |
| `leaf_detect.tflite`   | YOLO         | finds leaves (bounding boxes)           |
| `leaf_classify.tflite` | EfficientNet | classifies each leaf healthy / diseased |

## Which model to train first

**Train the detector (`leaf_detect.tflite`) first.** Disease classification only runs on leaves the detector has found, so a good detector is the foundation. Once leaves are reliably detected, train the classifier.

### 1. Detector (YOLO)

* **Data:** leaf photos + one `.txt` label per photo (YOLO format, one line per leaf: `class x y w h`).
* **Train (on a PC):** Train a lightweight YOLO model to detect leaves.
* **Output:** `best.pt`.

### 2. Classifier (EfficientNet)

* **Data:** cropped leaf images in two folders — `healthy/` and `diseased/`.
* **Train (on a PC):** a simple Keras model (EfficientNetB0 + `sigmoid`, binary `healthy/diseased`), saved as `efficientnet_model.h5`. Keep **class index 1 = diseased** (that's what `rover.py` expects).
* **Output:** `efficientnet_model.h5`.

## Convert to `.tflite` (once, on a PC)

### Detector

```text
YOLO model (.pt) → Export to ONNX → ONNX model (.onnx) → Convert to TensorFlow Lite → leaf_detect.tflite
```

### Classifier

```text
Keras / EfficientNet model (.h5) → Convert to TensorFlow Lite → leaf_classify.tflite
```

Only the two `.tflite` files go in this repo and onto the Pi. The source files (`best.pt`, `.h5`) stay on your PC.

## Install on the Raspberry Pi

```bash
cd rover
pip install -r requirements.txt    # includes tflite-runtime
# copy leaf_detect.tflite and leaf_classify.tflite into models/
```

`rover.py` loads them automatically from `rover/models/` on startup.

## Detection settings (code defaults)

| Setting              | Value                |
| -------------------- | -------------------- |
| Detection confidence | 0.7                  |
| NMS IoU threshold    | 0.45                 |
| Disease probability  | 0.7                  |
| Detector input       | letterbox, RGB, ÷255 |
| Classifier input     | resized, BGR, ÷255   |

> If detections look weak on your camera, remove the `cv2.COLOR_BGR2RGB` conversion in `detect_leaves()` (feed BGR frames instead).
