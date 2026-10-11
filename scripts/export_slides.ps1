# Render every slide of a PowerPoint file to 1920x1080 PNG through PowerPoint COM (Windows).
# Safety: ingest.py passes a COPY of the user's deck. If PowerPoint is already running with other presentations open,
# this script never closes or quits them (a previous run discarded a user's unsaved edits by calling Quit()).
param([Parameter(Mandatory=$true)][string]$Pptx, [Parameter(Mandatory=$true)][string]$OutDir, [int]$Width = 1920, [int]$Height = 1080)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force $OutDir | Out-Null
$wasRunning = [bool](Get-Process POWERPNT -ErrorAction SilentlyContinue)
$app = New-Object -ComObject PowerPoint.Application
$openBefore = $app.Presentations.Count
$pres = $app.Presentations.Open((Resolve-Path $Pptx).Path, $true, $false, $false)   # read-only, no window
$n = $pres.Slides.Count
for ($i = 1; $i -le $n; $i++) {
  $bmp = Join-Path $OutDir ("slide{0:D2}.bmp" -f $i)
  $pres.Slides.Item($i).Export($bmp, "BMP", $Width, $Height)       # lossless, then converted to PNG by Python
}
$pres.Close()
if (-not $wasRunning -and $openBefore -eq 0) { $app.Quit() }
python -c "import glob,os;from PIL import Image;[ (Image.open(f).convert('RGB').save(f[:-4]+'.png',optimize=True), os.remove(f)) for f in glob.glob(os.path.join(r'$OutDir','slide*.bmp'))]"
"exported $n slides to $OutDir"
