@echo off
SET RETRIES=0
SET MAX_RETRIES=5
SET SCRIPT_PATH="main_tencent.py"
SET WORKING_DIRECTORY="%USERPROFILE%\Documents\SalesOperation_code\itjuzi_everyday"
SET CONDA_ENV_NAME="itjuzi_condaenv"

:: Set working dir
cd /d %WORKING_DIRECTORY%

:retry
ECHO %DATE% %TIME%
ECHO Current RETRIES: %RETRIES%, MAX_RETRIES: %MAX_RETRIES%
IF %RETRIES% GEQ %MAX_RETRIES% (
    echo Max retries reached. Script run unsuccessfully.
    EXIT /B 1
)

:: Activate conda
CALL conda activate %CONDA_ENV_NAME%
ECHO %ERRORLEVEL%

python %SCRIPT_PATH%
@REM ECHO %ERRORLEVEL%

IF %ERRORLEVEL% NEQ 0 (
    SET /A RETRIES+=1
    echo Failed. Retrying...^(Retry No. %RETRIES% ^)
    GOTO retry
)

echo Run successfully!
EXIT /B 0
