@echo off

echo Running department-news-board without Docker

where /q pipenv
if %ERRORLEVEL% NEQ 0 (
	echo Error level: %ERRORLEVEL%
	echo Pipenv is not installed. Please install it using `pip install pipenv`
	exit
)

call pipenv install

call pipenv run nameko run services.gateway.main 
call pipenv run nameko run user.main 
call pipenv run nameko run news.main 
call pipenv run nameko run storage.main 