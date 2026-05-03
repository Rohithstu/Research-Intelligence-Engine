#!/bin/bash
echo "============================================"
echo " Research Intelligence System - Setup"
echo "============================================"

echo ""
echo "[1/3] Setting up Python backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✓ Backend setup complete"

echo ""
echo "[2/3] Setting up React frontend..."
cd ../frontend
npm install
echo "✓ Frontend setup complete"

echo ""
echo "============================================"
echo "  SETUP COMPLETE!"
echo "============================================"
echo ""
echo "To START the system:"
echo ""
echo "  Terminal 1 (Backend):"
echo "    cd backend && source venv/bin/activate"
echo "    uvicorn main:app --reload --port 8000"
echo ""
echo "  Terminal 2 (Frontend):"
echo "    cd frontend && npm start"
echo ""
echo "  Then open: http://localhost:3000"
echo "============================================"
