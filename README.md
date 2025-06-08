# Rekognition OTIO Exporter (Media AI Project)

Please read the entire document before proceeding!

This Python MVP allows users to filter and export Amazon Rekognition video metadata (faces, objects, text) into OpenTimelineIO (`.otio`) format for visual review in DaVinci Resolve.

---

## ✅ Features

- Load metadata from:
  - `faces.csv`
  - `labels.csv`
  - `text.csv`
- Filter by:
  - **Face** (e.g., `Tom`) 
  - **Label** (e.g., `Beach`)
  - **Text** (e.g., `Ice Cream`)
- Checkbox selection of matching events
- Color-coded timeline markers:
  - 🔵 Face
  - 🟢 Label
  - 🟣 Text
- OTIO export with one clip per video, all valid markers included
- Minimally compatible with DaVinci Resolve ONLY.  
---

## 📥 Setup Instructions

### 1. Dependencies

Install Python packages:

```bash
pip install opentimelineio pandas
```

Tkinter is built into most Python distributions. If needed:

```bash
sudo apt-get install python3-tk     # (Linux)
brew install python-tk              # (Mac, if missing)
```

---

### 2. File Structure

Expected folder structure:

```
rekognition-otio-exporter/
├── app.py
├── README.md
├── data/
│   ├── faces.csv
│   ├── labels.csv
│   └── text.csv
├── videos/
│   ├── IMG_0866.mp4
│   └── (any matching video files)
```

**Note:** All Rekognition `.csv` files should be placed in `data/`. Matching video files should live in `videos/`.  Please limit testing to provided videos only.  Adding your own will not produce results in current version!

---

### 3. Run the App

```bash
python app.py
```

---

## 🔍 Search Examples

### ✅ Supported Faces (case-insensitive):
- `Millie`
- `Jojo`
- `Kari`
- `Tom`

### ✅ Sample Labels:
- `Beach`
- `Indoors`
- `Outdoors`
- `Park`
- `Grass`


You can **explore the CSVs directly** to discover more available matches. The system supports **exact matches only**, not partials.

---

## 📦 Output

- One `.otio` timeline file
- Each clip includes all relevant markers from that video
- Marker color indicates metadata type (face/label/text)
- Works with DaVinci Resolve and other OTIO-compatible NLEs

Davinci Resolve Note: Videos must be added to Media Pool prior to receive markers.  Clip selection is accurate, markers need further dev for total frame accuracy.


---

## ⚠️ Known Issues

- ❗ **Markers may exceed clip duration** (default max is 180s). If a video is shorter and metadata is inaccurate, markers may not appear.
- 🧠 **Clip durations are not dynamically detected** — future versions should integrate `ffprobe`.
- ⌛ **Only exact keyword matches are used** for now.
- 🎯 **Video files must be locally accessible** via the `videos/` folder.

---


## Author

**Thomas Fugelsang**  
CSC 510 – Foundations of Artificial Intelligence  
Colorado State University Global
