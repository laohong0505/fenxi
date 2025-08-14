@echo off
echo 正在打包，请稍候...
pyinstaller --onefile --noconsole --icon=crypto.ico Crypto_Analysis_Tool.py
pause
