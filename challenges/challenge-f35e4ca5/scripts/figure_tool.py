"""Inspect actual figure pixels/OCR and map explicitly calibrated pixel positions."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import re
import shutil
import subprocess
from pathlib import Path


def source(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError("expected input-relative source path")
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("source missing or outside input")
    return path


def rgb_image(path: Path) -> tuple[int, int, bytes]:
    # Prefer installed Pillow; retain ImageMagick as the documented fallback.
    try:
        from PIL import Image
    except ImportError:
        Image = None
    if Image is not None:
        with Image.open(path) as im:
            if im.width*im.height > 30_000_000:
                raise ValueError("image too large")
            im = im.convert("RGBA")
            bg = Image.new("RGBA",im.size,"white"); bg.alpha_composite(im)
            rgb = bg.convert("RGB")
            return rgb.width,rgb.height,rgb.tobytes()
    converter = shutil.which("magick") or shutil.which("convert")
    if not converter:
        raise ValueError("ImageMagick is unavailable")
    proc = subprocess.run([converter, str(path), "-background", "white", "-alpha", "remove", "-alpha", "off", "-depth", "8", "ppm:-"],
                          capture_output=True, timeout=60, check=True)
    match = re.match(rb"P6\s+(?:#[^\n]*\s+)*(\d+)\s+(\d+)\s+255\s", proc.stdout)
    if not match:
        raise ValueError("could not decode image to 8-bit RGB")
    width, height = int(match.group(1)), int(match.group(2))
    pixels = proc.stdout[match.end():]
    if width <= 0 or height <= 0 or width*height > 30_000_000 or len(pixels) != width*height*3:
        raise ValueError("image is too large or has an invalid pixel payload")
    return width, height, pixels


def ocr_preview(tsv: bytes, limit: int = 4000) -> dict:
    """Return a bounded, line-grouped OCR preview; the TSV remains authoritative."""
    rows = csv.DictReader(io.StringIO(tsv.decode("utf-8", errors="replace")), delimiter="\t")
    lines, current, previous, count = [], [], None, 0
    for row in rows:
        word = (row.get("text") or "").strip()
        if not word:
            continue
        group = tuple(row.get(key, "") for key in ("page_num", "block_num", "par_num", "line_num"))
        if previous is not None and group != previous and current:
            lines.append(" ".join(current))
            current = []
        current.append(word)
        previous = group
        count += 1
    if current:
        lines.append(" ".join(current))
    text = "\n".join(lines)
    return {"text": text[:limit], "word_count": count, "truncated": len(text) > limit}


def inspect(root: Path, name: str, out: Path) -> dict:
    path = source(root, name)
    width, height, _ = rgb_image(path)
    out.mkdir(parents=True, exist_ok=True)
    ocr = shutil.which("tesseract")
    info = {"file":name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"width":width,"height":height,
            "ocr_tsv":None,"ocr_preview":None,"warnings":["OCR may misread text and numbers; verify against image pixels and original captions."]}
    if ocr:
        try:
            proc = subprocess.run([ocr,str(path),"stdout","tsv"],capture_output=True,timeout=90)
            if proc.returncode == 0:
                (out/"figure_ocr.tsv").write_bytes(proc.stdout)
                info["ocr_tsv"] = "figure_ocr.tsv"
                info["ocr_preview"] = ocr_preview(proc.stdout)
            else:
                info["warnings"].append("OCR failed; manual inspection is required.")
        except (OSError,subprocess.TimeoutExpired):
            info["warnings"].append("OCR unavailable or timed out; manual inspection is required.")
    else:
        info["warnings"].append("Tesseract unavailable; manual inspection is required.")
    (out/"figure_inspection.json").write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return info


def value_at(pixel: float, axis: dict) -> float:
    try:
        p0,p1 = float(axis["pixel0"]),float(axis["pixel1"])
        v0,v1 = float(axis["value0"]),float(axis["value1"])
    except (KeyError,TypeError,ValueError) as exc:
        raise ValueError("axis needs pixel0, pixel1, value0 and value1") from exc
    if not all(math.isfinite(v) for v in (p0,p1,v0,v1,pixel)) or p0 == p1 or v0 == v1:
        raise ValueError("invalid or identical calibration pixels")
    fraction = (pixel-p0)/(p1-p0)
    scale = axis.get("scale", "linear")
    if scale == "linear":
        return v0+fraction*(v1-v0)
    if scale == "log" and v0>0 and v1>0:
        return math.exp(math.log(v0)+fraction*(math.log(v1)-math.log(v0)))
    raise ValueError("scale must be linear or positive logarithmic")


def calibration_check(axis: dict) -> dict:
    """Check independent ticks in pixel space. This does not identify a scale automatically."""
    value_at(float(axis["pixel0"]),axis)
    p0,p1=float(axis["pixel0"]),float(axis["pixel1"])
    v0,v1=float(axis["value0"]),float(axis["value1"])
    tol=float(axis.get("tick_tolerance_px",2))
    if not math.isfinite(tol) or tol < 0: raise ValueError("invalid tick tolerance")
    ticks=axis.get("check_ticks",[])
    residuals=[]
    for tick in ticks:
        pixel,value=float(tick["pixel"]),float(tick["value"])
        if not all(math.isfinite(v) for v in (pixel,value)): raise ValueError("nonfinite check tick")
        if axis.get("scale","linear")=="log":
            if value<=0: raise ValueError("log check tick must be positive")
            frac=(math.log(value)-math.log(v0))/(math.log(v1)-math.log(v0))
        else: frac=(value-v0)/(v1-v0)
        expected=p0+frac*(p1-p0); residual=abs(pixel-expected)
        if residual>tol: raise ValueError("independent tick conflicts with declared axis scale")
        residuals.append(residual)
    return {"check_tick_count":len(ticks),"max_residual_px":max(residuals,default=0),
            "independently_checked":bool(ticks)}

def reading_interval(pixel: float,axis: dict,radius: float) -> list:
    radius=float(radius)
    if not math.isfinite(radius) or radius<0: raise ValueError("invalid pixel uncertainty")
    if not min(axis["pixel0"],axis["pixel1"])<=pixel<=max(axis["pixel0"],axis["pixel1"]):
        raise ValueError("refusing extrapolation beyond calibrated axis")
    return sorted([value_at(pixel-radius,axis),value_at(pixel+radius,axis)])

def digitize(root: Path, config: dict, out: Path) -> dict:
    path = source(root, config.get("image"))
    w,h,pixels = rgb_image(path)
    axes, points = config.get("axes"), config.get("points")
    if not isinstance(axes,dict) or not all(isinstance(axes.get(k),dict) for k in ("x","y")):
        raise ValueError("both axes require explicit calibration")
    if not isinstance(points,list) or not points:
        raise ValueError("at least one explicitly inspected point is required")
    for axis in axes.values():
        if not isinstance(axis.get("unit"),str) or not axis["unit"].strip() or not isinstance(axis.get("evidence"),str) or not axis["evidence"].strip():
            raise ValueError("each axis needs a unit and source evidence")
    calibration={k:calibration_check(axes[k]) for k in ("x","y")}
    rows=[]
    for p in points:
        x,y = p.get("x"),p.get("y")
        if not isinstance(x,int) or not isinstance(y,int) or not (0<=x<w and 0<=y<h):
            raise ValueError("point must be an integer pixel inside the image")
        role=p.get("role")
        if role not in {"data", "reference"}:
            raise ValueError("every pixel needs role 'data' or 'reference'")
        radius=p.get("pixel_radius",1)
        intervals={k:reading_interval(px,axes[k],radius+calibration[k]["max_residual_px"]) for k,px in (("x",x),("y",y))} if role=="data" else {}
        i=(y*w+x)*3
        rows.append({"label":p.get("label"),"role":role,"pixel_x":x,"pixel_y":y,"rgb":list(pixels[i:i+3]),"reading_interval_x":intervals.get("x"),"reading_interval_y":intervals.get("y"),"method":"agent-selected pixel; calibrated estimate" if role=="data" else "non-data reference",
                     "x_value":value_at(x,axes["x"]) if role=="data" else None,
                     "y_value":value_at(y,axes["y"]) if role=="data" else None,
                     "x_one_pixel_delta":abs(value_at(x+1,axes["x"])-value_at(x,axes["x"])) if role=="data" else None,
                     "y_one_pixel_delta":abs(value_at(y+1,axes["y"])-value_at(y,axes["y"])) if role=="data" else None})
    report={"image":config["image"],"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"width":w,"height":h,
            "axes":axes,"calibration":calibration,"points":rows,"warnings":["Point locations and calibration are supplied by the agent and must be checked against the image; pixel rounding alone does not capture line thickness, resolution, OCR or calibration errors.",
                                                       "Do not infer statistical significance, exact values, units or unprovided figure panels."]}
    out.mkdir(parents=True,exist_ok=True)
    (out/"digitized_points.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (out/"digitized_points.csv").open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return report


def tables(root: Path, out: Path) -> dict:
    result=[]
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or path.suffix.lower() not in {".csv",".tsv"}:
            continue
        try:
            with path.open(encoding="utf-8-sig",newline="") as stream:
                rows=list(csv.reader(stream,delimiter="\t" if path.suffix.lower()==".tsv" else ","))
            result.append({"file":path.relative_to(root).as_posix(),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"rows":rows})
        except (OSError,UnicodeError,csv.Error) as exc:
            result.append({"file":path.relative_to(root).as_posix(),"error":str(exc)})
    out.mkdir(parents=True,exist_ok=True)
    (out/"table_inventory.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"table_count":len(result),"note":"Only CSV/TSV are parsed automatically; inspect other provided table formats separately."}


def init(root: Path,out: Path) -> None:
    out.mkdir(parents=True,exist_ok=True)
    target=out/"result.json"
    if target.exists(): return
    case=json.loads((root/"case.json").read_text(encoding="utf-8"))
    contract=case.get("output_contract",{})
    result={k:None for k in contract} if isinstance(contract,dict) else {}
    result.update({"case_id":case.get("case_id"),"status":"partial","sources":[],"uncertainty":["Actual image and all supplied tables still require inspection."],"change_log":[{"action":"initialize"}],
                   "figure_progress":{"writer":"figure_tool.py","phase":"initialized"}})
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def merge_partial(out: Path, phase: str, report: dict) -> None:
    target=out/"result.json"
    if not target.is_file(): return
    result=json.loads(target.read_text(encoding="utf-8"))
    progress=result.get("figure_progress")
    if result.get("status")!="partial" or not isinstance(progress,dict) or progress.get("writer")!="figure_tool.py": return
    if phase=="inspect":
        result["figure"]={"source_file":report["file"],"source_sha256":report["sha256"],
                          "width":report["width"],"height":report["height"],"inspection":"figure_inspection.json",
                          "ocr_tsv":report["ocr_tsv"]}
        result["sources"].append({"file":report["file"],"sha256":report["sha256"],"role":"actual image"})
    elif phase=="tables":
        result["tables"]={"inventory":"table_inventory.json","csv_tsv_files":report["table_count"]}
    elif phase=="digitize":
        if not isinstance(result.get("figure"),dict): result["figure"]={}
        result["figure"]["digitized_points"]="digitized_points.json"
        result["figure"]["digitized_csv"]="digitized_points.csv"
    result["uncertainty"]=["This is an incomplete intermediate result: the Agent must inspect all image elements, all table formats, evidence and case-specific questions."]
    result["change_log"].append({"action":phase,"detail":"Saved actual intermediate artifacts; interpretation remains pending."})
    progress["phase"]=phase
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=["init","inspect","tables","digitize"])
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--out",type=Path,default=Path("/app/output"))
    parser.add_argument("--image")
    parser.add_argument("--config",type=Path)
    args=parser.parse_args()
    if args.command=="init": init(args.input,args.out); report={"initialized":True}
    elif args.command=="inspect": report=inspect(args.input,args.image,args.out)
    elif args.command=="tables": report=tables(args.input,args.out)
    else: report=digitize(args.input,json.loads(args.config.read_text(encoding="utf-8")),args.out)
    if args.command!="init": merge_partial(args.out,args.command,report)
    print(json.dumps(report,ensure_ascii=False))


if __name__=="__main__": main()
