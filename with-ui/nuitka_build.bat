if not exist ".\nuitka_exe\NUL" mkdir ".\nuitka_exe"
cd .\nuitka_exe
py -3.12 -m nuitka ..\program.py --windows-console-mode=disable --windows-icon-from-ico=..\misc\icon.ico