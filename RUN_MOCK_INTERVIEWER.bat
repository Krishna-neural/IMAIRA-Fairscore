@echo off
setlocal
cd /d "%~dp0"
echo =====================================================================
echo  IMAIRA FairScore -- AI Mock Interviewer & Accent-Fair Assessment
echo =====================================================================
echo.

if exist ".venv\Scripts\streamlit.exe" (
    set "STREAMLIT_BIN=.venv\Scripts\streamlit.exe"
) else if exist "..\torch-env\Scripts\streamlit.exe" (
    set "STREAMLIT_BIN=..\torch-env\Scripts\streamlit.exe"
) else (
    set "STREAMLIT_BIN=streamlit"
)

echo Starting IMAIRA FairScore UI with: %STREAMLIT_BIN%
echo Access the web interface at: http://localhost:8501
echo.

"%STREAMLIT_BIN%" run ui/app.py

echo.
pause
