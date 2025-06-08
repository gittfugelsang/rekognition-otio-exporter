import os
import tkinter as tk
from tkinter import messagebox, filedialog
import pandas as pd
import opentimelineio as otio
from opentimelineio.opentime import RationalTime, TimeRange

# Dynamically set the CSV directory relative to the script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, "data")

LABEL_FILES = {
    "Label": os.path.join(CSV_DIR, "labels.csv"),
    "Face": os.path.join(CSV_DIR, "faces.csv"),
    "Text": os.path.join(CSV_DIR, "text.csv"),
}

DEFAULT_DURATION_SECONDS = 180

def load_all_rows():
    results = []
    for key, path in LABEL_FILES.items():
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            confidence = row.get("Confidence")
            timestamp_sec = row["Timestamp(ms)"] / 1000.0
            if timestamp_sec > DEFAULT_DURATION_SECONDS:
                continue
            if confidence < 70:
                continue
            if key == "Label":
                label = row.get("Label")
            elif key == "Face":
                label = row.get("MatchedName")
            else:
                label = row.get("DetectedText")
            results.append({
                "file_name": os.path.basename(row["Video"]),
                "label": label,
                "start_time": timestamp_sec,
                "duration": 1.0,
                "confidence": confidence,
                "label_type": key,
            })
    return results

def create_otio_clip(row, fps=24):
    print(f"Creating clip for {row['file_name']} at time {row['start_time']}s")
    media_ref = otio.schema.ExternalReference(
        target_url=row["file_name"],
        available_range=TimeRange(
            start_time=RationalTime(0, fps),
            duration=RationalTime(DEFAULT_DURATION_SECONDS, fps)
        )
    )
    clip = otio.schema.Clip(
        name=f"{row['file_name']} Tags",
        media_reference=media_ref,
        source_range=TimeRange(
            start_time=RationalTime(row["start_time"], fps),
            duration=RationalTime(DEFAULT_DURATION_SECONDS, fps)
        )
    )

    color_map = {
        "Face": otio.schema.MarkerColor.BLUE,
        "Label": otio.schema.MarkerColor.GREEN,
        "Text": otio.schema.MarkerColor.MAGENTA
    }
    marker_color = color_map.get(row["label_type"], otio.schema.MarkerColor.RED)

    marker = otio.schema.Marker(
        name=row["label"],
        marked_range=TimeRange(
            start_time=RationalTime(0, fps),
            duration=RationalTime(1.0, fps)
        ),
        metadata={"label_type": row["label_type"], "confidence": row["confidence"]},
        color=marker_color
    )
    clip.markers.append(marker)
    return clip

def export_to_otio(selected_rows):
    if not selected_rows:
        messagebox.showwarning("Nothing Selected", "Please select events to export.")
        return
    output_path = filedialog.asksaveasfilename(
        title="Save OTIO File As",
        defaultextension=".otio",
        initialdir=CSV_DIR,
        initialfile="filtered_output.otio",
        filetypes=[("OpenTimelineIO", "*.otio")]
    )
    if not output_path:
        return

    from collections import defaultdict
    grouped = defaultdict(list)
    for row in selected_rows:
        grouped[row["file_name"]].append(row)

    timeline = otio.schema.Timeline(name="Filtered Rekognition Tags")
    track = otio.schema.Track(name="Filtered", kind=otio.schema.TrackKind.Video)

    for file_name, rows in grouped.items():
        first_row = rows[0]
        min_time = min(row["start_time"] for row in rows)

        media_ref = otio.schema.ExternalReference(
            target_url=file_name,
            available_range=TimeRange(
                start_time=RationalTime(0, 24),
                duration=RationalTime(DEFAULT_DURATION_SECONDS, 24)
            )
        )
        clip = otio.schema.Clip(
            name=f"{file_name} Tags",
            media_reference=media_ref,
            source_range=TimeRange(
                start_time=RationalTime(0, 24),
                duration=RationalTime(DEFAULT_DURATION_SECONDS, 24)
            )
        )
        color_map = {
            "Face": otio.schema.MarkerColor.BLUE,
            "Label": otio.schema.MarkerColor.GREEN,
            "Text": otio.schema.MarkerColor.MAGENTA
        }
        for row in rows:
            print(f"Marker at {row['start_time'] - min_time:.2f}s for {row['label']}")
            marker = otio.schema.Marker(
                name=row["label"],
                marked_range=TimeRange(
                    start_time=RationalTime(row["start_time"] - min_time, 24),
                    duration=RationalTime(1.0, 24)
                ),
                metadata={"label_type": row["label_type"], "confidence": row["confidence"]},
                color=color_map.get(row["label_type"], otio.schema.MarkerColor.RED)
            )
            clip.markers.append(marker)
        track.append(clip)

    timeline.tracks.append(track)
    otio.adapters.write_to_file(timeline, output_path)
    messagebox.showinfo("Export Successful", f"Saved to:\n{output_path}")

def launch_gui():
    all_rows = load_all_rows()
    root = tk.Tk()
    root.title("Rekognition OTIO Exporter")
    root.geometry("800x700")

    tk.Label(root, text="Enter Face Label").pack()
    face_entry = tk.Entry(root)
    face_entry.pack()

    tk.Label(root, text="Enter Object Label").pack()
    label_entry = tk.Entry(root)
    label_entry.pack()

    tk.Label(root, text="Enter Text Label").pack()
    text_entry = tk.Entry(root)
    text_entry.pack()

    checkbox_vars = []
    checkbox_rows = []
    canvas_frame = tk.Frame(root)
    canvas_frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(canvas_frame)
    scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    result_frame = scrollable_frame

    def clear_results():
        for widget in result_frame.winfo_children():
            widget.destroy()
        checkbox_vars.clear()
        checkbox_rows.clear()

    def apply_filter():
        clear_results()
        face_val = face_entry.get().strip().lower()
        label_val = label_entry.get().strip().lower()
        text_val = text_entry.get().strip().lower()

        queries = []
        if face_val:
            queries.append(("Face", face_val))
        if label_val:
            queries.append(("Label", label_val))
        if text_val:
            queries.append(("Text", text_val))

        if not queries:
            messagebox.showinfo("No Input", "Please enter at least one search term.")
            return

        file_sets = []
        for typ, q in queries:
            matched_files = {
                row["file_name"]
                for row in all_rows
                if row["label_type"] == typ and q in row["label"].strip().lower()
            }
            if matched_files:
                file_sets.append(matched_files)

        if len(file_sets) != len(queries):
            messagebox.showinfo("No Results", "No matching tags found.")
            return

        valid_files = set.intersection(*file_sets)
        filtered_rows = []
        for row in all_rows:
            if row["file_name"] in valid_files:
                if any(row["label_type"] == typ and q in row["label"].strip().lower() for typ, q in queries):
                    filtered_rows.append(row)

        for row in filtered_rows:
            var = tk.BooleanVar()
            checkbox_vars.append(var)
            checkbox_rows.append(row)
            display = f"{row['file_name']} | {row['label']} ({row['label_type']}) @ {row['start_time']}s"
            cb = tk.Checkbutton(result_frame, text=display, variable=var, anchor='w', width=100, justify='left')
            cb.pack(fill='x', padx=10, pady=2)

        if not checkbox_rows:
            messagebox.showinfo("No Results", "No matching tags found.")

    def export_selected():
        selected = [row for var, row in zip(checkbox_vars, checkbox_rows) if var.get()]
        export_to_otio(selected)

    tk.Button(root, text="Apply Filter", command=apply_filter, bg="#2196F3", fg="black").pack(pady=5)
    tk.Button(root, text="Export Selected to OTIO", command=export_selected, bg="#4CAF50", fg="black").pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    launch_gui()
