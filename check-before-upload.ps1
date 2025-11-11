# Pre-upload Security Check Script
# Run this before uploading to Gitee to ensure no sensitive data

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Gitee Upload Security Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$issues = @()

# 1. Check if config file exists and would be uploaded
Write-Host "[1/6] Checking configuration files..." -ForegroundColor Yellow
if (Test-Path "config\translation_api.json") {
    # Check if it's in .gitignore
    $gitignore = Get-Content ".gitignore" -ErrorAction SilentlyContinue
    if ($gitignore -match "config/translation_api.json") {
        Write-Host "  OK: config/translation_api.json is in .gitignore" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: config/translation_api.json is NOT in .gitignore!" -ForegroundColor Red
        $issues += "config/translation_api.json is not in .gitignore"
    }

    # Check if it contains real API keys
    $config = Get-Content "config\translation_api.json" -Raw
    if ($config -match "sk-[a-zA-Z0-9]+") {
        Write-Host "  WARNING: Possible real API Key detected!" -ForegroundColor Yellow
    }
} else {
    Write-Host "  OK: config/translation_api.json does not exist" -ForegroundColor Green
}

# 2. Check if example config exists
Write-Host "[2/6] Checking template config file..." -ForegroundColor Yellow
if (Test-Path "config\translation_api.json.example") {
    Write-Host "  OK: Template config file exists" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Template config file missing!" -ForegroundColor Red
    $issues += "Missing config/translation_api.json.example"
}

# 3. Check database files
Write-Host "[3/6] Checking database files..." -ForegroundColor Yellow
$dbFiles = Get-ChildItem -Path "data" -Filter "*.db" -Recurse -ErrorAction SilentlyContinue
if ($dbFiles) {
    Write-Host "  INFO: Found $($dbFiles.Count) database file(s)" -ForegroundColor Yellow
    $gitignore = Get-Content ".gitignore" -ErrorAction SilentlyContinue
    if ($gitignore -match "\.db") {
        Write-Host "  OK: Database files are in .gitignore" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Database files are NOT in .gitignore!" -ForegroundColor Red
        $issues += "Database files are not in .gitignore"
    }
} else {
    Write-Host "  OK: No database files found" -ForegroundColor Green
}

# 4. Check for hardcoded API keys in code
Write-Host "[4/6] Scanning code for hardcoded keys..." -ForegroundColor Yellow
$suspiciousFiles = @()
Get-ChildItem -Path "src" -Filter "*.py" -Recurse | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match "sk-[a-zA-Z0-9]{30,}") {
        $suspiciousFiles += $_.FullName
    }
}

if ($suspiciousFiles.Count -eq 0) {
    Write-Host "  OK: No hardcoded API keys found" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Possible hardcoded API keys in:" -ForegroundColor Yellow
    foreach ($file in $suspiciousFiles) {
        Write-Host "    - $file" -ForegroundColor Yellow
    }
    $issues += "Possible hardcoded API keys found"
}

# 5. Check required files
Write-Host "[5/6] Checking required files..." -ForegroundColor Yellow
$requiredFiles = @("README.md", "LICENSE", "CONTRIBUTING.md", ".gitignore", "requirements.txt")
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  OK: $file exists" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Missing $file" -ForegroundColor Red
        $issues += "Missing file: $file"
    }
}

# 6. Check git status
Write-Host "[6/6] Checking Git status..." -ForegroundColor Yellow
if (Test-Path ".git") {
    try {
        $status = git status --porcelain 2>&1
        if ($LASTEXITCODE -eq 0) {
            $tracked = git ls-files | Select-String "config/translation_api.json"
            if ($tracked) {
                Write-Host "  WARNING: config/translation_api.json is tracked by Git!" -ForegroundColor Red
                $issues += "config/translation_api.json is tracked by Git"
            } else {
                Write-Host "  OK: Config file is not tracked" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "  INFO: Git not initialized" -ForegroundColor Gray
    }
} else {
    Write-Host "  INFO: Git not initialized" -ForegroundColor Gray
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($issues.Count -eq 0) {
    Write-Host "  All checks passed!" -ForegroundColor Green
    Write-Host "  Safe to upload to Gitee" -ForegroundColor Green
} else {
    Write-Host "  Found $($issues.Count) issue(s):" -ForegroundColor Red
    foreach ($issue in $issues) {
        Write-Host "    - $issue" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "  Please fix these issues before uploading!" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Pause
Read-Host "Press Enter to exit"
