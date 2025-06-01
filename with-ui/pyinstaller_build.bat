if not exist ".\pyinstaller_exe\NUL" mkdir ".\pyinstaller_exe"
cd .\pyinstaller_exe
pyinstaller --noconfirm --onefile --windowed --icon ..\misc\icon.ico ..\program.py