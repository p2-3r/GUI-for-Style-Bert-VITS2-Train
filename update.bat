@echo off

echo [34mINFO[0m^|[32m%time:~0,2%:%time:~3,2%:%time:~6,2%[0m^|Starting update...

git pull
git merge origin/dev

echo echo [33mCOMPLETE[0m^|[32m%time:~0,2%:%time:~3,2%:%time:~6,2%[0m^|Update completed successfully!
pause