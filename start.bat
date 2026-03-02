@echo off
echo Starting FarmBuddy Backend...
start cmd /k "cd backend && python app.py"
timeout /t 3
echo Starting FarmBuddy Frontend...
start cmd /k "cd frontend && python -m http.server 5500"
timeout /t 2
start http://127.0.0.1:5500
echo FarmBuddy is running!