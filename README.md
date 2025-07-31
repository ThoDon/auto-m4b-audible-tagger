# Auto M4B Audible Tagger

Automatically tags .m4b audiobook files with metadata from Audible's API, compatible with Mp3Tag's Audible API Web Source.

## Features

- **Automatic Metadata Tagging**: Extract comprehensive metadata from Audible's API
- **Auto-Tagging Support**: Automatically process files that already have ASIN tags
- **Batch Processing**: Process multiple files at once via API
- **Mp3Tag Compatibility**: Uses the same tag structure as Mp3Tag's Audible API.inc
- **Multiple Interfaces**: Command-line, REST API, and Telegram bot
- **Cover Art Embedding**: Automatically download and embed cover images
- **Library Organization**: Organize files by Author/Series/Title structure
- **Audiobookshelf Compatibility**: Create additional metadata files

## Auto-Tagging Feature

The system now supports automatic processing of files that already contain ASIN tags:

### Configuration

Enable auto-tagging in `config.json`:

```json
{
  "auto_tag_enabled": true
}
```

### Usage

#### Command Line

The tagger will automatically try to process files with existing ASIN tags first, then fall back to interactive mode if no ASIN is found.

#### API Endpoints

**Batch Auto-Processing** (process all pending files):

```bash
POST /audiobooks/auto/batch
```

**Individual Auto-Processing**:

```bash
POST /audiobooks/{file_id}/auto
```

#### Telegram Bot

**Batch Auto-Processing**:

```
/auto
```

**Individual Auto-Processing**:
Use the "🤖 Auto" button in the file list.

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `config.json` with your preferences
4. Place .m4b files in the `incoming/` directory

## Usage

### Command Line

```bash
python scripts/tagger.py
```

### API Server

```bash
python scripts/api_server.py incoming/ library/
```

### Telegram Bot

```bash
python scripts/telegram_bot.py --api-url http://localhost:5000 --token YOUR_BOT_TOKEN
```

## Configuration

Key settings in `config.json`:

- `auto_tag_enabled`: Enable/disable auto-tagging functionality
- `preferred_locale`: Preferred Audible locale (fr, com, co.uk, etc.)
- `embed_covers`: Download and embed cover art
- `include_series_in_filename`: Include series info in filenames
- `create_additional_metadata`: Create Audiobookshelf-compatible files

## API Endpoints

- `GET /health` - Health check
- `GET /audiobooks` - List pending audiobooks
- `GET /audiobooks/{id}/search` - Search for metadata
- `POST /audiobooks/{id}/search/custom` - Custom search
- `GET /audiobooks/{id}/process` - Process with selection
- `POST /audiobooks/{id}/auto` - Auto-process individual file
- `POST /audiobooks/auto/batch` - Batch auto-process all files
- `POST /audiobooks/{id}/skip` - Skip processing

## Telegram Commands

- `/start` - Welcome message
- `/list` - List pending audiobooks
- `/auto` - Batch auto-process all files
- `/language` - Change language
- `/getnewreleases` - Trigger n8n workflow (if configured)

## File Organization

Processed files are organized as:

```
library/
├── Author Name/
│   ├── Series Name/
│   │   └── Book Title (Series #1)/
│   │       ├── Book Title (Series #1).m4b
│   │       ├── desc.txt
│   │       ├── reader.txt
│   │       ├── cover.jpg
│   │       └── Book Title (Series #1).opf
│   └── Standalone Book/
│       └── Book Title/
│           ├── Book Title.m4b
│           └── ...
```

## License

MIT License - see LICENSE file for details.
