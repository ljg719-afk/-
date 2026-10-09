@echo off
chcp 65001 >nul
pip install python-pptx python-docx pillow
python "%~dp0make_quiz_ppt.py" "C:\Users\Dddd5\OneDrive\문서\제혜영\24 요양보호사 문제"
pause
