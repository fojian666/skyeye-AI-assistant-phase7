@echo off & setlocal EnableDelayedExpansion
for %%a in (8000，8001) do (
    set pid=0
    for /f "tokens=2,5" %%b in ('netstat -ano ^| findstr ":%%a"') do (
        set temp=%%b
        for /f "usebackq delims=: tokens=1,2" %%i in (`set temp`) do (
            if %%j==%%a (
                taskkill /f /pid %%c
                set pid=%%c
                echo 端口号【%%a】相关进程已杀死
            ) else (
                echo 不是本机占用端口【%%a】
            )
        )
    )
    if !pid!==0 (
       echo 端口号【%%a】没有占用
    )
)
call C:\low_altitudelgtus\pack\Scripts\activate.bat
C:
cd low_altitudelgtus\gtus_pack
python manage.py runserver 0.0.0.0:8000
pause
