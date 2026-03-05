@echo off
echo ========================================
echo    Starting FarmBuddy AI Application
echo ========================================
echo.

echo [1/3] Starting Backend Server (Port 5000)...
cd backend
start cmd /k "..\venv\Scripts\activate && python app.py"
cd ..

timeout /t 5

echo [2/3] Starting Frontend Server (Port 5500)...
cd frontend
start cmd /k "python -m http.server 5500"
cd ..

timeout /t 2

echo [3/3] Opening FarmBuddy Landing Page...
start "" "%~dp0frontend\landing.html"

echo.
echo ========================================
echo    FarmBuddy AI is now running!
echo ========================================
echo.
echo Landing Page: %~dp0frontend\landing.html
echo Backend API: http://127.0.0.1:5000
echo.
echo Press any key to stop all servers...
echo.

pause > nul
taskkill /f /im python.exe > nul 2>&1
echo All servers stopped.