# Start Python Research Portal System
# This script starts both backend and frontend with proper configuration

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Python Research Portal Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Stop any running instances
Write-Host "Stopping any running instances..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*uvicorn*" -or $_.ProcessName -like "*streamlit*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Start Backend
Write-Host "Starting Backend..." -ForegroundColor Green
Write-Host "Location: http://127.0.0.1:8000" -ForegroundColor Gray

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 8

# Test backend
Write-Host "Testing backend health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 5
    if ($health.status -eq "ok") {
        Write-Host "[OK] Backend is healthy!" -ForegroundColor Green
    }
} catch {
    Write-Host "[ERROR] Backend health check failed!" -ForegroundColor Red
    Write-Host "Please check the backend window for errors" -ForegroundColor Yellow
    exit 1
}

# Start Frontend
Write-Host ""
Write-Host "Starting Frontend..." -ForegroundColor Green
Write-Host "Location: http://localhost:8501" -ForegroundColor Gray

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; streamlit run app.py"

Start-Sleep -Seconds 8

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  System Started Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host "Frontend: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "API Keys: Using config/settings.env" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to open frontend in browser..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Start-Process "http://localhost:8501"

Write-Host ""
Write-Host "System is running!" -ForegroundColor Green
Write-Host "Close this window or press Ctrl+C to stop monitoring" -ForegroundColor Gray
Write-Host ""

# Keep window open
Read-Host "Press Enter to exit"




