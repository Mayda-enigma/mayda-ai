@echo off
setlocal enabledelayedexpansion

REM Voice Chef Docker Management Script for Windows

set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

:print_status
echo %BLUE%[INFO]%NC% %1
goto :eof

:print_success
echo %GREEN%[SUCCESS]%NC% %1
goto :eof

:print_warning
echo %YELLOW%[WARNING]%NC% %1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %1
goto :eof

:check_docker
docker info >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker is not running. Please start Docker Desktop first."
    exit /b 1
)
goto :eof

:build
call :print_status "Building Voice Chef Docker image..."
call :check_docker
docker-compose build --no-cache
if errorlevel 1 (
    call :print_error "Build failed!"
    exit /b 1
)
call :print_success "Build completed successfully!"
goto :eof

:run
call :print_status "Starting Voice Chef application..."
call :check_docker
docker-compose up -d
if errorlevel 1 (
    call :print_error "Failed to start application!"
    exit /b 1
)
call :print_success "Application started! Use 'logs' command to view output."
goto :eof

:dev
call :print_status "Starting Voice Chef in development mode..."
call :check_docker
docker-compose -f docker-compose.dev.yml up
goto :eof

:logs
call :print_status "Viewing application logs..."
docker-compose logs -f voice-chef
goto :eof

:stop
call :print_status "Stopping Voice Chef application..."
docker-compose down
call :print_success "Application stopped successfully!"
goto :eof

:restart
call :print_status "Restarting Voice Chef application..."
call :stop
call :run
goto :eof

:clean
call :print_status "Cleaning up Docker resources..."
docker-compose down -v --remove-orphans
docker image prune -f
call :print_success "Cleanup completed!"
goto :eof

:test_audio
call :print_status "Testing audio in container..."
docker-compose exec voice-chef python -c "import sounddevice as sd; print('Available audio devices:'); print(sd.query_devices()); print('Audio test completed')"
goto :eof

:shell
call :print_status "Opening shell in Voice Chef container..."
docker-compose exec voice-chef /bin/bash
goto :eof

:status
call :print_status "Voice Chef application status:"
docker-compose ps
goto :eof

:help
echo Voice Chef Docker Management for Windows
echo.
echo Usage: %0 [COMMAND]
echo.
echo Commands:
echo   build       Build the Docker image
echo   run         Start the application in production mode
echo   dev         Start the application in development mode
echo   logs        View application logs
echo   stop        Stop the application
echo   restart     Restart the application
echo   clean       Clean up Docker resources
echo   test-audio  Test audio functionality in container
echo   shell       Open a shell in the container
echo   status      Show application status
echo   help        Show this help message
echo.
echo Examples:
echo   %0 build     # Build the Docker image
echo   %0 run       # Run the application
echo   %0 logs      # View real-time logs
goto :eof

REM Main script logic
if "%1"=="" goto help
if "%1"=="build" goto build
if "%1"=="run" goto run
if "%1"=="dev" goto dev
if "%1"=="logs" goto logs
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="clean" goto clean
if "%1"=="test-audio" goto test_audio
if "%1"=="shell" goto shell
if "%1"=="status" goto status
if "%1"=="help" goto help
if "%1"=="--help" goto help
if "%1"=="-h" goto help

call :print_error "Unknown command: %1"
echo.
goto help