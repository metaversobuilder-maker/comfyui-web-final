@echo off
echo Starting ComfyUI Web Services...
echo.

REM Start PostgreSQL
echo Starting PostgreSQL...
docker start comfyui-postgres
timeout /t 2 /nobreak >nul

REM Start API
echo Starting API...
cd C:\Users\moncl\.openclaw\workspace\comfyui-web\backend
start "ComfyUI API" python main.py
timeout /t 3 /nobreak >nul

REM Start Worker
echo Starting Worker...
start "ComfyUI Worker" python worker_new.py
timeout /t 2 /nobreak >nul

REM Start Frontend
echo Starting Frontend...
cd C:\Users\moncl\.openclaw\workspace\comfyui-web\frontend
start "ComfyUI Frontend" npm run dev

REM Start ComfyUI
echo Starting ComfyUI...
cd C:\COMFYUINEW
start "ComfyUI Server" run_SAGE_ALL.bat

echo.
echo All services started!
echo API: http://localhost:8000
echo Frontend: http://localhost:3000
pause