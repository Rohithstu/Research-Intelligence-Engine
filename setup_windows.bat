@echo off
echo ============================================
echo  Research Intelligence System - Setup
echo ============================================

echo.
echo [1/3] Setting up Python backend...
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
echo Backend setup complete.

echo.
echo [2/3] Setting up React frontend...
cd ..\frontend
npm install
echo Frontend setup complete.

echo.
echo [3/3] Setup complete!
echo.
echo To START the system:
echo   Terminal 1 (Backend):  cd backend ^&^& venv\Scripts\activate ^&^& uvicorn main:app --reload --port 8000
echo   Terminal 2 (Frontend): cd frontend ^&^& npm start
echo.
echo Then open: http://localhost:3000
pause
