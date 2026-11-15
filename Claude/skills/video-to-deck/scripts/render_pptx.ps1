# Render slides of a .pptx to PNG with the installed PowerPoint (Windows), for visual QA.
# Use when LibreOffice/pdftoppm are not available. Validate the deck first: a corrupt file
# makes PowerPoint show a repair dialog and this script hangs.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File render_pptx.ps1 -Deck C:\path\deck.pptx -OutDir C:\path\render [-Only "3,7,12"]
param([Parameter(Mandatory)][string]$Deck, [Parameter(Mandatory)][string]$OutDir, [string]$Only = "", [int]$Width = 1600)
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Deck = (Resolve-Path -LiteralPath $Deck).Path
$OutDir = (Resolve-Path -LiteralPath $OutDir).Path
$app = New-Object -ComObject PowerPoint.Application
try {
  $p = $app.Presentations.Open($Deck, $true, $false, $false)   # read-only, no window
  $n = $p.Slides.Count
  $h = [int]($Width * $p.PageSetup.SlideHeight / $p.PageSetup.SlideWidth)
  $list = if ($Only) { $Only.Split(",") | ForEach-Object { [int]$_ } } else { 1..$n }
  foreach ($i in $list) {
    $p.Slides.Item($i).Export((Join-Path $OutDir ("slide-{0:D2}.png" -f $i)), "PNG", $Width, $h)
  }
  "slides: $n; rendered: $($list.Count) -> $OutDir"
  $p.Close()
} finally {
  $app.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
}
