@echo off
cd /d C:\Users\User\tiktok-script-generator
echo TikTok 바이럴 분석기 시작 중...
python -m streamlit run app.py --server.port 8501 --server.headless false --server.fileWatcherType none
pause
