echo off
set PWD=%~dp0
cd /d %PWD%\DeDRM_lib && start /min python DeDRM_app.pyw %*
exit
