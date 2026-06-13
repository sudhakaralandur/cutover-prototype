@echo off
echo.
echo ==========================================
echo   Cutover Pro - Starting Application
echo ==========================================
echo.

cd /d "C:\Users\sudha\OneDrive\00-Codex Projects\Cutover Prototype"

echo Starting Flask app in background...
start "Cutover Flask App" cmd /k "python app.py"

echo Waiting for Flask to start...
timeout /t 3 /nobreak > nul

echo.
echo Starting ngrok tunnel on port 5001...
echo.
echo Your public URL will appear below.
echo Share the https://xxxx.ngrok-free.app URL
echo.
echo Press Ctrl+C to stop the tunnel.
echo.
ngrok http 5001
pause
