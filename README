# GTK Image Viewer

A simple, fast image viewer built with Python and GTK3. It focuses on handling large images more efficiently than typical basic viewers by automatically scaling them to fit the window.

---

## Preview

Lightweight GTK interface with automatic image fitting and responsive resizing.

---

## Features

* Open images with a native file dialog
* Automatically fits images to the window
* Maintains aspect ratio (no distortion)
* Updates image size when the window is resized
* Works with common formats (PNG, JPEG, TIFF, etc.)
* Optimized for large images

---

## Tech Stack

* **Python 3** – core language
* **GTK3 (PyGObject)** – GUI framework
* **Pillow** – image loading and processing
* **Pillow-SIMD (optional)** – faster image resizing

---

## Why Pillow-SIMD?

Pillow-SIMD is a drop-in replacement for Pillow that speeds up operations like resizing.

This matters because:

* Large images (like 40k × 40k) contain billions of pixels
* Resizing them is the slowest part of rendering
* SIMD acceleration can make resizing **2×–5× faster**

---

## Installation

### 1. Install system dependencies (Linux)

Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

---

### 2. Clone the repository

```bash
git clone https://github.com/yourusername/gtk-image-viewer.git
cd gtk-image-viewer
```

---

### 3. Install Python dependencies

#### Option A (standard)

```bash
pip install pillow
```

#### Option B (recommended – faster)

```bash
pip uninstall pillow
CC="cc -mavx2" pip install --no-cache-dir pillow-simd
```

---

### 4. Run the app

```bash
python3 main.py
```

---

## Performance Notes

This app can open very large images, but there are some limits:

* Huge TIFF files may use **several GB of RAM**
* Loading time depends on disk speed and image compression
* Resizing cost grows with image size

Using Pillow-SIMD improves performance, but for extremely large images (e.g., >1 billion pixels), more advanced approaches may be needed.

---

## Limitations

* Loads full image into memory (can be heavy for massive files)
* No zoom/pan yet
* No GPU acceleration

---

## Future Improvements

* Smooth zoom (scroll wheel)
* Click-and-drag panning
* Image centering
* Better handling of massive images (tiling/streaming)
* Possible integration with pyvips for huge TIFF support

---

## License

MIT License
