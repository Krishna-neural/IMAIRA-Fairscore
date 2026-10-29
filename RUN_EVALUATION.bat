@echo off
setlocal
cd /d "%~dp0"
echo =====================================================================
echo  IMAIRA FairScore -- Candidate Technical Interview Evaluator
echo =====================================================================
echo.

if exist "..\torch-env\Scripts\python.exe" (
    set "PYTHON_EXE=..\torch-env\Scripts\python.exe"
) else if exist "torch-env\Scripts\python.exe" (
    set "PYTHON_EXE=torch-env\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Using Python runtime: %PYTHON_EXE%
echo Scanning for recordings in: data\recordings\ (fallback: asr\)
echo.

"%PYTHON_EXE%" evaluate_interview.py %*

echo.
echo =====================================================================
echo Evaluation finished. Full reports generated at:
echo   [Markdown] reports\interview_evaluation_report.md
echo   [JSON]     reports\interview_evaluation_report.json
echo =====================================================================
echo.
pause
