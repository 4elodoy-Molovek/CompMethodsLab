@echo off
echo ========================================
echo Starting Beet Optimization Lab
echo ========================================
echo.

echo Starting Backend (Flask server on port 5000)...
start "Backend Server" cmd /c "python backend/app.py"
timeout /t 2 /nobreak >nul

echo.
echo Starting Frontend (Web server on port 8000)...
echo.
echo ========================================
echo Application is starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:8000
echo ========================================
echo.
echo Press Ctrl+C to stop the frontend server
echo (Backend will continue running in separate window)
echo.

python -m http.server 8000

