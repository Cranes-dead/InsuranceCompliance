# 🚀 Start Motor Vehicle Insurance Compliance System Frontend
Write-Host "🚀 Starting Motor Vehicle Insurance Compliance System Frontend" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan

# Navigate to project directory
Set-Location "D:\Capstone"

Write-Host "✅ Activating Python environment..." -ForegroundColor Yellow
& "D:\Capstone\.venv\Scripts\Activate.ps1"

Write-Host "🌐 Starting Streamlit frontend..." -ForegroundColor Yellow
Write-Host "Access the application at: http://localhost:8501" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start Streamlit
D:/Capstone/.venv/Scripts/python.exe -m streamlit run src/frontend/compliance_app.py