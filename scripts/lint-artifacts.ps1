# Optional anti-pattern lint pass for paperboard-rendered HTML artifacts.
# Uses pbakaus/impeccable's detection rules. Non-blocking by default.
# Exits non-zero on Critical/High findings (CI can gate on this).
#
# Usage:
#   .\scripts\lint-artifacts.ps1                              # lints examples\output\*.html
#   .\scripts\lint-artifacts.ps1 -Targets path\to\file.html   # lints supplied paths
#   .\scripts\lint-artifacts.ps1 -Targets path\to\dir         # lints a directory

param([string[]]$Targets = @('examples\output\*.html'))

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    Write-Host "lint-artifacts: npx not found. Install Node.js to use this optional lint." -ForegroundColor Yellow
    exit 0
}

$resolved = New-Object System.Collections.Generic.List[string]
foreach ($t in $Targets) {
    if ($t -match '[\*\?\[]') {
        $matched = @(Get-ChildItem -Path $t -ErrorAction SilentlyContinue -File | ForEach-Object { $_.FullName })
        if ($matched.Count -eq 0) {
            Write-Host "lint-artifacts: no files matched '$t'" -ForegroundColor Yellow
        } else {
            $matched | ForEach-Object { $resolved.Add($_) }
        }
    } else {
        $resolved.Add($t)
    }
}

if ($resolved.Count -eq 0) {
    exit 0
}

& npx --no-install impeccable detect @resolved
exit $LASTEXITCODE
