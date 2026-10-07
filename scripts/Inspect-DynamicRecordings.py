"""Create non-destructive media inventories and timestamped contact sheets.

Diagnostic previews are resized; native recordings and later training frames
are never modified. This audit does not certify camera synchronization.
Uses the optional board-print tool environment for Pillow and OpenCV.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageOps


def run(command):
    result = subprocess.run([str(item) for item in command], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:])
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    parser.add_argument("--samples", type=int, default=9)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    session = json.loads(args.session.read_text(encoding="utf-8-sig"))
    root = args.session.parent
    output = args.output or Path(".local/workflows") / session["session_id"] / "audit"
    if output.exists():
        raise ValueError("Audit output already exists; choose a new folder to preserve it")
    tools = json.loads(Path("static-tools.json").read_text(encoding="utf-8-sig"))
    tool = next(item for item in tools["portable_tools"] if item["name"] == "FFmpeg")
    ffmpeg, probe = tool["executable_path"], tool["ffprobe_path"]
    output.mkdir(parents=True)
    records = []
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
    small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
    cell_width, cell_height, columns = 360, 256, 3
    montage = Image.new("RGB", (columns*cell_width, (args.samples+1)*cell_height), "#171b22")
    draw = ImageDraw.Draw(montage)
    for col, camera in enumerate(session["cameras"]):
        video = (root/camera["video"]).resolve()
        metadata = json.loads(run([probe, "-v", "error", "-show_format", "-show_streams", "-of", "json", video]))
        stream = next(s for s in metadata["streams"] if s["codec_type"] == "video")
        count = int(stream["nb_frames"])
        fps_n, fps_d = map(int, stream["avg_frame_rate"].split("/"))
        fps = fps_n/fps_d
        indices = sorted(set(round(i*(count-1)/(args.samples-1)) for i in range(args.samples)))
        frames = output/camera["id"]
        frames.mkdir()
        select = "+".join(f"eq(n,{index})" for index in indices)
        filter_file = frames/"preview_filter.txt"
        filter_file.write_text(f"select='{select}',scale=960:960:force_original_aspect_ratio=decrease", encoding="utf-8")
        run([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-noautorotate", "-i", video,
             "-/filter:v", filter_file, "-fps_mode", "vfr", "-compression_level", "3", frames/"sample_%02d.png"])
        samples = sorted(frames.glob("sample_*.png"))
        if len(samples) != len(indices):
            raise ValueError("FFmpeg preview count does not match selected decoded frames")
        title = f"{session['session_id']} | {camera['id']}"
        x = col*cell_width
        draw.text((x+12, 15), title, font=font, fill="white")
        draw.text((x+12, 46), f"{stream['width']} x {stream['height']} | {fps:.3f} fps", font=small, fill="#cad2de")
        draw.text((x+12, 70), f"{count} frames | {stream.get('color_transfer', 'unknown')} | {stream['pix_fmt']}", font=small, fill="#cad2de")
        draw.text((x+12, 105), "Preview times are file-relative.", font=small, fill="#d8b969")
        draw.text((x+12, 128), "Matching times do not prove synchronization.", font=small, fill="#d8b969")
        frame_records = []
        for row, (index, path) in enumerate(zip(indices, samples), 1):
            with Image.open(path) as image:
                thumbnail = ImageOps.contain(image.convert("RGB"), (cell_width-12, cell_height-38))
                montage.paste(thumbnail, (x+(cell_width-thumbnail.width)//2, row*cell_height+26))
            draw.text((x+12, row*cell_height+4), f"frame {index} | nominal t={index/fps:.3f} s", font=small, fill="white")
            frame_records.append({"decoded_index": index, "nominal_time_s": index/fps,
                                  "preview": str(path.relative_to(output)).replace("\\", "/")})
        records.append({"camera_id": camera["id"], "video": camera["video"], "metadata": metadata,
                        "preview_frames": frame_records})
        print(f"Audited {camera['id']}: {count} frames at {fps:.6f} fps", flush=True)
    montage.save(output/"contact_sheet.jpg", quality=95)
    report = {"schema_version": 1, "session_id": session["session_id"], "sensor_sync_verified": False,
              "preview_only": True, "cameras": records}
    (output/"media_inventory.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(f"Contact sheet: {output/'contact_sheet.jpg'}", flush=True)


if __name__ == "__main__":
    main()
