# Voice Chef - Docker Quick Start Guide

## 🐳 Docker Setup Complete!

Your Voice Chef application has been successfully dockerized! Here are all the
files created:

### 📁 Docker Files Created:

- `Dockerfile` - Main container configuration
- `docker-compose.yml` - Production setup
- `docker-compose.dev.yml` - Development setup
- `requirements.txt` - Python dependencies
- `.dockerignore` - Files to exclude from Docker build
- `docker-manage.sh` - Linux/Mac management script
- `docker-manage.bat` - Windows management script
- `README.md` - Complete documentation

## 🚀 Quick Start

### Windows (PowerShell):

```powershell
# Build and run
.\docker-manage.bat build
.\docker-manage.bat run

# View logs
.\docker-manage.bat logs

# Stop application
.\docker-manage.bat stop
```

### Linux/Mac (Bash):

```bash
# Make script executable
chmod +x docker-manage.sh

# Build and run
./docker-manage.sh build
./docker-manage.sh run

# View logs
./docker-manage.sh logs

# Stop application
./docker-manage.sh stop
```

### Direct Docker Compose:

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f voice-chef

# Stop
docker-compose down
```

## 🎤 Audio Configuration

### Windows:

- Audio in Docker containers on Windows can be challenging
- For best results, consider running natively on Windows
- If using WSL2, audio passthrough requires additional setup

### Linux:

- Make sure you're in the audio group: `sudo usermod -a -G audio $USER`
- Restart your session after adding to the audio group
- The container uses PulseAudio for audio access

### Mac:

- Audio device access in Docker on Mac has limitations
- Consider running natively for better audio support

## 🔧 Development Mode

For development with hot reload:

```bash
# Linux/Mac
./docker-manage.sh dev

# Windows
.\docker-manage.bat dev

# Or directly
docker-compose -f docker-compose.dev.yml up
```

## 🐛 Troubleshooting

### Check Audio Devices:

```bash
# Linux/Mac
./docker-manage.sh test-audio

# Windows
.\docker-manage.bat test-audio
```

### Container Shell Access:

```bash
# Linux/Mac
./docker-manage.sh shell

# Windows
.\docker-manage.bat shell
```

### View Status:

```bash
docker-compose ps
```

### Rebuild Everything:

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

## 📝 Notes

1. **First Run**: The Whisper model will be downloaded on first run (~150MB)
2. **Audio Access**: The container needs access to your audio devices
3. **Permissions**: On Linux, the container runs in privileged mode for audio
   access
4. **Persistence**: Model cache is stored in a Docker volume to avoid
   re-downloading

## 🏭 Production Deployment

For production, modify `docker-compose.yml`:

- Remove `privileged: true`
- Add resource limits
- Configure proper audio group permissions
- Set up logging and monitoring
- Use environment-specific configurations

## ✅ What's Included

Your dockerized Voice Chef includes:

- ✅ Continuous voice listening
- ✅ Voice command recognition with fuzzy matching
- ✅ Voice confirmation system
- ✅ French language support
- ✅ Whisper AI transcription
- ✅ Audio device access
- ✅ Development and production configurations
- ✅ Management scripts for easy operation
- ✅ Complete documentation

## 🎯 Next Steps

1. Run `docker-compose up --build` to start
2. Speak commands like "Commande 15 prete"
3. Confirm with "OUI" when prompted
4. Monitor logs to see command processing

Your Voice Chef is now fully containerized and ready for deployment! 🍳👨‍🍳
