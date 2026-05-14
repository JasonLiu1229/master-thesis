# Usage: .\pick_files.ps1 -SourceDir <source> -TargetDir <target> [-IndicesFile <file>]
# Copies TestClass{INDEX}_java.jsonl files listed in indices file from source to target.
# Defaults to indices.txt in the current directory if not specified.

param(
    [Parameter(Mandatory)][string]$SourceDir,
    [Parameter(Mandatory)][string]$TargetDir,
    [string]$IndicesFile = "indices.txt"
)

if (-not (Test-Path $IndicesFile)) {
    Write-Error "Indices file '$IndicesFile' not found."
    exit 1
}

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

$found = 0
$missing = 0

Get-Content $IndicesFile | ForEach-Object {
    $idx = $_.Trim()

    # Skip blank lines or comments
    if ($idx -eq "" -or $idx.StartsWith("#")) { return }

    $filename = "TestClass${idx}.java.jsonl"
    $src = Join-Path $SourceDir $filename

    if (Test-Path $src) {
        Copy-Item $src -Destination (Join-Path $TargetDir $filename)
        Write-Host "Copied: $filename"
        $found++
    } else {
        Write-Warning "Missing: $filename"
        $missing++
    }
}

Write-Host ""
Write-Host "Done - copied: $found, missing: $missing"
