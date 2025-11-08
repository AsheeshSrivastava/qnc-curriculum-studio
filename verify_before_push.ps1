# Verify Before Push - Security Check Script
# Quest and Crossfire™

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "SECURITY CHECK BEFORE PUSHING TO GITHUB" -ForegroundColor Yellow
Write-Host "============================================================`n" -ForegroundColor Cyan

$hasErrors = $false

# Check 1: Verify .gitignore exists
Write-Host "[1/6] Checking .gitignore..." -ForegroundColor Yellow
if (Test-Path ".gitignore") {
    Write-Host "  ✅ .gitignore exists" -ForegroundColor Green
} else {
    Write-Host "  ❌ .gitignore NOT FOUND!" -ForegroundColor Red
    $hasErrors = $true
}

# Check 2: Verify sensitive files are NOT tracked
Write-Host "`n[2/6] Checking for sensitive files..." -ForegroundColor Yellow
$sensitiveFiles = @(
    "config/settings.env",
    ".env",
    "backend/config/settings.env",
    "frontend/.env"
)

foreach ($file in $sensitiveFiles) {
    if (Test-Path $file) {
        $tracked = git ls-files $file 2>$null
        if ($tracked) {
            Write-Host "  ❌ WARNING: $file is tracked by git!" -ForegroundColor Red
            $hasErrors = $true
        } else {
            Write-Host "  ✅ $file is ignored" -ForegroundColor Green
        }
    }
}

# Check 3: Search for hardcoded API keys
Write-Host "`n[3/6] Scanning for hardcoded API keys..." -ForegroundColor Yellow
$patterns = @("sk-", "tvly-", "ls__", "Bearer ")
$foundKeys = $false

Get-ChildItem -Recurse -Include *.py,*.js,*.ts,*.json -Exclude __pycache__,node_modules | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    foreach ($pattern in $patterns) {
        if ($content -match $pattern) {
            Write-Host "  ⚠️  Possible API key in: $($_.Name)" -ForegroundColor Yellow
            $foundKeys = $true
        }
    }
}

if (-not $foundKeys) {
    Write-Host "  ✅ No obvious API keys found" -ForegroundColor Green
}

# Check 4: Verify LICENSE exists
Write-Host "`n[4/6] Checking LICENSE..." -ForegroundColor Yellow
if (Test-Path "LICENSE") {
    Write-Host "  ✅ LICENSE file exists" -ForegroundColor Green
} else {
    Write-Host "  ❌ LICENSE file NOT FOUND!" -ForegroundColor Red
    $hasErrors = $true
}

# Check 5: Verify SECURITY.md exists
Write-Host "`n[5/6] Checking SECURITY.md..." -ForegroundColor Yellow
if (Test-Path "SECURITY.md") {
    Write-Host "  ✅ SECURITY.md exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  SECURITY.md NOT FOUND!" -ForegroundColor Yellow
}

# Check 6: Verify README exists
Write-Host "`n[6/6] Checking README.md..." -ForegroundColor Yellow
if (Test-Path "README.md") {
    Write-Host "  ✅ README.md exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  README.md NOT FOUND!" -ForegroundColor Yellow
}

# Final verdict
Write-Host "`n============================================================" -ForegroundColor Cyan
if ($hasErrors) {
    Write-Host "❌ SECURITY ISSUES FOUND - DO NOT PUSH YET!" -ForegroundColor Red
    Write-Host "`nFix the issues above before pushing to GitHub." -ForegroundColor Yellow
} else {
    Write-Host "✅ SECURITY CHECK PASSED" -ForegroundColor Green
    Write-Host "`nYou can safely push to GitHub (make sure repo is PRIVATE)." -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. git add ." -ForegroundColor Cyan
    Write-Host "  2. git status (review carefully)" -ForegroundColor Cyan
    Write-Host "  3. git commit -m 'Initial commit'" -ForegroundColor Cyan
    Write-Host "  4. Create PRIVATE repo on GitHub" -ForegroundColor Cyan
    Write-Host "  5. git remote add origin <url>" -ForegroundColor Cyan
    Write-Host "  6. git push -u origin main" -ForegroundColor Cyan
}
Write-Host "============================================================`n" -ForegroundColor Cyan



