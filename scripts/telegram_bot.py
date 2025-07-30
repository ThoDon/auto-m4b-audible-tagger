#!/usr/bin/env python3
"""
Telegram Bot for Audiobook Processing
Handles interactive commands for processing audiobooks via Telegram
"""

import os
import sys
import json
import logging
import requests
import traceback
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from translations import get_text, get_supported_languages

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))


class AudiobookTelegramBot:
    """Telegram bot for audiobook processing"""
    
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.app = Application.builder().token(token).build()
        
        # Track custom search conversations
        self.custom_search_states = {}  # user_id -> (file_id, message_id)
        
        # Check for n8n webhook URL
        self.n8n_webhook_url = os.getenv('N8N_NEW_RELEASES_WEBHOOK_URL')
        if self.n8n_webhook_url:
            self.logger.info(f"n8n webhook URL configured: {self.n8n_webhook_url}")
        else:
            self.logger.info("n8n webhook URL not configured - /getnewreleases command will not be available")
        
        # Language settings
        self.default_language = os.getenv('BOT_LANGUAGE', 'en')
        self.user_languages = {}  # user_id -> language
        
        # Setup logging
        self.setup_logging()
        
        # Register handlers
        self.register_handlers()
    
    def get_user_language(self, user_id: int) -> str:
        """Get language for a specific user, fallback to default"""
        return self.user_languages.get(user_id, self.default_language)
    
    def set_user_language(self, user_id: int, language: str):
        """Set language for a specific user"""
        if language in get_supported_languages():
            self.user_languages[user_id] = language
        
    def setup_logging(self):
        """Setup logging for Telegram bot"""
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Use absolute path for log file
        log_file = logs_dir / "telegram_bot.log"
        
        # Try to set up file logging, fallback to console only if permission denied
        try:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"Telegram Bot logging initialized. Log file: {log_file}")
        except PermissionError:
            # Fallback to console logging only
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
            self.logger.warning(f"Permission denied writing to {log_file}, using console logging only")
        except Exception as e:
            # Fallback to console logging only
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
            self.logger.error(f"Error setting up file logging: {e}, using console logging only")
        
    def register_handlers(self):
        """Register all command and callback handlers"""
        # Register command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("list", self.list_command))
        self.app.add_handler(CommandHandler("language", self.language_command))
        
        # Register n8n command if webhook URL is configured
        if self.n8n_webhook_url:
            self.app.add_handler(CommandHandler("getnewreleases", self.get_new_releases_command))
        
        # Register callback query handler for inline buttons
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Register message handler for custom search
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def setup_bot_commands(self):
        """Set up the bot commands menu"""
        # Use English descriptions for the menu (Telegram doesn't support localized menus yet)
        commands = [
            BotCommand("start", get_text("cmd_start", "en")),
            BotCommand("list", get_text("cmd_list", "en")),
            BotCommand("language", get_text("cmd_language", "en"))
        ]
        
        # Add getnewreleases command if n8n webhook is configured
        if self.n8n_webhook_url:
            commands.append(BotCommand("getnewreleases", get_text("cmd_getnewreleases", "en")))
        
        try:
            await self.app.bot.set_my_commands(commands)
            self.logger.info("Bot commands menu set successfully")
        except Exception as e:
            self.logger.error(f"Failed to set bot commands: {e}")
    

    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        # Set up bot commands on first start
        try:
            await self.setup_bot_commands()
        except Exception as e:
            self.logger.error(f"Failed to set up bot commands: {e}")
        
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        welcome_text = f"""
{get_text('welcome_title', language)}

{get_text('welcome_commands', language)}
{get_text('welcome_list', language)}"""
        
        # Add conditional commands
        if self.n8n_webhook_url:
            welcome_text += f"""
{get_text('welcome_getnewreleases', language)}"""
        
        welcome_text += f"""

{get_text('welcome_help', language)}
{get_text('welcome_buttons', language)}
        """
        
        await update.message.reply_text(welcome_text.strip())
        
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        try:
            response = requests.get(f"{self.api_url}/audiobooks")
            data = response.json()
            
            if data['status'] == 'success':
                if data['count'] == 0:
                    await update.message.reply_text(get_text('list_no_books', language))
                    return
                
                # Create message with audiobook list
                message = get_text('list_found_books', language, data['count']) + "\n\n"
                
                for i, book in enumerate(data['audiobooks'], 1):
                    message += get_text('list_book_entry', language, i, book['parsed_title'], book['parsed_author']) + "\n"
                    message += get_text('list_file_info', language, book['filename']) + "\n"
                    message += get_text('list_id_info', language, book['id']) + "\n\n"
                
                # Create inline keyboard for processing options
                keyboard = []
                for i, book in enumerate(data['audiobooks']):
                    keyboard.append([
                        InlineKeyboardButton(
                            get_text('button_search', language, i+1), 
                            callback_data=f"search:{book['id']}"
                        ),
                        InlineKeyboardButton(
                            get_text('button_skip', language, i+1), 
                            callback_data=f"skip:{book['id']}"
                        )
                    ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    message, 
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(get_text('list_error', language, data.get('message', get_text('error_unknown', language))))
                
        except Exception as e:
            self.logger.error(f"Error in list command: {e}")
            error_details = traceback.format_exc()
            self.logger.error(f"Full traceback: {error_details}")
            await update.message.reply_text(get_text('error_generic', language, str(e)) + "\n\n" + get_text('error_debug_info', language, type(e).__name__))
            
    async def get_new_releases_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /getnewreleases command - trigger n8n workflow"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        if not self.n8n_webhook_url:
            await update.message.reply_text(get_text('getnewreleases_not_configured', language))
            return
            
        try:
            # Send GET request to n8n webhook
            response = requests.get(self.n8n_webhook_url, timeout=30)
            
            if response.status_code == 200:
                await update.message.reply_text(get_text('getnewreleases_success', language))
            else:
                await update.message.reply_text(get_text('getnewreleases_failed', language, response.status_code))
                
        except requests.exceptions.Timeout:
            await update.message.reply_text(get_text('getnewreleases_timeout', language))
        except requests.exceptions.ConnectionError:
            await update.message.reply_text(get_text('getnewreleases_connection_error', language))
        except Exception as e:
            self.logger.error(f"Error in getNewReleases command: {e}")
            error_details = traceback.format_exc()
            self.logger.error(f"Full traceback: {error_details}")
            await update.message.reply_text(get_text('error_generic', language, str(e)) + "\n\n" + get_text('error_debug_info', language, type(e).__name__))
            
    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /language command"""
        user_id = update.effective_user.id
        current_language = self.get_user_language(user_id)
        
        # Get supported languages
        supported_languages = get_supported_languages()
        
        # Create message with current language and available options
        message = f"🌍 **Current Language**: {current_language.upper()}\n\n"
        message += "**Available Languages:**\n"
        
        # Create inline keyboard for language selection
        keyboard = []
        language_names = {
            'en': '🇺🇸 English',
            'fr': '🇫🇷 Français', 
            'es': '🇪🇸 Español',
            'it': '🇮🇹 Italiano',
            'de': '🇩🇪 Deutsch'
        }
        for lang_code in supported_languages:
            lang_name = language_names.get(lang_code, lang_code.upper())
            keyboard.append([
                InlineKeyboardButton(
                    f"{lang_name} {'✅' if lang_code == current_language else ''}", 
                    callback_data=f"language:{lang_code}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
            
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        parts = data.split(':')
        
        if parts[0] == 'search':
            file_id = parts[1]
            await self.handle_search_callback(query, file_id)
        elif parts[0] == 'custom_search':
            file_id = parts[1]
            await self.handle_custom_search_callback(query, file_id)
        elif parts[0] == 'skip':
            file_id = parts[1]
            await self.handle_skip_callback(query, file_id)
        elif parts[0] == 'process':
            file_id = parts[1]
            selection_id = parts[2]
            await self.handle_process_callback(query, file_id, selection_id)
        elif parts[0] == 'language':
            lang_code = parts[1]
            await self.handle_language_callback(query, lang_code)
            
    async def handle_search_callback(self, query, file_id):
        """Handle search button callback"""
        user_id = query.from_user.id
        language = self.get_user_language(user_id)
        
        try:
            response = requests.get(f"{self.api_url}/audiobooks/{file_id}/search")
            data = response.json()
            
            if data['status'] == 'success':
                results = data['results']
                
                if not results:
                    # No results found - offer custom search option
                    message = get_text('search_no_results', language, data['filename']) + "\n\n"
                    message += get_text('search_query_used', language, data['search_query']) + "\n\n"
                    message += get_text('search_try_custom', language)
                    
                    # Create keyboard with custom search option
                    keyboard = [
                        [InlineKeyboardButton(get_text('search_custom_option', language), callback_data=f"custom_search:{file_id}")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        message,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                    return
                    
                # Create message with search results
                message = get_text('search_results_title', language, data['filename']) + "\n\n"
                message += get_text('search_query', language, data['search_query']) + "\n\n"
                
                for i, result in enumerate(results, 1):
                    message += get_text('search_result_entry', language, i, result['title'], result['author']) + "\n"
                    if result.get('narrator'):
                        message += get_text('search_narrated_by', language, result['narrator']) + "\n"
                    message += get_text('search_asin', language, result['asin']) + "\n\n"
                
                # Create inline keyboard for selection
                keyboard = []
                for i, result in enumerate(results, 1):
                    keyboard.append([
                        InlineKeyboardButton(
                            get_text('search_select_option', language, i), 
                            callback_data=f"process:{file_id}:{result['selection_id']}"
                        )
                    ])
                
                # Add custom search option at the bottom
                keyboard.append([
                    InlineKeyboardButton(get_text('search_custom_option', language), callback_data=f"custom_search:{file_id}")
                ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(get_text('error_generic', language, data.get('message', get_text('error_unknown', language))))
                
        except Exception as e:
            self.logger.error(f"Error in search callback: {e}")
            error_details = traceback.format_exc()
            self.logger.error(f"Full traceback: {error_details}")
            await query.edit_message_text(get_text('error_generic', language, str(e)) + "\n\n" + get_text('error_debug_info', language, type(e).__name__))
            
    async def handle_custom_search_callback(self, query, file_id):
        """Handle custom search button callback"""
        user_id = query.from_user.id
        language = self.get_user_language(user_id)
        
        try:
            # Store the custom search state
            self.custom_search_states[user_id] = (file_id, query.message.message_id)
            
            # Try to get the original search query for context
            try:
                response = requests.get(f"{self.api_url}/audiobooks/{file_id}/search")
                data = response.json()
                original_query = data.get('search_query', 'unknown')
            except:
                original_query = 'unknown'
            
            message = get_text('custom_search_title', language, file_id) + "\n\n"
            message += get_text('custom_search_original', language, original_query) + "\n\n"
            message += get_text('custom_search_instructions', language) + "\n"
            message += get_text('custom_search_examples', language) + "\n"
            message += get_text('custom_search_book_title', language) + "\n"
            message += get_text('custom_search_author', language) + "\n"
            message += get_text('custom_search_title_author', language) + "\n"
            message += get_text('custom_search_series', language) + "\n"
            message += get_text('custom_search_spelling', language) + "\n\n"
            message += get_text('custom_search_type_now', language)
            
            await query.edit_message_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Error in custom search callback: {e}")
            error_details = traceback.format_exc()
            self.logger.error(f"Full traceback: {error_details}")
            await query.edit_message_text(get_text('error_generic', language, str(e)) + "\n\n" + get_text('error_debug_info', language, type(e).__name__))
            
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages for custom search"""
        user_id = update.message.from_user.id
        language = self.get_user_language(user_id)
        
        # Check if user is in custom search state
        if user_id in self.custom_search_states:
            file_id, message_id = self.custom_search_states[user_id]
            search_query = update.message.text.strip()
            
            if not search_query:
                await update.message.reply_text(get_text('error_please_provide_query', language))
                return
            
            try:
                # Clear the custom search state
                del self.custom_search_states[user_id]
                
                # Show processing message
                await update.message.reply_text(get_text('custom_search_processing', language, search_query))
                
                # Make custom search request
                response = requests.post(
                    f"{self.api_url}/audiobooks/{file_id}/search/custom",
                    json={'search_query': search_query}
                )
                data = response.json()
                
                if data['status'] == 'success':
                    results = data['results']
                    
                    if not results:
                        await update.message.reply_text(
                            get_text('custom_search_no_results', language, search_query) + "\n\n" +
                            get_text('custom_search_try_different', language),
                            parse_mode='Markdown'
                        )
                        return
                    
                    # Create message with search results
                    message = get_text('custom_search_results_title', language, data['filename']) + "\n\n"
                    message += get_text('search_query', language, search_query) + "\n\n"
                    
                    for i, result in enumerate(results, 1):
                        message += get_text('search_result_entry', language, i, result['title'], result['author']) + "\n"
                        if result.get('narrator'):
                            message += get_text('search_narrated_by', language, result['narrator']) + "\n"
                        message += get_text('search_asin', language, result['asin']) + "\n\n"
                    
                    # Create inline keyboard for selection
                    keyboard = []
                    for i, result in enumerate(results, 1):
                        keyboard.append([
                            InlineKeyboardButton(
                                get_text('search_select_option', language, i), 
                                callback_data=f"process:{file_id}:{result['selection_id']}"
                            )
                        ])
                    
                    # Add custom search option at the bottom
                    keyboard.append([
                        InlineKeyboardButton(get_text('search_custom_option', language), callback_data=f"custom_search:{file_id}")
                    ])
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        message,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(get_text('error_generic', language, data.get('message', get_text('error_unknown', language))))
                    
            except Exception as e:
                self.logger.error(f"Error in custom search: {e}")
                error_details = traceback.format_exc()
                self.logger.error(f"Full traceback: {error_details}")
                await update.message.reply_text(get_text('error_generic', language, str(e)) + "\n\n" + get_text('error_debug_info', language, type(e).__name__))
            
    async def handle_skip_callback(self, query, file_id):
        """Handle skip button callback"""
        user_id = query.from_user.id
        language = self.get_user_language(user_id)
        
        try:
            response = requests.post(f"{self.api_url}/audiobooks/{file_id}/skip")
            data = response.json()
            
            if data['status'] == 'success':
                message = get_text('skip_success', language, data['filename']) + "\n"
                message += get_text('skip_moved_to', language, data['moved_to'])
                await query.edit_message_text(message)
            else:
                await query.edit_message_text(get_text('error_generic', language, data.get('message', get_text('error_unknown', language))))
                
        except Exception as e:
            self.logger.error(f"Error in skip callback: {e}")
            error_details = traceback.format_exc()
            self.logger.error(f"Full traceback: {error_details}")
            await query.edit_message_text(get_text('error_generic', language, str(e)) + "\n\n" + get_text('error_debug_info', language, type(e).__name__))
            
    async def handle_process_callback(self, query, file_id, selection_id):
        """Handle process button callback"""
        user_id = query.from_user.id
        language = self.get_user_language(user_id)
        
        try:
            # Show processing message
            await query.edit_message_text(get_text('processing_start', language))
            
            # Process the audiobook
            response = requests.get(f"{self.api_url}/audiobooks/{file_id}/process?selection_id={selection_id}")
            data = response.json()
            
            if data['status'] == 'success':
                # Build success message with metadata
                message = get_text('processing_success', language, data['filename']) + "\n\n"
                message += get_text('processing_metadata', language) + "\n"
                message += get_text('processing_title', language, data['metadata']['title']) + "\n"
                message += get_text('processing_author', language, data['metadata']['author']) + "\n"
                
                if data['metadata'].get('narrator'):
                    message += get_text('processing_narrator', language, data['metadata']['narrator']) + "\n"
                
                if data['metadata'].get('series'):
                    series_text = data['metadata']['series']
                    if data['metadata'].get('series_part'):
                        series_text += get_text('processing_series_part', language, data['metadata']['series_part'])
                    message += get_text('processing_series', language, series_text) + "\n"
                else:
                    message += get_text('processing_series', language, get_text('processing_standalone', language)) + "\n"
                
                message += get_text('processing_moved_to', language, data['moved_to'])
                
                await query.edit_message_text(message)
            else:
                await query.edit_message_text(get_text('processing_error', language, data.get('message', get_text('error_unknown', language))))
                
        except Exception as e:
            self.logger.error(f"Error in process callback: {e}")
            error_details = traceback.format_exc()
            self.logger.error(f"Full traceback: {error_details}")
            await query.edit_message_text(get_text('error_generic', language, str(e)) + "\n\n" + get_text('error_debug_info', language, type(e).__name__))
            
    async def handle_language_callback(self, query, lang_code):
        """Handle language selection button callback"""
        user_id = query.from_user.id
        language = self.get_user_language(user_id)
        
        if lang_code == language:
            await query.answer(text=f"Your language is already {language.upper()}")
            return
            
        try:
            self.set_user_language(user_id, lang_code)
            await query.answer(text=f"Language changed to {lang_code.upper()}")
            await query.edit_message_text(f"🌍 Your language has been changed to {lang_code.upper()}")
        except Exception as e:
            self.logger.error(f"Error changing language: {e}")
            error_details = traceback.format_exc()
            self.logger.error(f"Full traceback: {error_details}")
            await query.edit_message_text(get_text('error_generic', language, str(e)) + "\n\n" + get_text('error_debug_info', language, type(e).__name__))
            
    def run(self):
        """Run the Telegram bot"""
        self.logger.info("Starting Telegram bot...")
        
        # Start the main bot polling
        self.app.run_polling()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Audiobook Processor Telegram Bot')
    parser.add_argument('--api-url', default='http://localhost:5000', help='API server URL')
    parser.add_argument('--token', required=True, help='Telegram bot token')
    
    args = parser.parse_args()
    
    # Create and run bot
    bot = AudiobookTelegramBot(args.api_url, args.token)
    bot.run()


if __name__ == '__main__':
    main() 