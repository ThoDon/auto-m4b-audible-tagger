#!/usr/bin/env python3
"""
Audible Audiobook Tagger
Automatically tags .m4b files with metadata from Audible's API
"""

import os
import re
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from colorama import init, Fore, Style
from tqdm import tqdm

# Initialize colorama for cross-platform colored output
init()

class AudibleTagger:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.incoming_dir = self.base_dir / "incoming"
        self.library_dir = self.base_dir / "library"
        self.covers_dir = self.base_dir / "covers"
        
        # Create necessary directories
        self.incoming_dir.mkdir(exist_ok=True)
        self.library_dir.mkdir(exist_ok=True)
        self.covers_dir.mkdir(exist_ok=True)
        
        # Setup logging first
        self.setup_logging()
        
        # Load configuration
        self.config = self.load_config()
        
        # Update logging level based on config
        self.update_logging_level()
        
        # Audible API headers (simulating a browser)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def load_config(self) -> Dict:
        """Load configuration from config.json"""
        config_path = self.base_dir / "config.json"
        
        # Default configuration
        default_config = {
            "preferred_locale": "fr",
            "embed_covers": True,
            "include_series_in_filename": True,
            "create_additional_metadata": True,
            "exclude_translators": True,
            "output_single_author": False,
            "log_level": "WARNING"
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Merge user config with defaults
                    default_config.update(user_config)
                    if hasattr(self, 'logger'):
                        pass  # Remove config loading logging
            else:
                # Create default config file
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                if hasattr(self, 'logger'):
                    pass  # Remove default config creation logging
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.warning(f"Error loading configuration: {e}. Using defaults.")
        
        return default_config
    
    def clean_html_text(self, html_text: str) -> str:
        """Clean HTML text and format for plain text files"""
        if not html_text:
            return ""
        
        # Replace common HTML entities
        html_text = html_text.replace('&nbsp;', ' ')
        html_text = html_text.replace('&amp;', '&')
        html_text = html_text.replace('&lt;', '<')
        html_text = html_text.replace('&gt;', '>')
        html_text = html_text.replace('&quot;', '"')
        html_text = html_text.replace('&#39;', "'")
        html_text = html_text.replace('&apos;', "'")
        html_text = html_text.replace('&ldquo;', '"')
        html_text = html_text.replace('&rdquo;', '"')
        html_text = html_text.replace('&lsquo;', "'")
        html_text = html_text.replace('&rsquo;', "'")
        html_text = html_text.replace('&mdash;', '—')
        html_text = html_text.replace('&ndash;', '–')
        html_text = html_text.replace('&hellip;', '...')
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', html_text)
        
        # Split into paragraphs and clean each one
        paragraphs = clean_text.split('\n')
        clean_text = '\n\n'.join([p.strip() for p in paragraphs if p.strip()])
        
        # Add periods to sentences that don't end with punctuation
        sentences = clean_text.split('. ')
        cleaned_sentences = []
        for sentence in sentences:
            if sentence and not sentence.endswith(('.', '!', '?')):
                sentence += '.'
            cleaned_sentences.append(sentence)
        
        return '. '.join(cleaned_sentences)
    
    def create_additional_metadata_files(self, dest_dir: Path, metadata: Dict, cover_path: Optional[str] = None) -> None:
        """Create additional metadata files compatible with Audiobookshelf"""
        # Check if additional metadata creation is enabled
        if not self.config.get('create_additional_metadata', True):
            return
            
        try:
            # Create desc.txt (description)
            if metadata.get('description'):
                desc_content = self.clean_html_text(metadata['description'])
                if desc_content:
                    desc_file = dest_dir / "desc.txt"
                    with open(desc_file, 'w', encoding='utf-8') as f:
                        f.write(desc_content)
                    # Remove description file creation logging
            
            # Create reader.txt (narrator)
            if metadata.get('narrator'):
                reader_file = dest_dir / "reader.txt"
                with open(reader_file, 'w', encoding='utf-8') as f:
                    f.write(metadata['narrator'])
                # Remove narrator file creation logging
            
            # Create OPF file (Open Packaging Format)
            opf_content = self.create_opf_content(metadata)
            if opf_content:
                opf_file = dest_dir / f"{metadata.get('asin', 'book')}.opf"
                with open(opf_file, 'w', encoding='utf-8') as f:
                    f.write(opf_content)
                # Remove OPF file creation logging
            
            # Copy cover image to book folder if available
            if cover_path and Path(cover_path).exists():
                cover_dest = dest_dir / "cover.jpg"
                try:
                    shutil.copy2(cover_path, cover_dest)
                    # Remove cover copy logging
                except Exception as e:
                    self.logger.warning(f"Could not copy cover to book folder: {e}")
            
        except Exception as e:
            self.logger.error(f"Error creating additional metadata files: {e}")
    
    def create_opf_content(self, metadata: Dict) -> str:
        """Create OPF content for Audiobookshelf compatibility"""
        try:
            from xml.sax.saxutils import escape
            
            # Extract basic information with proper None handling
            title = metadata.get('title') or 'Unknown Title'
            author = metadata.get('author') or 'Unknown Author'
            narrator = metadata.get('narrator', '')
            publisher = metadata.get('publisher_name', '')
            isbn = metadata.get('isbn', '')
            description = self.clean_html_text(metadata.get('description', ''))
            language = metadata.get('language', 'en')
            series = metadata.get('series', '')
            series_part = metadata.get('series_part', '')
            
            # Extract publish year from release date
            publish_year = ''
            if metadata.get('release_date'):
                try:
                    publish_year = metadata['release_date'][:4]
                except:
                    pass
            
            # Create genres list
            genres = metadata.get('genres', [])
            genres_text = ', '.join(genres) if genres else ''
            
            # Create OPF content with conditional fields
            opf_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:identifier id="BookId">{metadata.get('asin', 'unknown')}</dc:identifier>
        <dc:title>{escape(title)}</dc:title>
        <dc:creator>{escape(author)}</dc:creator>"""
            
            # Add optional fields only if they have content
            if publisher:
                opf_content += f'\n        <dc:publisher>{escape(publisher)}</dc:publisher>'
            else:
                opf_content += '\n        <dc:publisher></dc:publisher>'
                
            opf_content += f'\n        <dc:language>{language}</dc:language>'
            
            if description:
                opf_content += f'\n        <dc:description>{escape(description)}</dc:description>'
            else:
                opf_content += '\n        <dc:description></dc:description>'
                
            if genres_text:
                opf_content += f'\n        <dc:subject>{escape(genres_text)}</dc:subject>'
            else:
                opf_content += '\n        <dc:subject></dc:subject>'
                
            if publish_year:
                opf_content += f'\n        <dc:date>{publish_year}</dc:date>'
            else:
                opf_content += '\n        <dc:date></dc:date>'
                
            opf_content += f'\n        <dc:identifier opf:scheme="ISBN">{escape(isbn)}</dc:identifier>'
            opf_content += f'\n        <dc:identifier opf:scheme="ASIN">{metadata.get("asin", "")}</dc:identifier>'
            
            # Add narrator if available
            if narrator:
                opf_content += f'\n        <dc:contributor role="nrt">{escape(narrator)}</dc:contributor>'
            
            # Add series information if available
            if series:
                opf_content += f'\n        <dc:subject opf:authority="series">{escape(series)}</dc:subject>'
                if series_part:
                    opf_content += f'\n        <meta property="series-part">{series_part}</meta>'
            
            # Close OPF content
            opf_content += """\n    </metadata>
<manifest>
    <item id="cover" href="cover.jpg" media-type="image/jpeg"/>
</manifest>
<spine>
    <itemref idref="cover"/>
</spine>
</package>"""
            
            return opf_content
            
        except Exception as e:
            self.logger.error(f"Error creating OPF content: {e}")
            return ""
    
    def process_authors(self, authors_list: List[Dict]) -> str:
        """Process authors list according to configuration settings"""
        if not authors_list:
            return 'Unknown Author'
        
        # Baked-in translator keywords
        translator_keywords = [
            "traducteur", "traductrice", "translator", "traductor", "traductora",
            "übersetzer", "übersetzerin", "traduttore", "traduttrice",
            "翻訳者", "번역가", "переводчик", "переводчица"
        ]
        
        # Get author handling configuration
        exclude_translators = self.config.get('exclude_translators', True)
        output_single_author = self.config.get('output_single_author', False)
        
        # Filter authors
        filtered_authors = []
        for author in authors_list:
            author_name = author.get('name', '').strip()
            if not author_name:
                continue
                
            # Skip translators if enabled
            if exclude_translators:
                is_translator = any(keyword.lower() in author_name.lower() for keyword in translator_keywords)
                if is_translator:
                    continue
            
            filtered_authors.append(author_name)
        
        # If no authors after filtering, return original list
        if not filtered_authors:
            filtered_authors = [author.get('name', '').strip() for author in authors_list if author.get('name', '').strip()]
        
        # Return single author or all authors based on configuration
        if output_single_author and filtered_authors:
            return filtered_authors[0]
        else:
            return ', '.join(filtered_authors) if filtered_authors else 'Unknown Author'
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Use absolute path for log file
        log_file = logs_dir / "tagger.log"
        
        # Use default log level initially
        log_level = logging.INFO
        
        # Try to set up file logging, fallback to console only if permission denied
        try:
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    # Remove console handler to reduce output
                ]
            )
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"Tagger logging initialized. Log file: {log_file}")
        except PermissionError:
            # Fallback to console logging only
            logging.basicConfig(
                level=log_level,
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
                level=log_level,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
            self.logger.error(f"Error setting up file logging: {e}, using console logging only")
    
    def update_logging_level(self):
        """Update logging level based on config after config is loaded"""
        if hasattr(self, 'config'):
            log_level_str = self.config.get('log_level', 'INFO').upper()
            log_level = getattr(logging, log_level_str, logging.INFO)
            logging.getLogger().setLevel(log_level)
            self.logger.setLevel(log_level)
            # Remove log level update message
    
    def parse_filename(self, filename: str) -> Tuple[str, str]:
        """Parse filename to extract title and author"""
        # Remove .m4b extension
        name = filename.replace('.m4b', '')
        
        # Handle empty filename
        if not name.strip():
            return "Unknown Title", "Unknown Author"
        
        # Common patterns for author - title format (in order of specificity)
        patterns = [
            r'^(.+?)\s*by\s*(.+)$',      # Title by Author (most specific)
            r'^(.+?)\s*\((.+?)\)$',      # Title (Author)
            r'^([^-–—]+?)\s*[-–—]\s*(.+)$',  # Author - Title (least specific)
        ]
        
        for pattern in patterns:
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                if 'by' in pattern:
                    # Title by Author format
                    return match.group(1).strip(), match.group(2).strip()
                elif '(' in pattern:
                    # Title (Author) format
                    return match.group(1).strip(), match.group(2).strip()
                elif '[-–—]' in pattern:
                    # Author - Title format
                    return match.group(2).strip(), match.group(1).strip()
                else:
                    # Fallback
                    return match.group(1).strip(), match.group(2).strip()
        
        # If no pattern matches, assume the whole name is the title
        return name.strip(), "Unknown Author"
    
    def search_audible(self, query: str) -> List[Dict]:
        """Search Audible for books matching the query using the official API"""
        try:
            # Use baked-in search locales with preferred locale first
            locales = ['com', 'co.uk', 'ca', 'fr', 'de', 'it', 'es', 'co.jp', 'com.au', 'com.br']
            preferred_locale = self.config.get('preferred_locale', 'com')
            
            # Put preferred locale first in search order
            if preferred_locale in locales:
                locales.remove(preferred_locale)
            locales.insert(0, preferred_locale)
            
            results = []
            
            for locale in locales:
                try:
                    # Search API endpoint
                    search_url = f"https://api.audible.{locale}/1.0/catalog/products"
                    params = {
                        'keywords': query,
                        'response_groups': 'category_ladders,contributors,media,product_desc,product_attrs,product_extended_attrs,rating,series',
                        'image_sizes': '500,1000',
                        'num_results': '5'
                    }
                    
                    # Remove verbose search logging
                    response = requests.get(search_url, params=params, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    if 'products' in data:
                        for product in data['products']:
                            # Extract basic info
                            asin = product.get('asin', '')
                            title = product.get('title', 'Unknown Title')
                            
                            # Extract authors using the new processing method
                            author = self.process_authors(product.get('authors', []))
                            
                            # Extract narrators
                            narrators = []
                            if 'narrators' in product:
                                for narrator in product['narrators']:
                                    narrators.append(narrator.get('name', ''))
                            
                            narrator = ', '.join(narrators) if narrators else ''
                            
                            # Check if we already have this ASIN
                            if not any(r['asin'] == asin for r in results):
                                results.append({
                                    'title': title,
                                    'author': author,
                                    'narrator': narrator,
                                    'asin': asin,
                                    'locale': locale
                                })
                        
                        # If we found results, we can stop searching other locales
                        if results:
                            break
                            
                except Exception as e:
                    self.logger.warning(f"Error searching Audible {locale}: {e}")
                    continue
            
            return results[:5]  # Limit to 5 results
            
        except Exception as e:
            self.logger.error(f"Error searching Audible: {e}")
            return []
    
    def get_book_details(self, asin: str, locale: str = 'com') -> Optional[Dict]:
        """Get detailed book information from Audible using the official API"""
        try:
            # Use the official Audible API
            url = f"https://api.audible.{locale}/1.0/catalog/products/{asin}"
            params = {
                'response_groups': 'category_ladders,contributors,media,product_desc,product_attrs,product_extended_attrs,rating,series',
                'image_sizes': '500,1000'
            }
            
            # Remove verbose details logging
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"API Response keys: {list(data.keys())}")
            
            if 'product' not in data:
                self.logger.error(f"No 'product' key in API response. Available keys: {list(data.keys())}")
                return None
                
            product = data['product']
            self.logger.info(f"Product keys: {list(product.keys())}")
            
            # Extract comprehensive metadata based on Mp3tag reference
            details = {
                'asin': asin,
                'title': product.get('title', ''),
                'subtitle': product.get('subtitle', ''),
                'author': '',
                'authors': [],
                'narrator': '',
                'narrators': [],
                'series': '',
                'series_part': '',
                'description': '',
                'publisher_summary': '',
                'runtime_length_min': '',
                'rating': '',
                'release_date': '',
                'release_time': '',
                'language': '',
                'format_type': '',
                'publisher_name': '',
                'is_adult_product': False,
                'cover_url': '',
                'genres': [],
                'copyright': '',
                'isbn': '',
                'explicit': False
            }
            
            # Extract authors using the new processing method
            if 'authors' in product:
                details['authors'] = [author.get('name', '') for author in product['authors'] if author.get('name')]
                details['author'] = self.process_authors(product['authors'])
            
            # Extract narrators
            if 'narrators' in product:
                for narrator in product['narrators']:
                    details['narrators'].append(narrator.get('name', ''))
                details['narrator'] = ', '.join(details['narrators'])
            
            # Extract series information
            if 'series' in product:
                series_list = product['series']
                if series_list:
                    series_info = series_list[0]  # Take the first series
                    details['series'] = series_info.get('title', '')
                    details['series_part'] = str(series_info.get('sequence', ''))
            
            # Extract description/summary
            if 'publisher_summary' in product:
                details['publisher_summary'] = product['publisher_summary']
                details['description'] = product['publisher_summary']
                self.logger.info(f"Found description: {product['publisher_summary'][:100]}...")
            else:
                self.logger.warning(f"No publisher_summary found in product data. Available keys: {list(product.keys())}")
                # Try alternative description fields
                if 'merchandising_summary' in product:
                    details['publisher_summary'] = product['merchandising_summary']
                    details['description'] = product['merchandising_summary']
                    self.logger.info(f"Using merchandising_summary as description")
                elif 'product_desc' in product:
                    details['publisher_summary'] = product['product_desc']
                    details['description'] = product['product_desc']
                    self.logger.info(f"Using product_desc as description")
                else:
                    # Final fallback - use empty string
                    details['publisher_summary'] = ''
                    details['description'] = ''
                    self.logger.warning(f"No description found, using empty string")
            
            # Extract runtime
            if 'runtime_length_min' in product:
                details['runtime_length_min'] = str(product['runtime_length_min'])
            
            # Extract rating
            if 'rating' in product:
                rating = product['rating']
                if 'overall_distribution' in rating:
                    overall = rating['overall_distribution']
                    details['rating'] = overall.get('display_average_rating', '')
            
            # Extract release date
            if 'publication_datetime' in product:
                details['release_date'] = product['publication_datetime']
                # Also extract just the date part for RELEASETIME
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(product['publication_datetime'].replace('Z', '+00:00'))
                    details['release_time'] = dt.strftime('%Y-%m-%d')
                except:
                    details['release_time'] = product['publication_datetime'][:10] if len(product['publication_datetime']) >= 10 else ''
            
            # Extract language
            details['language'] = product.get('language', '')
            
            # Extract format type
            details['format_type'] = product.get('format_type', '')
            
            # Extract publisher
            details['publisher_name'] = product.get('publisher_name', '')
            
            # Extract adult content flag
            details['is_adult_product'] = product.get('is_adult_product', False)
            details['explicit'] = product.get('is_adult_product', False)
            
            # Extract cover image
            if 'product_images' in product:
                images = product['product_images']
                details['cover_url'] = images.get('1000', images.get('500', ''))
            
            # Extract genres from category ladders
            if 'category_ladders' in product:
                for ladder in product['category_ladders']:
                    if ladder.get('root') == 'Genres':
                        for category in ladder.get('ladder', []):
                            details['genres'].append(category.get('name', ''))
            
            # Extract copyright and ISBN from extended attributes
            if 'product_extended_attrs' in product:
                ext_attrs = product['product_extended_attrs']
                details['copyright'] = ext_attrs.get('copyright', '')
                details['isbn'] = ext_attrs.get('isbn', '')
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error fetching book details: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def download_cover(self, cover_url: str, asin: str) -> Optional[str]:
        """Download and save cover image with robust fallback handling"""
        try:
            if not cover_url or not self.config.get('embed_covers', True):
                return None
                
            response = requests.get(cover_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Try multiple approaches to save the cover
            save_attempts = [
                # Primary attempt - covers directory
                lambda: self._save_cover_to_path(self.covers_dir / f"{asin}.jpg", response.content),
                # Fallback 1 - /tmp directory
                lambda: self._save_cover_to_path(Path("/tmp") / f"{asin}.jpg", response.content),
                # Fallback 2 - /tmp with prefix
                lambda: self._save_cover_to_path(Path("/tmp") / f"cover_{asin}.jpg", response.content),
                # Fallback 3 - temp file in covers directory
                lambda: self._save_cover_to_path(self.covers_dir / f"temp_{asin}.jpg", response.content),
                # Fallback 4 - current working directory
                lambda: self._save_cover_to_path(Path.cwd() / f"cover_{asin}.jpg", response.content),
                # Fallback 5 - system temp directory
                lambda: self._save_cover_to_path(Path("/var/tmp") / f"{asin}.jpg", response.content),
            ]
            
            for i, save_attempt in enumerate(save_attempts):
                try:
                    result = save_attempt()
                    if result:
                        self.logger.info(f"Successfully saved cover (attempt {i+1}): {result}")
                        return result
                except Exception as e:
                    self.logger.warning(f"Cover save attempt {i+1} failed: {e}")
                    continue
            
            # If all attempts fail, log and return None
            self.logger.error("All cover save attempts failed, skipping cover")
            return None
            
        except Exception as e:
            self.logger.error(f"Error downloading cover: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def _save_cover_to_path(self, cover_path: Path, content: bytes) -> Optional[str]:
        """Helper method to save cover content to a specific path"""
        try:
            # Ensure parent directory exists
            cover_path.parent.mkdir(exist_ok=True, parents=True)
            
            # Try to write the file
            with open(cover_path, 'wb') as f:
                f.write(content)
            
            # Verify the file was written successfully
            if cover_path.exists() and cover_path.stat().st_size > 0:
                return str(cover_path)
            else:
                raise Exception("File was not written successfully")
                
        except Exception as e:
            self.logger.debug(f"Failed to save to {cover_path}: {e}")
            raise
    
    def tag_file(self, file_path: Path, metadata: Dict, cover_path: Optional[str] = None) -> bool:
        """Tag the .m4b file with comprehensive metadata using ffmpeg"""
        try:
            # Remove verbose metadata logging
            
            # Check file permissions first
            if not os.access(file_path, os.W_OK):
                self.logger.error(f"File is not writable: {file_path}")
                return False
            
            # Create a backup before tagging
            backup_path = file_path.with_suffix('.m4b.backup')
            try:
                shutil.copy2(file_path, backup_path)
                # Remove backup creation logging
            except Exception as e:
                self.logger.warning(f"Could not create backup: {e}")
            
            # Tag with ffmpeg
            return self.tag_with_ffmpeg(file_path, metadata, cover_path)
                
        except Exception as e:
            self.logger.error(f"Error tagging file {file_path}: {e}")
            return False
    

    
    def tag_with_ffmpeg(self, file_path: Path, metadata: Dict, cover_path: Optional[str] = None) -> bool:
        """Tag using ffmpeg with comprehensive metadata matching Mp3tag Audible API Web Source"""
        try:
            # Remove ffmpeg tagging logging
            
            # Prepare ffmpeg command
            cmd = [
                'ffmpeg',
                '-i', str(file_path),
            ]
            
            # Add cover art if available
            if cover_path and self.config.get('embed_covers', True):
                cmd.extend(['-i', cover_path])
            
            # Add output options
            cmd.extend([
                '-c', 'copy',  # Copy streams without re-encoding
            ])
            
            # Add cover art mapping if cover is provided
            if cover_path and self.config.get('embed_covers', True):
                cmd.extend(['-map', '0:a', '-map', '1:v', '-disposition:v:0', 'attached_pic'])
            
            # Build comprehensive metadata list matching Mp3tag Audible API Web Source
            metadata_list = []
            
            # Basic fields (using exact Mp3tag field names)
            metadata_list.extend([
                ('TITLE', metadata.get("title", "")),
                ('ALBUM', metadata.get("title", "")),
                ('YEAR', metadata.get("release_date", "")[:4] if metadata.get("release_date") else ""),
                ('ASIN', metadata.get("asin", "")),
                ('ISBN', metadata.get("isbn", "")),
                ('COPYRIGHT', metadata.get("copyright", "")),
                ('LANGUAGE', metadata.get("language", "")),
                ('FORMAT', metadata.get("format_type", "")),
                ('PUBLISHER', metadata.get("publisher_name", "")),
                ('SUBTITLE', metadata.get("subtitle", "")),
                ('RELEASETIME', metadata.get("release_time", "")),
            ])
            
            # Author/Artist handling (matching Mp3tag behavior)
            if metadata.get('authors'):
                if len(metadata['authors']) == 1:
                    # Single author
                    metadata_list.extend([
                        ('ARTIST', metadata['authors'][0]),
                        ('ALBUMARTIST', metadata['authors'][0]),
                    ])
                else:
                    # Multiple authors
                    author_list = "; ".join(metadata['authors'])
                    metadata_list.extend([
                        ('ARTIST', author_list),
                        ('ALBUMARTIST', metadata['authors'][0]),  # First author as album_artist
                        ('ALBUMARTISTS', author_list),  # All authors
                    ])
            
            # Narrator/Composer handling
            if metadata.get('narrators'):
                if len(metadata['narrators']) == 1:
                    metadata_list.extend([
                        ('COMPOSER', metadata['narrators'][0]),
                    ])
                else:
                    metadata_list.extend([
                        ('COMPOSER', "; ".join(metadata['narrators'])),
                    ])
            
            # Series information
            if metadata.get('series'):
                series_name = metadata['series']
                series_part = metadata.get('series_part', '')
                
                metadata_list.extend([
                    ('SERIES', series_name),
                    ('MOVEMENTNAME', series_name),
                    ('CONTENTGROUP', f"{series_name} #{series_part}" if series_part else series_name),
                ])
                
                if series_part:
                    metadata_list.extend([
                        ('SERIES-PART', series_part),
                        ('MOVEMENT', series_part),
                    ])
                
                # Set show_movement for M4B
                metadata_list.append(('SHOWMOVEMENT', '1'))
            
            # Description/Summary
            if metadata.get('description'):
                metadata_list.extend([
                    ('COMMENT', metadata['description']),
                    ('DESCRIPTION', metadata['description']),
                ])
            
            # Genres
            if metadata.get('genres'):
                metadata_list.extend([
                    ('GENRE', "/".join(metadata['genres'])),
                ])
            
            # Rating
            if metadata.get('rating'):
                metadata_list.extend([
                    ('RATING', metadata['rating']),
                ])
            
            # Adult content flags
            if metadata.get('is_adult_product'):
                metadata_list.extend([
                    ('EXPLICIT', '1'),
                    ('ITUNESADVISORY', '1'),
                ])
            else:
                metadata_list.extend([
                    ('EXPLICIT', '0'),
                    ('ITUNESADVISORY', '2'),
                ])
            
            # iTunes specific fields for M4B
            metadata_list.extend([
                ('ITUNESGAPLESS', '1'),
                ('ITUNESMEDIATYPE', 'Audiobook'),
            ])
            
            # Audible URL
            if metadata.get('asin'):
                locale = self.config.get('preferred_locale', 'com')
                metadata_list.append(('WWWAUDIOFILE', f"https://www.audible.{locale}/pd/{metadata['asin']}"))
            
            # Album sort order (matching Mp3tag logic)
            if metadata.get('series'):
                if metadata.get('series_part'):
                    album_sort = f"{metadata['series']} #{metadata['series_part']} - {metadata.get('title', '')}"
                else:
                    album_sort = f"{metadata['series']} - {metadata.get('title', '')}"
            elif metadata.get('subtitle'):
                album_sort = f"{metadata.get('title', '')} - {metadata['subtitle']}"
            else:
                album_sort = metadata.get('title', '')
            
            metadata_list.append(('ALBUMSORT', album_sort))
            
            # Add all metadata to ffmpeg command
            for key, value in metadata_list:
                if value:  # Only add non-empty values
                    cmd.extend(['-metadata', f'{key}={value}'])
            
            # Output file - use a different name to avoid conflicts
            output_path = file_path.with_name(f"{file_path.stem}_tagged.m4b")
            cmd.append(str(output_path))
            
            # Remove ffmpeg command logging
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                # Remove ffmpeg success logging
                
                # Replace original with tagged file
                os.remove(file_path)
                os.rename(output_path, file_path)
                # Remove file replacement logging
                
                # Clean up backup file
                backup_path = file_path.with_suffix('.m4b.backup')
                if backup_path.exists():
                    os.remove(backup_path)
                    # Remove backup removal logging
                
                # Verify tags (but don't fail the entire process)
                verification_result = self.verify_ffmpeg_tags(file_path, metadata)
                
                # Verify cover art if it was supposed to be embedded
                if cover_path and self.config.get('embed_covers', True):
                    if not self.verify_cover_art(file_path):
                        self.logger.warning("⚠️ Cover art may not have been embedded correctly")
                
                # Return True even if verification had warnings - the file was still processed
                return True
            else:
                self.logger.error(f"ffmpeg error: {result.stderr}")
                self.logger.error(f"ffmpeg stdout: {result.stdout}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error with ffmpeg tagging: {e}")
            return False
    
    def verify_ffmpeg_tags(self, file_path: Path, expected_metadata: Dict) -> bool:
        """Verify tags using ffprobe"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', str(file_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                format_info = data.get('format', {})
                tags = format_info.get('tags', {})
                
                # Remove ffprobe metadata logging
                
                # Check if expected tags are present
                expected_title = expected_metadata.get('title', '')
                expected_artist = expected_metadata.get('author', '')
                expected_description = expected_metadata.get('description', '')
                
                verification_passed = True
                
                if expected_title and expected_title not in str(tags):
                    self.logger.warning(f"Expected title '{expected_title}' not found in metadata")
                    verification_passed = False
                
                if expected_artist and expected_artist not in str(tags):
                    self.logger.warning(f"Expected artist '{expected_artist}' not found in metadata")
                    verification_passed = False
                
                if expected_description and expected_description not in str(tags):
                    self.logger.warning(f"Expected description not found in metadata")
                    verification_passed = False
                
                # Return True even if some tags are missing - just log warnings
                if not verification_passed:
                    self.logger.warning("Some expected tags were not found, but continuing with processing...")
                
                return True
            else:
                self.logger.warning(f"Could not read metadata with ffprobe: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying ffmpeg tags: {e}")
            return False
    

    def verify_cover_art(self, file_path: Path) -> bool:
        """Verify that cover art was embedded in the file"""
        try:
            # Use ffprobe to check if artwork exists
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', str(file_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                streams = data.get('streams', [])
                
                # Check if there's a video stream (cover art)
                for stream in streams:
                    if stream.get('codec_type') == 'video':
                        # Remove cover art verification logging
                        return True
                
                self.logger.warning(f"No cover art found in: {file_path}")
                return False
            else:
                self.logger.warning(f"Could not verify cover art for: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying cover art: {e}")
            return False
    

    
    def extract_cover_art(self, file_path: Path, output_path: Path) -> bool:
        """Extract cover art from file to verify it was embedded"""
        try:
            # Use ffmpeg to extract cover art
            cmd = ['ffmpeg', '-i', str(file_path), '-vf', 'select=eq(n\\,0)', '-vframes', '1', str(output_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                # Check if image file was created
                if output_path.exists():
                    # Remove cover art extraction logging
                    return True
                else:
                    self.logger.warning(f"No cover art could be extracted from: {file_path}")
                    return False
            else:
                self.logger.warning(f"Could not extract cover art from: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error extracting cover art: {e}")
            return False
    
    def move_to_library(self, file_path: Path, metadata: Dict, cover_path: Optional[str] = None) -> Path:
        """Move tagged file to organized library structure"""
        try:
            # Create directory structure: library/Author/Series/Title.m4b
            author = metadata.get('author', 'Unknown Author')
            series = metadata.get('series', '')
            title = metadata.get('title', 'Unknown Title')
            
            # Clean names for filesystem with Unicode handling
            def clean_filename(name: str) -> str:
                """Clean filename for filesystem compatibility"""
                if not name:
                    return 'Unknown'
                # Remove or replace problematic characters
                cleaned = re.sub(r'[<>:"/\\|?*]', '_', name)
                # Handle Unicode characters that might cause issues
                cleaned = cleaned.encode('utf-8', errors='replace').decode('utf-8')
                # Remove leading/trailing spaces and dots
                cleaned = cleaned.strip(' .')
                return cleaned if cleaned else 'Unknown'
            
            author_clean = clean_filename(author)
            series_clean = clean_filename(series) if series else ''
            title_clean = clean_filename(title)
            
            # Get series part number if available
            series_part = metadata.get('series_part', '')
            
            # Create filename with series number if available (if enabled in config)
            if self.config.get('include_series_in_filename', True):
                if series_part and series_clean:
                    # Include series number in the filename
                    filename = f"{title_clean} ({series_clean} #{series_part}).m4b"
                elif series_clean:
                    # Include series name without number
                    filename = f"{title_clean} ({series_clean}).m4b"
                else:
                    # No series information
                    filename = f"{title_clean}.m4b"
            else:
                # Don't include series in filename
                filename = f"{title_clean}.m4b"
            
            # Create destination path - each book gets its own folder
            if series_clean:
                # For series: library/Author/Series/Title (Series #1)/Title (Series #1).m4b
                if series_part and self.config.get('include_series_in_filename', True):
                    folder_name = f"{title_clean} ({series_clean} #{series_part})"
                elif self.config.get('include_series_in_filename', True):
                    folder_name = f"{title_clean} ({series_clean})"
                else:
                    folder_name = title_clean
                dest_dir = self.library_dir / author_clean / series_clean / folder_name
            else:
                # For standalone: library/Author/Title/Title.m4b
                dest_dir = self.library_dir / author_clean / title_clean
            
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / filename
            
            # Move file with proper Unicode handling
            try:
                shutil.move(str(file_path), str(dest_path))
                # Remove file move logging
            except UnicodeEncodeError as e:
                self.logger.error(f"Unicode error moving file: {e}")
                # Fallback: try with encoded path
                encoded_src = str(file_path).encode('utf-8', errors='replace').decode('utf-8')
                encoded_dest = str(dest_path).encode('utf-8', errors='replace').decode('utf-8')
                shutil.move(encoded_src, encoded_dest)
                # Remove encoded file move logging
            
            # Create additional metadata files for Audiobookshelf compatibility
            self.create_additional_metadata_files(dest_dir, metadata, cover_path)
            
            return dest_path
            
        except Exception as e:
            self.logger.error(f"Error moving file to library: {e}")
            return file_path
    
    def display_book_info(self, metadata: Dict) -> None:
        """Display comprehensive book information in a formatted way"""
        print(f"\n{Fore.CYAN}📚 Book Information:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Title:{Style.RESET_ALL} {metadata.get('title', 'Unknown')}")
        if metadata.get('subtitle'):
            print(f"{Fore.YELLOW}Subtitle:{Style.RESET_ALL} {metadata['subtitle']}")
        print(f"{Fore.YELLOW}Author:{Style.RESET_ALL} {metadata.get('author', 'Unknown')}")
        if metadata.get('narrator'):
            print(f"{Fore.YELLOW}Narrator:{Style.RESET_ALL} {metadata['narrator']}")
        if metadata.get('series'):
            series_info = metadata['series']
            if metadata.get('series_part'):
                series_info += f" #{metadata['series_part']}"
            print(f"{Fore.YELLOW}Series:{Style.RESET_ALL} {series_info}")
        if metadata.get('runtime_length_min'):
            print(f"{Fore.YELLOW}Duration:{Style.RESET_ALL} {metadata['runtime_length_min']} minutes")
        if metadata.get('rating'):
            print(f"{Fore.YELLOW}Rating:{Style.RESET_ALL} {metadata['rating']}")
        if metadata.get('language'):
            print(f"{Fore.YELLOW}Language:{Style.RESET_ALL} {metadata['language']}")
        if metadata.get('format_type'):
            print(f"{Fore.YELLOW}Format:{Style.RESET_ALL} {metadata['format_type']}")
        if metadata.get('publisher_name'):
            print(f"{Fore.YELLOW}Publisher:{Style.RESET_ALL} {metadata['publisher_name']}")
        if metadata.get('release_date'):
            print(f"{Fore.YELLOW}Release Date:{Style.RESET_ALL} {metadata['release_date']}")
        if metadata.get('genres'):
            print(f"{Fore.YELLOW}Genres:{Style.RESET_ALL} {', '.join(metadata['genres'])}")
        if metadata.get('description'):
            print(f"{Fore.YELLOW}Description:{Style.RESET_ALL} {metadata['description'][:200]}...")
        print()
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single .m4b file"""
        try:
            # Remove file processing logging
            
            # Parse filename
            title, author = self.parse_filename(file_path.name)
            
            # Build search query - exclude "Unknown Author" from search
            if author == "Unknown Author":
                search_query = title.strip()
            else:
                search_query = f"{title} {author}".strip()
            
            print(f"\n{Fore.GREEN}🔍 Processing: {file_path.name}{Style.RESET_ALL}")
            print(f"Parsed as: {title} by {author}")
            
            # Search Audible
            results = self.search_audible(search_query)
            
            if not results:
                print(f"{Fore.RED}No results found for: {search_query}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Options:{Style.RESET_ALL}")
                print("1. Enter custom search query")
                print("2. Enter title only")
                print("3. Enter author only")
                print("4. Skip this file")
                
                choice = input(f"\n{Fore.CYAN}Choose option (1-4): {Style.RESET_ALL}").strip()
                
                if choice == "1":
                    custom_query = input("Enter custom search query: ").strip()
                    if custom_query:
                        results = self.search_audible(custom_query)
                elif choice == "2":
                    title_only = input("Enter book title: ").strip()
                    if title_only:
                        results = self.search_audible(title_only)
                elif choice == "3":
                    author_only = input("Enter author name: ").strip()
                    if author_only:
                        results = self.search_audible(author_only)
                elif choice == "4":
                    return False
                else:
                    print(f"{Fore.RED}Invalid choice. Skipping file.{Style.RESET_ALL}")
                    return False
            
            if not results:
                print(f"{Fore.RED}No results found. Skipping file.{Style.RESET_ALL}")
                return False
            
            # Display search results
            print(f"\n{Fore.CYAN}📖 Search Results:{Style.RESET_ALL}")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']} by {result['author']}")
                if result.get('narrator'):
                    print(f"   Narrated by: {result['narrator']}")
            
            # Get user selection with option to search again
            while True:
                try:
                    choice = input(f"\nSelect book (1-{len(results)}) or 's' to skip, 'r' to search again: ").strip()
                    if choice.lower() == 's':
                        return False
                    elif choice.lower() == 'r':
                        print(f"{Fore.YELLOW}Search options:{Style.RESET_ALL}")
                        print("1. Enter custom search query")
                        print("2. Enter title only")
                        print("3. Enter author only")
                        
                        search_choice = input(f"{Fore.CYAN}Choose search option (1-3): {Style.RESET_ALL}").strip()
                        
                        if search_choice == "1":
                            custom_query = input("Enter custom search query: ").strip()
                            if custom_query:
                                results = self.search_audible(custom_query)
                        elif search_choice == "2":
                            title_only = input("Enter book title: ").strip()
                            if title_only:
                                results = self.search_audible(title_only)
                        elif search_choice == "3":
                            author_only = input("Enter author name: ").strip()
                            if author_only:
                                results = self.search_audible(author_only)
                        else:
                            print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
                            continue
                        
                        if not results:
                            print(f"{Fore.RED}No results found. Skipping file.{Style.RESET_ALL}")
                            return False
                        
                        # Display new results
                        print(f"\n{Fore.CYAN}📖 New Search Results:{Style.RESET_ALL}")
                        for i, result in enumerate(results, 1):
                            print(f"{i}. {result['title']} by {result['author']}")
                            if result.get('narrator'):
                                print(f"   Narrated by: {result['narrator']}")
                        continue
                    
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(results):
                        selected = results[choice_idx]
                        break
                    else:
                        print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")
            
            # Get detailed book information
            details = self.get_book_details(selected['asin'], selected.get('locale', 'com'))
            if not details:
                print(f"{Fore.RED}Failed to get book details. Skipping file.{Style.RESET_ALL}")
                return False
            
            # Display book information
            self.display_book_info(details)
            
            # Proceed directly with tagging (user already confirmed by selecting the book)
            
            # Download cover
            cover_path = None
            if details.get('cover_url'):
                cover_path = self.download_cover(details['cover_url'], details['asin'])
            
            # Tag the file
            if self.tag_file(file_path, details, cover_path):
                # Verify cover art was embedded
                if cover_path:
                    cover_embedded = self.verify_cover_art(file_path)
                    if cover_embedded:
                        print(f"{Fore.GREEN}🖼️ Cover art embedded successfully{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}⚠️ Cover art may not have been embedded{Style.RESET_ALL}")
                
                # Move to library
                final_path = self.move_to_library(file_path, details, cover_path)
                print(f"{Fore.GREEN}✅ Successfully processed: {file_path.name}{Style.RESET_ALL}")
                
                # Final verification of the moved file
                if cover_path:
                    self.verify_cover_art(final_path)
                
                return True
            else:
                print(f"{Fore.RED}❌ Failed to process: {file_path.name}{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return False
    
    def run(self):
        """Main execution loop"""
        print(f"{Fore.CYAN}🎧 Audible Audiobook Tagger{Style.RESET_ALL}")
        print(f"Scanning directory: {self.incoming_dir}")
        
        # Find all .m4b files
        m4b_files = list(self.incoming_dir.rglob("*.m4b"))
        
        if not m4b_files:
            print(f"{Fore.YELLOW}No .m4b files found in {self.incoming_dir}{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}Found {len(m4b_files)} .m4b file(s){Style.RESET_ALL}")
        
        # Process each file
        processed = 0
        for file_path in tqdm(m4b_files, desc="Processing files"):
            if self.process_file(file_path):
                processed += 1
        
        print(f"\n{Fore.GREEN}🎉 Processing complete!{Style.RESET_ALL}")
        print(f"Successfully processed: {processed}/{len(m4b_files)} files")
        print(f"Check the library directory for organized files.")
    
    def test_cover_art(self, file_path: str):
        """Test function to verify cover art embedding"""
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return
        
        print(f"Testing cover art for: {file_path}")
        
        # Verify cover art exists
        has_art = self.verify_cover_art(file_path)
        print(f"Cover art detected: {has_art}")
        
        if has_art:
            # Extract cover art to verify
            extract_path = self.covers_dir / f"extracted_{file_path.stem}"
            extracted = self.extract_cover_art(file_path, extract_path)
            print(f"Cover art extracted: {extracted}")
            
            if extracted:
                extracted_files = list(self.covers_dir.glob(f"extracted_{file_path.stem}*"))
                if extracted_files:
                    print(f"Extracted cover art saved to: {extracted_files[0]}")

if __name__ == "__main__":
    import sys
    
    tagger = AudibleTagger()
    
    # Check if testing cover art
    if len(sys.argv) > 1 and sys.argv[1] == "--test-cover":
        if len(sys.argv) > 2:
            tagger.test_cover_art(sys.argv[2])
        else:
            print("Usage: python tagger.py --test-cover <file_path>")
    else:
        tagger.run() 