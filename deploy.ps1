# Rimworld MOD Localization Assistant - One-Click Deployment Script
# PowerShell Script for Windows

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Rimworld MOD Localization Assistant" -ForegroundColor Cyan
Write-Host "One-Click Deployment Script" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/7] Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Green

    $version = [regex]::Match($pythonVersion, "(\d+)\.(\d+)").Groups
    $major = [int]$version[1].Value
    $minor = [int]$version[2].Value

    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
        Write-Host "  Error: Python 3.9 or higher is required!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  Error: Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "  Please install Python 3.9+ from https://www.python.org/" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "[2/7] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  Virtual environment already exists, skipping..." -ForegroundColor Green
} else {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Error: Failed to create virtual environment!" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Virtual environment created successfully!" -ForegroundColor Green
}

# Install dependencies (without activating venv, use venv python directly)
Write-Host "[3/7] Upgrading pip..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple 2>&1 | Out-Null
Write-Host "  Pip upgraded successfully!" -ForegroundColor Green

# Install dependencies
Write-Host "[4/7] Installing dependencies (using Tsinghua mirror)..." -ForegroundColor Yellow
& ".\venv\Scripts\pip.exe" install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Error: Failed to install dependencies!" -ForegroundColor Red
    exit 1
}
Write-Host "  Dependencies installed successfully!" -ForegroundColor Green

# Check and install beautifulsoup4 specifically (for online glossary search)
Write-Host "  Verifying beautifulsoup4 installation..." -ForegroundColor Yellow
$bs4Check = & ".\venv\Scripts\python.exe" -c "import bs4" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Installing beautifulsoup4..." -ForegroundColor Yellow
    & ".\venv\Scripts\pip.exe" install beautifulsoup4 -i https://pypi.tuna.tsinghua.edu.cn/simple
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  beautifulsoup4 installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "  Warning: Failed to install beautifulsoup4. Online glossary search may not work." -ForegroundColor Yellow
    }
} else {
    Write-Host "  beautifulsoup4 is already installed!" -ForegroundColor Green
}

# Initialize database directory
Write-Host "[5/7] Initializing data directory..." -ForegroundColor Yellow
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
}
if (-not (Test-Path "data\backups")) {
    New-Item -ItemType Directory -Path "data\backups" | Out-Null
}
Write-Host "  Data directory initialized!" -ForegroundColor Green

# Check config file
Write-Host "[6/7] Checking configuration file..." -ForegroundColor Yellow
if (Test-Path "config\translation_api.json") {
    Write-Host "  Configuration file exists!" -ForegroundColor Green
    Write-Host "  Please edit config\translation_api.json to add your API keys" -ForegroundColor Yellow
} else {
    Write-Host "  Warning: config\translation_api.json not found!" -ForegroundColor Red
    Write-Host "  Please create this file based on README.md" -ForegroundColor Yellow
}

# Test virtual environment
Write-Host "[7/7] Testing virtual environment..." -ForegroundColor Yellow
$testResult = & ".\venv\Scripts\python.exe" --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Virtual environment is ready! ($testResult)" -ForegroundColor Green
} else {
    Write-Host "  Warning: Virtual environment test failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Deployment Completed Successfully!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Edit config\translation_api.json to configure translation APIs" -ForegroundColor White
Write-Host "2. Run the application:" -ForegroundColor White
Write-Host "   - GUI mode (Recommended): python src\main.py --gui" -ForegroundColor Cyan
Write-Host "   - CLI mode: python src\main.py --cli" -ForegroundColor White
Write-Host ""
Write-Host "Features:" -ForegroundColor Yellow
Write-Host "  - MOD extraction and translation" -ForegroundColor White
Write-Host "  - AI-powered batch translation (DeepSeek/Baidu/Ollama)" -ForegroundColor White
Write-Host "  - Translation memory and glossary" -ForegroundColor White
Write-Host "  - Auto-save and session management" -ForegroundColor White
Write-Host ""
Write-Host "For more information, see README.md" -ForegroundColor White
Write-Host ""

# Ask user if they want to start the application
Write-Host "==================================" -ForegroundColor Cyan
$startApp = Read-Host "Do you want to start the application now? (y/n)"

if ($startApp.Trim() -eq 'y' -or $startApp.Trim() -eq 'Y') {
    Write-Host ""
    Write-Host "Select mode:" -ForegroundColor Yellow
    Write-Host "1. GUI mode (Recommended)" -ForegroundColor Cyan
    Write-Host "2. CLI mode" -ForegroundColor White
    Write-Host ""

    $mode = Read-Host "Enter your choice (1 or 2)"
    $mode = $mode.Trim()

    Write-Host ""
    if ($mode -eq '1') {
        Write-Host "Starting GUI mode..." -ForegroundColor Green
        Write-Host ""
        & ".\venv\Scripts\python.exe" src\main.py --gui
    }
    elseif ($mode -eq '2') {
        Write-Host "Starting CLI mode..." -ForegroundColor Green
        Write-Host ""
        & ".\venv\Scripts\python.exe" src\main.py --cli
    }
    else {
        Write-Host "Invalid choice: '$mode'" -ForegroundColor Red
        Write-Host "Please run manually:" -ForegroundColor Yellow
        Write-Host "  .\start-gui.ps1  (Quick start GUI)" -ForegroundColor Cyan
        Write-Host "  .\start-cli.ps1  (Quick start CLI)" -ForegroundColor Cyan
    }
} else {
    Write-Host ""
    Write-Host "You can start the application later by running:" -ForegroundColor Yellow
    Write-Host "  .\start-gui.ps1  (for GUI mode)" -ForegroundColor Cyan
    Write-Host "  .\start-cli.ps1  (for CLI mode)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or manually:" -ForegroundColor Yellow
    Write-Host "  python src\main.py --gui" -ForegroundColor White
    Write-Host "  python src\main.py --cli" -ForegroundColor White
}

Write-Host ""
Write-Host "Thank you for using Rimworld MOD Localization Assistant!" -ForegroundColor Cyan
Write-Host ""
