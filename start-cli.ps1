# Quick Start Script - CLI Mode
# Rimworld MOD Localization Assistant

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Rimworld MOD Localization Assistant" -ForegroundColor Cyan
Write-Host "Starting CLI Mode..." -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run deploy.ps1 first to set up the environment." -ForegroundColor Yellow
    Write-Host ""
    Read-Host -Prompt "Press Enter to exit"
    exit 1
}

# Activate virtual environment and run CLI
& ".\venv\Scripts\python.exe" "src\main.py" --cli

# If the application exits with an error
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "The application exited with an error." -ForegroundColor Red
    Write-Host "Please check the error message above." -ForegroundColor Yellow
    Write-Host ""
    Read-Host -Prompt "Press Enter to exit"
}
