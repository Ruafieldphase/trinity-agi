@echo off
REM Background Self Watchdog 실행 스크립트
REM 윈도우 시작 시 자동 실행되도록 시작 프로그램에 바로가기 추가

cd /d c:\workspace\agi
start /min pythonw.exe c:\workspace\agi\scripts\background_self_watchdog.py
