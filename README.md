# Auto M4B Audible Tagger

A Docker-based audiobook processing system that automatically tags M4B files with metadata from Audible's API, featuring a REST API server and Telegram bot interface.

## 🌍 Internationalization (i18n)

The Telegram bot supports multiple languages:

- **English** (en) - Default
- **French** (fr)
- **Spanish** (es)
- **Italian** (it)
- **German** (de)

### Language Configuration

Set the default bot language using the `BOT_LANGUAGE` environment variable:

```bash
BOT_LANGUAGE=fr  # French
BOT_LANGUAGE=es  # Spanish
BOT_LANGUAGE=it  # Italian
BOT_LANGUAGE=de  # German
```

### User Language Selection

Users can change their language using the `/language` command in the Telegram bot. Each user's language preference is stored separately.

### Available Commands

- `/start` - Welcome message and help
- `/list` - List pending audiobooks
- `/language` - Change your language preference
- `/getnewreleases` - Trigger new releases workflow (if configured)

## 🚀 Quick Start

Automatically tag and organize audiobooks with metadata from Audible's API. Features a REST API, Telegram bot, and Docker support.

## 🚀 Features

- **Automatic Metadata**: Fetch title, author, narrator, description from Audible
- **Cover Art**: Download and embed cover images (when enabled)
- **REST API**: Full automation support with JSON endpoints
- **Telegram Bot**: Interactive processing via Telegram
- **Docker Support**: Easy deployment with Docker Compose
- **Database**: SQLite tracking of processing status
- **Auto Cleanup**: Remove temporary files and invalid content
- **Multi-locale**: Support for multiple Audible regions

## 📋 Requirements

- **Python 3.8+**
- **FFmpeg** (for audio tagging)
- **Docker** (optional, for containerized deployment)

## 🛠️ Installation

### Local Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/auto-m4b-audible-tagger.git
   cd auto-m4b-audible-tagger
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Create directories**:

   ```bash
   mkdir -p incoming library skipped
   ```

4. **Configure settings** (optional):
   Edit `config.json` with your preferred settings.

### Docker Installation

1. **Create environment file**:

   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Start services**:
   ```bash
   docker compose up -d
   ```

## 📁 Directory Structure

```
auto-m4b-audible-tagger/
├── incoming/          # Place .m4b files here
├── library/           # Processed audiobooks
├── skipped/           # Skipped audiobooks
├── covers/            # Downloaded cover images
├── logs/              # Application logs
├── scripts/           # Core application
│   ├── tagger.py      # Main tagging logic
│   ├── api_server.py  # REST API server
│   ├── telegram_bot.py # Telegram bot
│   ├── database.py    # SQLite database
│   └── cleanup.py     # Auto cleanup
├── config.json        # Configuration
├── docker-compose.yml # Docker services
└── run.py            # Main launcher
```

## 🎯 Usage

### Interactive Mode

```bash
# Start interactive processing
python run.py

# Clean up temporary files
python run.py --cleanup

# Test cover art embedding
python run.py --test-cover <file_path>

# Test FFmpeg tagging
python run.py --test-ffmpeg <file_path>
```

### REST API

```bash
# Start API server
python scripts/api_server.py incoming library

# API endpoints
GET  /health                    # Health check
GET  /audiobooks               # List pending audiobooks
GET  /audiobooks/{id}/search   # Search for metadata
GET  /audiobooks/{id}/process  # Process audiobook
POST /audiobooks/{id}/skip     # Skip processing
GET  /stats                    # Processing statistics
```

### Telegram Bot

```bash
# Start Telegram bot
python scripts/telegram_bot.py --token YOUR_BOT_TOKEN --api-url http://localhost:5000
```

**Available Commands**:

- `/list` - List pending audiobooks (with interactive buttons)
- `/getnewreleases` - Trigger new releases workflow (if configured)

## ⚙️ Configuration

### Environment Variables

```bash
# Required for Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional N8N Integration
N8N_NEW_RELEASES_WEBHOOK_URL=http://your-n8n:5678/webhook/getnewreleases

# Docker permissions
PUID=1000
PGID=1000

# Paths (Docker)
INCOMING_PATH=./incoming
LIBRARY_PATH=./library
SKIPPED_PATH=./skipped
```

### Configuration File (config.json)

```json
{
  "preferred_locale": "fr",
  "embed_covers": true,
  "include_series_in_filename": true,
  "create_additional_metadata": true,
  "exclude_translators": true,
  "output_single_author": false,
  "log_level": "WARNING"
}
```

## 🐳 Docker Deployment

### Quick Start

```bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Services

- **API Server**: `http://localhost:3005` (REST API)
- **Telegram Bot**: Runs in background (requires bot token)

### Volume Mounts

- `./incoming:/app/incoming` - Input audiobooks
- `./library:/app/library` - Processed audiobooks
- `./skipped:/app/skipped` - Skipped audiobooks

## 🔧 API Endpoints

### Core Endpoints

| Method | Endpoint                   | Description             |
| ------ | -------------------------- | ----------------------- |
| `GET`  | `/health`                  | Health check            |
| `GET`  | `/audiobooks`              | List pending audiobooks |
| `GET`  | `/audiobooks/{id}/search`  | Search for metadata     |
| `GET`  | `/audiobooks/{id}/process` | Process audiobook       |
| `POST` | `/audiobooks/{id}/skip`    | Skip processing         |

### Example Workflow

```bash
# 1. List audiobooks
curl http://localhost:3005/audiobooks

# 2. Search for metadata
curl http://localhost:3005/audiobooks/abc123/search

# 3. Process with selection
curl "http://localhost:3005/audiobooks/abc123/process?selection_id=xyz_0"
```

## 📱 Telegram Bot

### Setup

1. **Create bot** with [@BotFather](https://t.me/botfather)
2. **Get token** and set `TELEGRAM_BOT_TOKEN`
3. **Start bot** with Docker or Python

### Usage

1. **Send `/list`** to see pending audiobooks
2. **Click buttons** to search, process, or skip
3. **Use custom search** if automatic search fails

## 🔄 Automation

### N8N Integration

Set `N8N_NEW_RELEASES_WEBHOOK_URL` to enable `/getnewreleases` command.

### Webhook Example

```javascript
// N8N workflow to trigger processing
{
  "method": "GET",
  "url": "http://localhost:3005/audiobooks",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

## 🧹 Auto Cleanup

The system automatically cleans up:

- **Temporary files**: `temp-*.m4b`, `*.tmp`, etc.
- **Non-m4b files**: Any file not ending in `.m4b`
- **Empty folders**: Completely empty directories
- **Invalid folders**: Folders without `.m4b` files

**Manual cleanup**:

```bash
python run.py --cleanup [directory]
```

## 📊 Database

SQLite database tracks:

- **Audiobooks**: File paths, status, metadata
- **Search sessions**: Search results and selections
- **Processing history**: Success/failure tracking

## 🐛 Troubleshooting

### Common Issues

1. **Permission errors**: Check file permissions on `incoming/` and `library/`
2. **FFmpeg not found**: Install FFmpeg and ensure it's in PATH
3. **Telegram bot not responding**: Verify bot token and API URL
4. **Docker build fails**: Check Dockerfile and dependencies

### Logs

- **API Server**: `logs/api_server.log`
- **Telegram Bot**: `logs/telegram_bot.log`
- **Tagger**: `logs/tagger.log`

### Health Check

```bash
curl http://localhost:3005/health
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
