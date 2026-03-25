@echo off
call "C:\Users\Admin\anaconda3\condabin\activate.bat" CC_Emu
cd "C:\Users\Admin\anaconda3\envs\CC_Emu" && claude "Work on it. Follow your workflow" --permission-mode bypassPermissions
cmd /k
