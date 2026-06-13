@echo off
echo.
echo ==========================================
echo   Cutover Pro - Starting ngrok Tunnel
echo ==========================================
echo.
echo Make sure app.py is already running!
echo.
cd /d "C:\Users\sudha\OneDrive\00-Codex Projects\Cutover Prototype"
echo Starting ngrok on port 5001...
echo.
echo Your public URL will appear below.
echo Share the https://xxxx.ngrok-free.app URL
echo.
echo Press Ctrl+C to stop the tunnel.
echo.
ngrok http 5001
pause
