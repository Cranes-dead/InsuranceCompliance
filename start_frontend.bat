@echo off
echo 🚀 Starting Motor Vehicle Insurance Compliance System Frontend
echo ================================================================

cd /d "D:\Capstone"

echo ✅ Activating Python environment...
call .venv\Scripts\activate.bat

echo 🌐 Starting Streamlit frontend...
echo Access the application at: http://localhost:8501
echo Press Ctrl+C to stop the server

D:/Capstone/.venv/Scripts/python.exe -m streamlit run src/frontend/compliance_app.py

pause