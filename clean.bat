@echo off
echo ִ����Ŀ�������������ִ�У�Ctrl+Cȡ����
pause > nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
if exist "New-Code\config.json" del /q "New-Code\config.json"
if exist "New-Code\logs" rd /s /q "New-Code\logs"
echo ������ɣ�