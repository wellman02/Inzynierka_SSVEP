# Build script for LaTeX with artifacts in build/ folder
# Usage: .\build.ps1

$outputDir = ".\build"
$mainFile = "main.tex"

Write-Host "Starting LaTeX compilation with output to: $outputDir" -ForegroundColor Green

# Clean old artifacts from main directory
Write-Host "Cleaning old artifacts from main directory..." -ForegroundColor Yellow
$junkExtensions = @('*.aux', '*.log', '*.bbl', '*.bcf', '*.toc', '*.out', '*.blg', '*.fls', '*.fdb_latexmk', '*.run.xml', '*.synctex.gz', '*-SAVE-ERROR', '*.lof')
foreach ($ext in $junkExtensions) {
    Remove-Item -Path $ext -Force -ErrorAction SilentlyContinue
}

# Ensure build directory exists
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

# 1. First pdflatex pass
Write-Host "1/4: First pdflatex pass..." -ForegroundColor Cyan
& pdflatex -interaction=nonstopmode "-output-directory=$outputDir" $mainFile 2>&1 > $null
$exit1 = $LASTEXITCODE

# 2. Biber (bibliography generation)
Write-Host "2/4: Generating bibliography with biber..." -ForegroundColor Cyan
& biber --output-directory=$outputDir main 2>&1 > $null
$exit2 = $LASTEXITCODE

# 3. Second pdflatex pass
Write-Host "3/4: Second pdflatex pass..." -ForegroundColor Cyan
& pdflatex -interaction=nonstopmode "-output-directory=$outputDir" $mainFile 2>&1 > $null

# 4. Third pdflatex pass (finalization)
Write-Host "4/4: Third pdflatex pass..." -ForegroundColor Cyan
& pdflatex -interaction=nonstopmode "-output-directory=$outputDir" $mainFile 2>&1 > $null

Write-Host "`nCompilation complete!" -ForegroundColor Green
$pdfFound = Get-ChildItem -Path $outputDir -Filter "main.pdf" -ErrorAction SilentlyContinue
$pdfInCwd = Get-ChildItem -Path (Get-Location) -Filter "main.pdf" -ErrorAction SilentlyContinue

if ($pdfFound) {
    Write-Host "PDF successfully generated at: $($pdfFound[0].FullName)" -ForegroundColor Yellow
} elseif ($pdfInCwd) {
    $src = $pdfInCwd[0].FullName
    $dst = Join-Path $outputDir "main.pdf"
    Move-Item -Path $src -Destination $dst -Force
    Write-Host "PDF was generated in project root; moved to: $dst" -ForegroundColor Yellow
} else {
    Write-Host "WARNING: PDF not found in $outputDir\main.pdf" -ForegroundColor Red
}
