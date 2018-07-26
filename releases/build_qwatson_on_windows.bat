python -m venv ..\environment
..\environment\Scripts\python.exe -m pip install --upgrade pip
..\environment\Scripts\python.exe -m pip install -r ..\requirements.txt
..\environment\Scripts\python.exe -m pip install pyinstaller
..\environment\Scripts\pyinstaller.exe qwatson.spec
pause