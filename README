# GTK Image Viewer

A simple, fast image viewer built with Python and GTK3. It automatically scales images to fit the window and handles large images better than basic viewers.

---

## Features

- Open images with a native file dialog  
- Automatically fits images to the window  
- Maintains aspect ratio (no distortion)  
- Resizes dynamically with the window  
- Supports common formats (PNG, JPEG, TIFF, etc.)  
- Optimized for large images  

---

## Tech Stack

- **Python 3** – core language  
- **GTK3 (PyGObject)** – GUI framework  
- **Pillow** – image loading and processing  
- **Pillow-SIMD (optional)** – faster image resizing  

---

## Why Pillow-SIMD?

Pillow-SIMD is a drop-in replacement for Pillow that speeds up operations like resizing using CPU vector instructions.

This matters because:
- Large images (like 40k × 40k) contain billions of pixels  
- Resizing them is the slowest part of rendering  
- SIMD acceleration can make resizing **2×–5× faster**

---

## Installation

### 1. Install system dependencies (Linux)

Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0
