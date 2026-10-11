"""Check (and say how to install) everything the pipeline needs. Run first; install what is missing yourself.
usage: python check_env.py
Machines often have several Pythons; if this one lacks packages, the script lists other interpreters that already have
them. Use that interpreter for EVERY script of the pipeline (call it $PY in your commands)."""
import glob, importlib, os, shutil, subprocess, sys

ok = True
NEED = [("faster_whisper", "faster-whisper"), ("soundfile", "soundfile"), ("scipy", "scipy"), ("numpy", "numpy"), ("PIL", "pillow")]


def row(name, good, hint=""):
    global ok
    ok &= bool(good)
    print(f"{'OK ' if good else 'MISSING'}  {name}" + ("" if good else f"   -> {hint}"))


def other_pythons():
    cands = set()
    for name in ("python", "python3"):
        cmd = ["where", name] if os.name == "nt" else ["which", "-a", name]
        out = subprocess.run(cmd, capture_output=True, text=True).stdout
        cands.update(l.strip() for l in out.splitlines() if l.strip())
    if os.name == "nt":
        out = subprocess.run(["py", "-0p"], capture_output=True, text=True).stdout if shutil.which("py") else ""
        cands.update(l.split()[-1] for l in out.splitlines() if l.strip().endswith(".exe"))
        cands.update(glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python3*\python.exe")))
    cands = {c for c in cands if "WindowsApps" not in c and os.path.exists(c) and os.path.abspath(c) != os.path.abspath(sys.executable)}
    probe = "import " + ", ".join(m for m, _ in NEED)
    return [c for c in sorted(cands) if subprocess.run([c, "-c", probe], capture_output=True).returncode == 0]


print(f"interpreter: {sys.executable} (Python {sys.version.split()[0]})")
sys.path.insert(0, os.path.dirname(__file__))
try:
    from common import ffmpeg, ffprobe
    row("ffmpeg/ffprobe", ffmpeg() and ffprobe(), "winget install Gyan.FFmpeg (or set FFMPEG_DIR)")
except SystemExit as e:
    row("ffmpeg/ffprobe", False, str(e))
missing = []
for mod, pipn in NEED:
    try:
        importlib.import_module(mod)
        row(f"python: {mod}", True)
    except ImportError:
        missing.append(pipn)
        row(f"python: {mod}", False, f"pip install {pipn}")
try:
    import ctranslate2
    n = ctranslate2.get_cuda_device_count()
    print(f"info     Whisper device: {'CUDA (' + str(n) + ' GPU)' if n else 'CPU int8 (large-v3 runs about 1-2x real time; fine for a 6-minute talk)'}")
except Exception:
    pass
row("node + npm", shutil.which("node") and (shutil.which("npm") or shutil.which("npm.cmd")), "install Node.js 18+ (winget install OpenJS.NodeJS.LTS)")
pp = os.name == "nt" and any(os.path.exists(os.path.expandvars(p)) for p in (r"%ProgramFiles%\Microsoft Office\root\Office16\POWERPNT.EXE",
                                                                              r"%ProgramFiles(x86)%\Microsoft Office\root\Office16\POWERPNT.EXE"))
lo = shutil.which("soffice") or shutil.which("libreoffice") or os.path.exists(r"C:\Program Files\LibreOffice\program\soffice.exe")
row("slide rendering (PowerPoint or LibreOffice)", pp or lo, "install LibreOffice, or ask the user for a PDF export of the deck")
try:
    importlib.import_module("fitz")
    row("python: pymupdf (PDF decks)", True)
except ImportError:
    print("info     pip install pymupdf  (only needed for PDF decks or the LibreOffice route)")
if missing:
    good = other_pythons()
    if good:
        print("\nthese interpreters already have the Python packages; run every script with one of them:")
        for g in good:
            print("   ", g)
print("\nall good" if ok else "\ninstall the missing items (or switch interpreter), then re-run")
