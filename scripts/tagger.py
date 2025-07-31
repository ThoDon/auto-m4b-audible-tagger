#!/usr/bin/env python3
"""
Audible Audiobook Tagger
Automatically tags .m4b files with metadata from Audible's API
"""

import os
import re
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from colorama import init, Fore, Style
from tqdm import tqdm
from mutagen.mp4 import MP4, MP4Cover, MP4FreeForm

# Initialize colorama for cross-platform colored output
init()


# Constants for better maintainability
class TagConstants:
    """Constants for M4B tag names - Compliant with MP3Tag's Audible API.inc"""

    # Basic tags
    TITLE = "\xa9nam"
    ALBUM = "\xa9alb"
    YEAR = "\xa9day"
    ARTIST = "\xa9ART"
    ALBUM_ARTIST = "aART"
    COMPOSER = "\xa9wrt"
    COMMENT = "\xa9cmt"
    COPYRIGHT = "\xa9cpy"
    GENRE = "\xa9gen"

    # iTunes custom tags
    ASIN = "----:com.apple.iTunes:ASIN"
    LANGUAGE = "----:com.apple.iTunes:LANGUAGE"
    FORMAT = "----:com.apple.iTunes:FORMAT"
    SUBTITLE = "----:com.apple.iTunes:SUBTITLE"
    RELEASETIME = "----:com.apple.iTunes:RELEASETIME"
    ALBUMARTISTS = "----:com.apple.iTunes:ALBUMARTISTS"
    SERIES = "----:com.apple.iTunes:SERIES"
    SERIES_PART = "----:com.apple.iTunes:SERIES-PART"
    RATING = "----:com.apple.iTunes:RATING"
    RATING_WMP = "----:com.apple.iTunes:RATING WMP"
    EXPLICIT = "----:com.apple.iTunes:EXPLICIT"
    WWWAUDIOFILE = "----:com.apple.iTunes:WWWAUDIOFILE"
    AUDIBLE_ASIN = "----:com.apple.iTunes:AUDIBLE_ASIN"

    # Alternative tags for compatibility
    ALBUM_SORT = "soal"
    SHOW_MOVEMENT_ALT = "shwm"
    GAPLESS_ALT = "pgap"
    STICK = "stik"
    SIMPLE_ASIN = "asin"
    CDEK_ASIN = "CDEK"
    DESC_ALT = "desc"
    DESC_ALT2 = "\xa9des"
    PUBLISHER_ALT = "\xa9pub"
    NARRATOR_ALT = "\xa9nrt"
    SERIES_ALT = "\xa9mvn"
    GROUP = "\xa9grp"


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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
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
            "log_level": "WARNING",
            # Mp3tag Audible API Web Source compatibility settings
            "add_narrator_to_artist": False,
            "add_single_album_artist_only": True,
            "add_single_genre_only": False,
            "genre_delimiter": "/",
            "auto_tag_enabled": False,  # New: Enable auto-tagging
        }

        try:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    # Merge user config with defaults
                    default_config.update(user_config)
                    if hasattr(self, "logger"):
                        pass  # Remove config loading logging
            else:
                # Create default config file
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                if hasattr(self, "logger"):
                    pass  # Remove default config creation logging

        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.warning(
                    f"Error loading configuration: {e}. Using defaults."
                )

        return default_config

    def clean_html_text(self, html_text: str) -> str:
        """Clean HTML text and format for plain text files"""
        if not html_text:
            return ""

        # Replace common HTML entities
        html_text = html_text.replace("&nbsp;", " ")
        html_text = html_text.replace("&amp;", "&")
        html_text = html_text.replace("&lt;", "<")
        html_text = html_text.replace("&gt;", ">")
        html_text = html_text.replace("&quot;", '"')
        html_text = html_text.replace("&#39;", "'")
        html_text = html_text.replace("&apos;", "'")
        html_text = html_text.replace("&ldquo;", '"')
        html_text = html_text.replace("&rdquo;", '"')
        html_text = html_text.replace("&lsquo;", "'")
        html_text = html_text.replace("&rsquo;", "'")
        html_text = html_text.replace("&mdash;", "—")
        html_text = html_text.replace("&ndash;", "–")
        html_text = html_text.replace("&hellip;", "...")

        # Remove HTML tags
        clean_text = re.sub(r"<[^>]+>", "", html_text)

        # Split into paragraphs and clean each one
        paragraphs = clean_text.split("\n")
        clean_text = "\n\n".join([p.strip() for p in paragraphs if p.strip()])

        # Return cleaned text without adding periods
        return clean_text

    def _ensure_string(self, value) -> str:
        """Ensure a value is a string, handling bytes and other types safely"""
        if isinstance(value, str):
            return value
        elif isinstance(value, bytes):
            try:
                return value.decode("utf-8", errors="replace")
            except UnicodeDecodeError:
                return str(value)
        else:
            return str(value)

    def create_additional_metadata_files(
        self,
        dest_dir: Path,
        metadata: Dict,
        cover_path: Optional[str] = None,
        file_path: Optional[Path] = None,
    ) -> None:
        """Create additional metadata files compatible with Audiobookshelf"""
        # Check if additional metadata creation is enabled
        if not self.config.get("create_additional_metadata", True):
            return

        try:
            # Create desc.txt (description)
            if metadata.get("description"):
                desc_content = metadata["description"]
                desc_file = dest_dir / "desc.txt"
                with open(desc_file, "w", encoding="utf-8") as f:
                    f.write(desc_content)

            # Create reader.txt (narrator)
            if metadata.get("narrator"):
                reader_file = dest_dir / "reader.txt"
                with open(reader_file, "w", encoding="utf-8") as f:
                    f.write(metadata["narrator"])

            # Create OPF file (Open Packaging Format)
            opf_content = self.create_opf_content(metadata)
            if opf_content:
                # Use the same name as the .m4b file but with .opf extension
                if file_path:
                    m4b_name = file_path.stem  # Get filename without extension
                else:
                    m4b_name = metadata.get("asin", "book")  # Fallback to ASIN
                opf_file = dest_dir / f"{m4b_name}.opf"
                with open(opf_file, "w", encoding="utf-8") as f:
                    f.write(opf_content)

            # Copy cover image to book folder if available
            if cover_path and Path(cover_path).exists():
                cover_dest = dest_dir / "cover.jpg"
                try:
                    shutil.copy2(cover_path, cover_dest)
                except Exception as e:
                    self.logger.warning(f"Could not copy cover to book folder: {e}")

        except Exception as e:
            self.logger.error(f"Error creating additional metadata files: {e}")

    def create_opf_content(self, metadata: Dict) -> str:
        """Create OPF content for Audiobookshelf compatibility"""
        try:
            from xml.sax.saxutils import escape

            # Extract basic information with proper None handling
            title = metadata.get("title") or "Unknown Title"
            author = metadata.get("author") or "Unknown Author"
            narrator = metadata.get("narrator", "")
            publisher = metadata.get("publisher_name", "")
            isbn = metadata.get("isbn", "")
            description = self.clean_html_text(metadata.get("description", ""))
            language = metadata.get("language", "en")
            series = metadata.get("series", "")
            series_part = metadata.get("series_part", "")

            # Extract publish year from release date
            publish_year = ""
            if metadata.get("release_date"):
                try:
                    publish_year = metadata["release_date"][:4]
                except:
                    pass

            # Create genres list
            genres = metadata.get("genres", [])
            genres_text = ", ".join(genres) if genres else ""

            # Create OPF content with conditional fields
            opf_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:identifier id="BookId">{metadata.get('asin', 'unknown')}</dc:identifier>
        <dc:title>{escape(title)}</dc:title>
        <dc:creator>{escape(author)}</dc:creator>"""

            # Add optional fields only if they have content
            if publisher:
                opf_content += (
                    f"\n        <dc:publisher>{escape(publisher)}</dc:publisher>"
                )
            else:
                opf_content += "\n        <dc:publisher></dc:publisher>"

            opf_content += f"\n        <dc:language>{language}</dc:language>"

            if description:
                opf_content += (
                    f"\n        <dc:description>{escape(description)}</dc:description>"
                )
            else:
                opf_content += "\n        <dc:description></dc:description>"

            if genres_text:
                opf_content += (
                    f"\n        <dc:subject>{escape(genres_text)}</dc:subject>"
                )
            else:
                opf_content += "\n        <dc:subject></dc:subject>"

            if publish_year:
                opf_content += f"\n        <dc:date>{publish_year}</dc:date>"
            else:
                opf_content += "\n        <dc:date></dc:date>"

            opf_content += f'\n        <dc:identifier opf:scheme="ASIN">{metadata.get("asin", "")}</dc:identifier>'

            # Add narrator if available
            if narrator:
                opf_content += f'\n        <dc:contributor role="nrt">{escape(narrator)}</dc:contributor>'

            # Add series information if available
            if series:
                opf_content += f'\n        <dc:subject opf:authority="series">{escape(series)}</dc:subject>'
                if series_part:
                    opf_content += (
                        f'\n        <meta property="series-part">{series_part}</meta>'
                    )

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
            return "Unknown Author"

        # Baked-in translator keywords
        translator_keywords = [
            "traducteur",
            "traductrice",
            "translator",
            "traductor",
            "traductora",
            "übersetzer",
            "übersetzerin",
            "traduttore",
            "traduttrice",
            "翻訳者",
            "번역가",
            "переводчик",
            "переводчица",
        ]

        # Get author handling configuration
        exclude_translators = self.config.get("exclude_translators", True)
        output_single_author = self.config.get("output_single_author", False)

        # Filter authors
        filtered_authors = []
        for author in authors_list:
            author_name = author.get("name", "").strip()
            if not author_name:
                continue

            # Skip translators if enabled
            if exclude_translators:
                is_translator = any(
                    keyword.lower() in author_name.lower()
                    for keyword in translator_keywords
                )
                if is_translator:
                    continue

            filtered_authors.append(author_name)

        # If no authors after filtering, return original list
        if not filtered_authors:
            filtered_authors = [
                author.get("name", "").strip()
                for author in authors_list
                if author.get("name", "").strip()
            ]

        # Return single author or all authors based on configuration
        if output_single_author and filtered_authors:
            return filtered_authors[0]
        else:
            return ", ".join(filtered_authors) if filtered_authors else "Unknown Author"

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
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[
                    logging.FileHandler(log_file),
                ],
            )
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"Tagger logging initialized. Log file: {log_file}")
        except PermissionError:
            # Fallback to console logging only
            logging.basicConfig(
                level=log_level,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[logging.StreamHandler()],
            )
            self.logger = logging.getLogger(__name__)
            self.logger.warning(
                f"Permission denied writing to {log_file}, using console logging only"
            )
        except Exception as e:
            # Fallback to console logging only
            logging.basicConfig(
                level=log_level,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[logging.StreamHandler()],
            )
            self.logger = logging.getLogger(__name__)
            self.logger.error(
                f"Error setting up file logging: {e}, using console logging only"
            )

    def update_logging_level(self):
        """Update logging level based on config after config is loaded"""
        if hasattr(self, "config"):
            log_level_str = self.config.get("log_level", "INFO").upper()
            log_level = getattr(logging, log_level_str, logging.INFO)
            logging.getLogger().setLevel(log_level)
            self.logger.setLevel(log_level)

    def parse_filename(self, filename: str) -> Tuple[str, str]:
        """Parse filename to extract title and author"""
        # Remove .m4b extension
        name = filename.replace(".m4b", "")

        # Handle empty filename
        if not name.strip():
            return "Unknown Title", "Unknown Author"

        # Common patterns for author - title format (in order of specificity)
        patterns = [
            r"^(.+?)\s*by\s*(.+)$",  # Title by Author (most specific)
            r"^(.+?)\s*\((.+?)\s*#\d+\.?\d*\)$",  # Title (Serie's name #book number)
            r"^(.+?)\s*\((.+?)\)$",  # Title (Author)
            r"^([^-–—]+?)\s*[-–—]\s*(.+)$",  # Author - Title (least specific)
        ]

        for i, pattern in enumerate(patterns):
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                if i == 0:  # Title by Author format
                    return match.group(1).strip(), match.group(2).strip()
                elif i == 1:  # Title (Serie's name #book number) format
                    # For series, only return the title, not the series name
                    return match.group(1).strip(), "Unknown Author"
                elif i == 2:  # Title (Author) format
                    return match.group(1).strip(), match.group(2).strip()
                elif i == 3:  # Author - Title format
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
            locales = [
                "com",
                "co.uk",
                "ca",
                "fr",
                "de",
                "it",
                "es",
                "co.jp",
                "com.au",
                "com.br",
            ]
            preferred_locale = self.config.get("preferred_locale", "com")

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
                        "keywords": query,
                        "response_groups": "category_ladders,contributors,media,product_desc,product_attrs,product_extended_attrs,rating,series",
                        "image_sizes": "500,1000",
                        "num_results": "5",
                    }

                    response = requests.get(
                        search_url, params=params, headers=self.headers, timeout=10
                    )
                    response.raise_for_status()

                    data = response.json()
                    if "products" in data:
                        for product in data["products"]:
                            # Extract basic info
                            asin = product.get("asin", "")
                            title = product.get("title", "Unknown Title")

                            # Extract authors using the new processing method
                            author = self.process_authors(product.get("authors", []))

                            # Extract narrators
                            narrators = []
                            if "narrators" in product:
                                for narrator in product["narrators"]:
                                    narrators.append(narrator.get("name", ""))

                            narrator = ", ".join(narrators) if narrators else ""

                            # Extract series information
                            series_info = ""
                            if "series" in product and product["series"]:
                                series_list = product["series"]
                                if series_list:
                                    series_info = series_list[0].get("title", "")
                                    if series_list[0].get("sequence"):
                                        series_info += f" #{series_list[0]['sequence']}"

                            # Check if we already have this ASIN
                            if not any(r["asin"] == asin for r in results):
                                results.append(
                                    {
                                        "title": title,
                                        "author": author,
                                        "narrator": narrator,
                                        "series": series_info,
                                        "asin": asin,
                                        "locale": locale,
                                    }
                                )

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

    def get_book_details(self, asin: str, locale: str = "com") -> Optional[Dict]:
        """Get detailed book information from Audible using the official API"""
        try:
            # Use the official Audible API
            url = f"https://api.audible.{locale}/1.0/catalog/products/{asin}"
            params = {
                "response_groups": "category_ladders,contributors,media,product_desc,product_attrs,product_extended_attrs,rating,series",
                "image_sizes": "500,1000",
            }

            response = requests.get(
                url, params=params, headers=self.headers, timeout=10
            )
            response.raise_for_status()

            data = response.json()
            self.logger.info(f"API Response keys: {list(data.keys())}")

            if "product" not in data:
                self.logger.error(
                    f"No 'product' key in API response. Available keys: {list(data.keys())}"
                )
                return None

            product = data["product"]
            self.logger.info(f"Product keys: {list(product.keys())}")

            # Extract comprehensive metadata based on Mp3tag reference
            details = {
                "asin": asin,
                "title": product.get("title", ""),
                "subtitle": product.get("subtitle", ""),
                "author": "",
                "authors": [],
                "narrator": "",
                "narrators": [],
                "series": "",
                "series_part": "",
                "description": "",
                "publisher_summary": "",
                "runtime_length_min": "",
                "rating": "",
                "release_date": "",
                "release_time": "",
                "language": "",
                "format_type": "",
                "publisher_name": "",
                "is_adult_product": False,
                "cover_url": "",
                "genres": [],
                "copyright": "",
                "isbn": "",
                "explicit": False,
            }

            # Extract authors using the new processing method
            if "authors" in product:
                details["authors"] = [
                    author.get("name", "")
                    for author in product["authors"]
                    if author.get("name")
                ]
                details["author"] = self.process_authors(product["authors"])

            # Extract narrators
            if "narrators" in product:
                for narrator in product["narrators"]:
                    details["narrators"].append(narrator.get("name", ""))
                details["narrator"] = ", ".join(details["narrators"])

            # Extract series information
            if "series" in product:
                series_list = product["series"]
                if series_list:
                    series_info = series_list[0]  # Take the first series
                    details["series"] = series_info.get("title", "")
                    details["series_part"] = str(series_info.get("sequence", ""))

            # Extract description/summary
            if "publisher_summary" in product:
                clean_summary = self.clean_html_text(product["publisher_summary"])
                details["publisher_summary"] = clean_summary
                details["description"] = clean_summary
                self.logger.info(
                    f"Found description: {product['publisher_summary'][:100]}..."
                )
            else:
                self.logger.warning(
                    f"No publisher_summary found in product data. Available keys: {list(product.keys())}"
                )
                # Try alternative description fields
                if "merchandising_summary" in product:
                    details["publisher_summary"] = product["merchandising_summary"]
                    details["description"] = product["merchandising_summary"]
                    self.logger.info(f"Using merchandising_summary as description")
                elif "product_desc" in product:
                    details["publisher_summary"] = product["product_desc"]
                    details["description"] = product["product_desc"]
                    self.logger.info(f"Using product_desc as description")
                else:
                    # Final fallback - use empty string
                    details["publisher_summary"] = ""
                    details["description"] = ""
                    self.logger.warning(f"No description found, using empty string")

            # Extract runtime
            if "runtime_length_min" in product:
                details["runtime_length_min"] = str(product["runtime_length_min"])

            # Extract rating
            if "rating" in product:
                rating = product["rating"]
                if "overall_distribution" in rating:
                    overall = rating["overall_distribution"]
                    details["rating"] = overall.get("display_average_rating", "")

            # Extract release date
            if "publication_datetime" in product:
                details["release_date"] = product["publication_datetime"]
                # Also extract just the date part for RELEASETIME
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(
                        product["publication_datetime"].replace("Z", "+00:00")
                    )
                    details["release_time"] = dt.strftime("%Y-%m-%d")
                except:
                    details["release_time"] = (
                        product["publication_datetime"][:10]
                        if len(product["publication_datetime"]) >= 10
                        else ""
                    )

            # Extract language
            details["language"] = product.get("language", "")

            # Extract format type
            details["format_type"] = product.get("format_type", "")

            # Extract publisher
            details["publisher_name"] = product.get("publisher_name", "")

            # Extract adult content flag
            details["is_adult_product"] = product.get("is_adult_product", False)
            details["explicit"] = product.get("is_adult_product", False)

            # Extract cover image
            if "product_images" in product:
                images = product["product_images"]
                details["cover_url"] = images.get("1000", images.get("500", ""))

            # Extract genres from category ladders
            if "category_ladders" in product:
                for ladder in product["category_ladders"]:
                    if ladder.get("root") == "Genres":
                        for category in ladder.get("ladder", []):
                            details["genres"].append(category.get("name", ""))

            # Extract copyright and ISBN from extended attributes
            if "product_extended_attrs" in product:
                ext_attrs = product["product_extended_attrs"]
                details["copyright"] = ext_attrs.get("copyright", "")

            return details

        except Exception as e:
            self.logger.error(f"Error fetching book details: {e}")
            import traceback

            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def download_cover(self, cover_url: str, asin: str) -> Optional[str]:
        """Download and save cover image"""
        try:
            if not cover_url or not self.config.get("embed_covers", True):
                return None

            response = requests.get(cover_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            # Save cover to covers directory
            cover_path = self.covers_dir / f"{asin}.jpg"
            return self._save_cover_to_path(cover_path, response.content)

        except Exception as e:
            self.logger.error(f"Error downloading cover: {e}")
            return None

    def _save_cover_to_path(self, cover_path: Path, content: bytes) -> Optional[str]:
        """Helper method to save cover content to a specific path"""
        try:
            # Ensure parent directory exists
            cover_path.parent.mkdir(exist_ok=True, parents=True)

            # Try to write the file
            with open(cover_path, "wb") as f:
                f.write(content)

            # Verify the file was written successfully
            if cover_path.exists() and cover_path.stat().st_size > 0:
                return str(cover_path)
            else:
                raise Exception("File was not written successfully")

        except Exception as e:
            self.logger.debug(f"Failed to save to {cover_path}: {e}")
            raise

    def tag_file(
        self, file_path: Path, metadata: Dict, cover_path: Optional[str] = None
    ) -> bool:
        """Tag the .m4b file with comprehensive metadata using mutagen"""
        backup_path = None
        try:
            # Check file permissions first
            if not os.access(file_path, os.W_OK):
                self.logger.error(f"File is not writable: {file_path}")
                return False

            # Create a backup before tagging
            backup_path = file_path.with_suffix(".m4b.backup")
            try:
                shutil.copy2(file_path, backup_path)
                # Remove backup creation logging
            except Exception as e:
                self.logger.warning(f"Could not create backup: {e}")

            # Tag with mutagen
            success = self.tag_with_mutagen(file_path, metadata, cover_path)

            # Remove backup if tagging was successful
            if success and backup_path and backup_path.exists():
                try:
                    backup_path.unlink()
                except Exception as e:
                    self.logger.warning(
                        f"Could not remove backup file {backup_path}: {e}"
                    )

            return success

        except Exception as e:
            self.logger.error(f"Error tagging file {file_path}: {e}")
            # Remove backup on error as well
            if backup_path and backup_path.exists():
                try:
                    backup_path.unlink()
                except Exception as backup_error:
                    self.logger.warning(
                        f"Could not remove backup file {backup_path}: {backup_error}"
                    )
            return False

    def _build_basic_tags(self, metadata: Dict) -> Dict:
        """Build basic metadata tags"""
        tags = {}

        if metadata.get("title"):
            tags[TagConstants.TITLE] = metadata["title"]  # Title
            tags[TagConstants.ALBUM] = metadata["title"]  # Album

        if metadata.get("release_date"):
            year = metadata["release_date"][:4]
            if year:
                tags[TagConstants.YEAR] = year  # Year

        if metadata.get("copyright"):
            tags[TagConstants.COPYRIGHT] = metadata["copyright"]

        return tags

    def _build_custom_tags(self, metadata: Dict) -> Dict:
        """Build custom iTunes tags"""
        tags = {}

        if metadata.get("asin"):
            tags[TagConstants.ASIN] = self._ensure_string(metadata["asin"])

        if metadata.get("language"):
            tags[TagConstants.LANGUAGE] = self._ensure_string(metadata["language"])

        if metadata.get("format_type"):
            tags[TagConstants.FORMAT] = self._ensure_string(metadata["format_type"])

        if metadata.get("subtitle"):
            tags[TagConstants.SUBTITLE] = self._ensure_string(metadata["subtitle"])

        if metadata.get("release_time"):
            tags[TagConstants.RELEASETIME] = self._ensure_string(
                metadata["release_time"]
            )

        return tags

    def _build_author_tags(self, metadata: Dict) -> Dict:
        """Build author and artist related tags"""
        tags = {}

        # Handle single album artist setting (Mp3tag compatibility)
        single_album_artist = self.config.get("add_single_album_artist_only", True)

        if metadata.get("authors"):
            # Handle both list of strings and list of dictionaries
            if isinstance(metadata["authors"][0], str):
                # List of strings (author names)
                author_names = [
                    name.strip() for name in metadata["authors"] if name.strip()
                ]
                author_count = len(author_names)
            else:
                # List of dictionaries (original format)
                author_count = 0
                for author in metadata["authors"]:
                    if author.get("asin"):  # Only count authors with ASIN
                        author_count += 1

                author_names = []
                for author in metadata["authors"]:
                    if author.get("asin"):
                        author_name = author.get("name", "").strip()
                        if author_name:
                            author_names.append(author_name)

            if author_count > 1 and single_album_artist:
                # Multiple authors - set ALBUMARTISTS for all, ALBUMARTIST for first only
                if author_names:
                    tags["\xa9ART"] = ", ".join(author_names)  # ARTIST (all authors)
                    tags["aART"] = author_names[0]  # ALBUMARTIST (first author only)
                    tags[TagConstants.ALBUMARTISTS] = ", ".join(
                        author_names
                    )  # ALBUMARTISTS (all authors)
            else:
                # Single author or multiple authors without single album artist setting
                if author_names:
                    author_list = ", ".join(author_names)
                    tags["\xa9ART"] = author_list  # ARTIST
                    tags["aART"] = author_list  # ALBUMARTIST
        elif metadata.get("author"):
            # Fallback to single author field
            tags["\xa9ART"] = metadata["author"]  # ARTIST
            tags["aART"] = metadata["author"]  # ALBUMARTIST

        # Set ARTIST tag based on single album artist setting (Audible API.inc logic)
        if single_album_artist and TagConstants.ALBUMARTISTS in tags:
            tags["\xa9ART"] = tags[TagConstants.ALBUMARTISTS]  # ARTIST = ALBUMARTISTS
        elif "aART" in tags:
            tags["\xa9ART"] = tags["aART"]  # ARTIST = ALBUMARTIST
        # If neither condition is met, \xa9ART is already set above or will remain unset

        return tags

    def _build_narrator_tags(self, metadata: Dict) -> Dict:
        """Build narrator and composer related tags"""
        tags = {}

        # Build narrator list from narrators array
        if metadata.get("narrators"):
            narrator_names = []
            # Handle both list of strings and list of dictionaries
            if isinstance(metadata["narrators"][0], str):
                # List of strings (narrator names)
                narrator_names = [
                    name.strip() for name in metadata["narrators"] if name.strip()
                ]
            else:
                # List of dictionaries (original format)
                for narrator in metadata["narrators"]:
                    narrator_name = narrator.get("name", "").strip()
                    if narrator_name:
                        narrator_names.append(narrator_name)

            if narrator_names:
                tags["\xa9wrt"] = ", ".join(narrator_names)  # COMPOSER (Narrator)
        elif metadata.get("narrator"):
            # Fallback to single narrator field
            tags["\xa9wrt"] = metadata["narrator"]  # COMPOSER (Narrator)

        # Note: Narrator to artist logic is handled in _build_missing_audible_api_tags
        # to ensure proper access to the accumulated tags dictionary

        return tags

    def _build_series_tags(self, metadata: Dict) -> Dict:
        """Build series related tags"""
        tags = {}

        # Check if series exists
        series_count = 0
        if metadata.get("series"):
            series_count = (
                1  # Simplified for now, could be enhanced to count multiple series
            )

        if series_count > 0:
            series_name = self._ensure_string(metadata.get("series", ""))
            series_part = self._ensure_string(metadata.get("series_part", ""))

            tags[TagConstants.SHOW_MOVEMENT_ALT] = "1"  # Alternative show movement tag

            # Set series tags
            if series_name:
                tags[TagConstants.SERIES] = series_name  # SERIES

                if series_part:
                    # Series with part number
                    tags[TagConstants.SERIES_PART] = series_part  # SERIES-PART

        return tags

    def _build_description_tags(self, metadata: Dict) -> Dict:
        """Build description and comment tags"""
        tags = {}

        cleaned_description = metadata.get("description", "")
        if cleaned_description:
            tags[TagConstants.COMMENT] = (
                cleaned_description  # COMMENT (Publisher's Summary for MP3)
            )
            tags[TagConstants.DESC_ALT] = (
                cleaned_description  # Alternative description tag
            )
            tags[TagConstants.DESC_ALT2] = (
                cleaned_description  # Alternative description tag
            )

        return tags

    def _build_genre_tags(self, metadata: Dict) -> Dict:
        """Build genre related tags"""
        tags = {}

        if metadata.get("genres"):
            single_genre = self.config.get("add_single_genre_only", False)

            if single_genre and len(metadata["genres"]) > 1:
                # Single genre mode - first genre in GENRE, others in TMP_GENRE1, TMP_GENRE2
                tags[TagConstants.GENRE] = metadata["genres"][
                    0
                ]  # GENRE (first genre only)

            else:
                # Multiple genres with delimiter
                delimiter = self.config.get("genre_delimiter", "/")
                tags[TagConstants.GENRE] = delimiter.join(
                    metadata["genres"]
                )  # GENRE (Genre1/Genre2)

        return tags

    def _build_rating_tags(self, metadata: Dict) -> Dict:
        """Build rating related tags"""
        tags = {}

        if metadata.get("rating"):
            tags[TagConstants.RATING] = metadata["rating"]  # RATING (Audible Rating)
            tags[TagConstants.RATING_WMP] = metadata[
                "rating"
            ]  # RATING WMP (Audible Rating for MP3)

        return tags

    def _build_adult_content_tags(self, metadata: Dict) -> Dict:
        """Build adult content flags"""
        tags = {}

        if metadata.get("is_adult_product"):
            tags[TagConstants.EXPLICIT] = "1"  # EXPLICIT (Set to 1 if adult content)
        else:
            tags[TagConstants.EXPLICIT] = "0"  # EXPLICIT (Set to 0 if clean)

        return tags

    def _build_itunes_tags(self) -> Dict:
        """Build iTunes specific tags"""
        tags = {}

        tags[TagConstants.GAPLESS_ALT] = "True"  # Alternative gapless tag
        tags[TagConstants.STICK] = "2"  # Audiobook stick

        return tags

    def _build_audible_tags(self, metadata: Dict) -> Dict:
        """Build Audible specific tags"""
        tags = {}

        if metadata.get("asin"):
            locale = self.config.get("preferred_locale", "com")
            audible_url = f"https://www.audible.{locale}/pd/{metadata['asin']}"
            tags[TagConstants.WWWAUDIOFILE] = (
                audible_url  # WWWAUDIOFILE (Audible Album URL)
            )
            tags[TagConstants.ASIN] = metadata[
                "asin"
            ]  # ASIN (Amazon Standard Identification Number)
            tags[TagConstants.AUDIBLE_ASIN] = metadata["asin"]  # Additional ASIN tag
            tags[TagConstants.SIMPLE_ASIN] = metadata["asin"]  # Simple ASIN tag
            tags[TagConstants.CDEK_ASIN] = metadata["asin"]  # Alternative ASIN tag

        return tags

    def _build_album_sort_tag(self, metadata: Dict) -> Dict:
        """Build album sort tag"""
        tags = {}

        if metadata.get("series"):
            if metadata.get("series_part"):
                album_sort = f"{metadata['series']} {metadata['series_part']} - {metadata.get('title', '')}"  # Series Series-Part - Title
            else:
                album_sort = f"{metadata['series']} - {metadata.get('title', '')}"  # Series - Title
        elif metadata.get("subtitle"):
            album_sort = f"{metadata.get('title', '')} - {metadata['subtitle']}"  # Title - Subtitle
        else:
            album_sort = metadata.get("title", "")  # Title only

        if album_sort:
            tags[TagConstants.ALBUM_SORT] = album_sort  # ALBUMSORT

        return tags

    def _build_compatibility_tags(self, metadata: Dict) -> Dict:
        """Build additional compatibility tags"""
        tags = {}

        if metadata.get("publisher_name"):
            tags[TagConstants.PUBLISHER_ALT] = metadata[
                "publisher_name"
            ]  # Alternative publisher tag

        if metadata.get("narrator"):
            tags[TagConstants.NARRATOR_ALT] = metadata[
                "narrator"
            ]  # Alternative narrator tag

        if metadata.get("series"):
            tags[TagConstants.SERIES_ALT] = metadata["series"]  # Alternative series tag
            if metadata.get("series_part"):
                tags[TagConstants.GROUP] = (
                    f"{metadata['series']}, Book #{metadata['series_part']}"  # Group tag
                )
            else:
                tags[TagConstants.GROUP] = metadata["series"]  # Group tag without part

        return tags

    def _build_missing_audible_api_tags(
        self, metadata: Dict, current_tags: Dict = None
    ) -> Dict:
        """Build missing tags from Audible API.inc specification"""
        tags = {}

        # Add narrator to artist if configured (Mp3tag setting)
        if metadata.get("narrator") and self.config.get(
            "add_narrator_to_artist", False
        ):
            # Get current artist from the tags being built (current_tags is the tags dict being built)
            current_artist = current_tags.get("\xa9ART", "") if current_tags else ""

            # Debug logging to identify the source of byte strings
            if isinstance(current_artist, bytes):
                self.logger.debug(
                    f"Found byte string in current_artist: {current_artist}"
                )
                current_artist = current_artist.decode("utf-8", errors="replace")
            elif not isinstance(current_artist, str):
                self.logger.debug(
                    f"Found non-string type in current_artist: {type(current_artist)} - {current_artist}"
                )
                current_artist = str(current_artist)

            if current_artist:
                tags["\xa9ART"] = (
                    f"{current_artist}, {self._ensure_string(metadata['narrator'])}"
                )
            else:
                tags["\xa9ART"] = self._ensure_string(metadata["narrator"])

        return tags

    def tag_with_mutagen(
        self, file_path: Path, metadata: Dict, cover_path: Optional[str] = None
    ) -> bool:
        """Tag using mutagen with comprehensive metadata matching Mp3tag Audible API Web Source"""
        try:

            # Load the M4B file
            audio = MP4(file_path)
            # Build comprehensive metadata dictionary using helper methods
            tags = {}

            # Build all tag categories
            tags.update(self._build_basic_tags(metadata))
            tags.update(self._build_custom_tags(metadata))
            tags.update(self._build_author_tags(metadata))
            tags.update(self._build_narrator_tags(metadata))
            tags.update(self._build_series_tags(metadata))
            tags.update(self._build_description_tags(metadata))
            tags.update(self._build_genre_tags(metadata))
            tags.update(self._build_rating_tags(metadata))
            tags.update(self._build_adult_content_tags(metadata))
            tags.update(self._build_itunes_tags())
            tags.update(self._build_audible_tags(metadata))
            tags.update(self._build_album_sort_tag(metadata))
            tags.update(self._build_compatibility_tags(metadata))
            tags.update(self._build_missing_audible_api_tags(metadata, tags))

            # Debug: Print tags before applying
            self.logger.debug(f"Built tags: {tags}")

            # Apply all tags with proper data types
            for key, value in tags.items():
                try:
                    if key.startswith("----:"):
                        # Freeform tags need to be MP4FreeForm objects
                        audio.tags[key] = [MP4FreeForm(value.encode("utf-8"))]
                    elif key in [
                        "shwm",
                        "stik",
                        "rtng",
                    ]:
                        # Integer tags
                        audio.tags[key] = [int(value)]
                    else:
                        # Standard tags can be strings
                        audio.tags[key] = [value]
                except Exception as tag_error:
                    self.logger.error(
                        f"Error applying tag {key} with value {value}: {tag_error}"
                    )
                    # Continue with other tags instead of failing completely
                    continue

            # Add cover art if available
            if cover_path and self.config.get("embed_covers", True):
                try:
                    with open(cover_path, "rb") as f:
                        cover_data = f.read()
                    audio["covr"] = [MP4Cover(cover_data)]
                except Exception as e:
                    self.logger.warning(f"Could not embed cover art: {e}")

            # Save the file
            audio.save()

            return True

        except Exception as e:
            self.logger.error(f"Error with mutagen tagging: {e}")
            import traceback

            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def move_to_library(
        self, file_path: Path, metadata: Dict, cover_path: Optional[str] = None
    ) -> Path:
        """Move tagged file to organized library structure"""
        try:
            # Create directory structure: library/Author/Series/Title.m4b
            author = metadata.get("author", "Unknown Author")
            series = metadata.get("series", "")
            title = metadata.get("title", "Unknown Title")

            # Clean names for filesystem with Unicode handling
            def clean_filename(name: str) -> str:
                """Clean filename for filesystem compatibility"""
                if not name:
                    return "Unknown"
                # Remove or replace problematic characters
                cleaned = re.sub(r'[<>:"/\\|?*]', "_", name)
                # Handle Unicode characters that might cause issues
                cleaned = cleaned.encode("utf-8", errors="replace").decode("utf-8")
                # Remove leading/trailing spaces and dots
                cleaned = cleaned.strip(" .")
                return cleaned if cleaned else "Unknown"

            author_clean = clean_filename(author)
            series_clean = clean_filename(series) if series else ""
            title_clean = clean_filename(title)

            # Get series part number if available
            series_part = metadata.get("series_part", "")

            # Create filename with series number if available (if enabled in config)
            if self.config.get("include_series_in_filename", True):
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
                if series_part and self.config.get("include_series_in_filename", True):
                    folder_name = f"{title_clean} ({series_clean} #{series_part})"
                elif self.config.get("include_series_in_filename", True):
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
                encoded_src = (
                    str(file_path).encode("utf-8", errors="replace").decode("utf-8")
                )
                encoded_dest = (
                    str(dest_path).encode("utf-8", errors="replace").decode("utf-8")
                )
                shutil.move(encoded_src, encoded_dest)

            # Create additional metadata files for Audiobookshelf compatibility
            self.create_additional_metadata_files(
                dest_dir, metadata, cover_path, file_path
            )

            return dest_path

        except Exception as e:
            self.logger.error(f"Error moving file to library: {e}")
            return file_path

    def display_book_info(self, metadata: Dict) -> None:
        """Display comprehensive book information in a formatted way"""
        print(f"\n{Fore.CYAN}📚 Book Information:{Style.RESET_ALL}")
        print(
            f"{Fore.YELLOW}Title:{Style.RESET_ALL} {metadata.get('title', 'Unknown')}"
        )
        if metadata.get("subtitle"):
            print(f"{Fore.YELLOW}Subtitle:{Style.RESET_ALL} {metadata['subtitle']}")
        print(
            f"{Fore.YELLOW}Author:{Style.RESET_ALL} {metadata.get('author', 'Unknown')}"
        )
        if metadata.get("narrator"):
            print(f"{Fore.YELLOW}Narrator:{Style.RESET_ALL} {metadata['narrator']}")
        if metadata.get("series"):
            series_info = metadata["series"]
            if metadata.get("series_part"):
                series_info += f" #{metadata['series_part']}"
            print(f"{Fore.YELLOW}Series:{Style.RESET_ALL} {series_info}")
        if metadata.get("runtime_length_min"):
            print(
                f"{Fore.YELLOW}Duration:{Style.RESET_ALL} {metadata['runtime_length_min']} minutes"
            )
        if metadata.get("rating"):
            print(f"{Fore.YELLOW}Rating:{Style.RESET_ALL} {metadata['rating']}")
        if metadata.get("language"):
            print(f"{Fore.YELLOW}Language:{Style.RESET_ALL} {metadata['language']}")
        if metadata.get("format_type"):
            print(f"{Fore.YELLOW}Format:{Style.RESET_ALL} {metadata['format_type']}")
        if metadata.get("publisher_name"):
            print(
                f"{Fore.YELLOW}Publisher:{Style.RESET_ALL} {metadata['publisher_name']}"
            )
        if metadata.get("release_date"):
            print(
                f"{Fore.YELLOW}Release Date:{Style.RESET_ALL} {metadata['release_date']}"
            )
        if metadata.get("genres"):
            print(
                f"{Fore.YELLOW}Genres:{Style.RESET_ALL} {', '.join(metadata['genres'])}"
            )
        if metadata.get("description"):
            print(
                f"{Fore.YELLOW}Description:{Style.RESET_ALL} {metadata['description'][:200]}..."
            )
        print()

    def _handle_no_search_results(self, search_query: str) -> Optional[List[Dict]]:
        """Handle case when no search results are found - UI logic"""
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
                return self.search_audible(custom_query)
        elif choice == "2":
            title_only = input("Enter book title: ").strip()
            if title_only:
                return self.search_audible(title_only)
        elif choice == "3":
            author_only = input("Enter author name: ").strip()
            if author_only:
                return self.search_audible(author_only)
        elif choice == "4":
            return None

        print(f"{Fore.RED}Invalid choice. Skipping file.{Style.RESET_ALL}")
        return None

    def _handle_search_retry(self, results: List[Dict]) -> Optional[List[Dict]]:
        """Handle search retry - UI logic"""
        print(f"{Fore.YELLOW}Search options:{Style.RESET_ALL}")
        print("1. Enter custom search query")
        print("2. Enter title only")
        print("3. Enter author only")

        search_choice = input(
            f"{Fore.CYAN}Choose search option (1-3): {Style.RESET_ALL}"
        ).strip()

        if search_choice == "1":
            custom_query = input("Enter custom search query: ").strip()
            if custom_query:
                return self.search_audible(custom_query)
        elif search_choice == "2":
            title_only = input("Enter book title: ").strip()
            if title_only:
                return self.search_audible(title_only)
        elif search_choice == "3":
            author_only = input("Enter author name: ").strip()
            if author_only:
                return self.search_audible(author_only)

        print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
        return results

    def _get_user_selection(self, results: List[Dict]) -> Optional[Dict]:
        """Get user selection from search results - UI logic"""
        # Display search results
        print(f"\n{Fore.CYAN}📖 Search Results:{Style.RESET_ALL}")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']} by {result['author']}")
            if result.get("series"):
                print(f"   Series: {result['series']}")
            if result.get("narrator"):
                print(f"   Narrated by: {result['narrator']}")

        # Get user selection with option to search again
        while True:
            try:
                choice = input(
                    f"\nSelect book (1-{len(results)}) or 's' to skip, 'r' to search again, 'c' for custom search: "
                ).strip()
                if choice.lower() == "s":
                    return None
                elif choice.lower() == "r":
                    new_results = self._handle_search_retry(results)
                    if new_results is None or not new_results:
                        print(
                            f"{Fore.RED}No results found. Skipping file.{Style.RESET_ALL}"
                        )
                        return None

                    # Display new results
                    print(f"\n{Fore.CYAN}📖 New Search Results:{Style.RESET_ALL}")
                    for i, result in enumerate(new_results, 1):
                        print(f"{i}. {result['title']} by {result['author']}")
                        if result.get("series"):
                            print(f"   Series: {result['series']}")
                        if result.get("narrator"):
                            print(f"   Narrated by: {result['narrator']}")
                    results = new_results
                    continue
                elif choice.lower() == "c":
                    custom_query = input("Enter custom search query: ").strip()
                    if custom_query:
                        new_results = self.search_audible(custom_query)
                        if new_results:
                            # Display new results
                            print(
                                f"\n{Fore.CYAN}📖 Custom Search Results:{Style.RESET_ALL}"
                            )
                            for i, result in enumerate(new_results, 1):
                                print(f"{i}. {result['title']} by {result['author']}")
                                if result.get("series"):
                                    print(f"   Series: {result['series']}")
                                if result.get("narrator"):
                                    print(f"   Narrated by: {result['narrator']}")
                            results = new_results
                            continue
                        else:
                            print(
                                f"{Fore.RED}No results found for custom search.{Style.RESET_ALL}"
                            )
                            continue
                    else:
                        print(
                            f"{Fore.RED}Empty search query. Please try again.{Style.RESET_ALL}"
                        )
                        continue

                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(results):
                    return results[choice_idx]
                else:
                    print(
                        f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}"
                    )
            except ValueError:
                print(
                    f"{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}"
                )

    def _process_file_core(self, file_path: Path, selected_result: Dict) -> bool:
        """Core file processing logic without UI dependencies"""
        try:
            # Get detailed book information
            book_data = self.get_book_details(
                selected_result["asin"], selected_result.get("locale", "com")
            )
            if not book_data:
                self.logger.error(
                    f"Failed to get book details for ASIN: {selected_result['asin']}"
                )
                return False

            # Download cover
            cover_path = None
            if book_data.get("cover_url"):
                cover_path = self.download_cover(
                    book_data["cover_url"], book_data["asin"]
                )

            # Tag the file
            if self.tag_file(file_path, book_data, cover_path):
                # Move to library
                self.move_to_library(file_path, book_data, cover_path)
                return True
            else:
                self.logger.error(f"Failed to tag file: {file_path}")
                return False

        except Exception as e:
            self.logger.error(f"Error in core processing for {file_path}: {e}")
            import traceback

            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def process_file(self, file_path: Path) -> bool:
        """Process a single .m4b file with UI interaction"""
        try:
            # Parse filename
            title, author = self.parse_filename(file_path.name)

            # Build search query - exclude "Unknown Author" from search and clean up common words
            if author == "Unknown Author":
                search_query = title.strip()
            else:
                # Remove common words like "by" from the search query
                search_query = f"{title} {author}".strip()
                # Remove "by" and other common words that might interfere with search
                search_query = re.sub(
                    r"\b(by|the|and|or|in|on|at|to|for|of|with|from)\b",
                    "",
                    search_query,
                    flags=re.IGNORECASE,
                )
                # Clean up extra whitespace
                search_query = re.sub(r"\s+", " ", search_query).strip()

            print(f"\n{Fore.GREEN}🔍 Processing: {file_path.name}{Style.RESET_ALL}")
            print(f"Parsed as: {title} {author}")
            print(f'Search string: "{search_query}"')

            # Search Audible
            results = self.search_audible(search_query)

            # Handle no results case
            if not results:
                results = self._handle_no_search_results(search_query)
                if not results:
                    return False

            # Get user selection
            selected = self._get_user_selection(results)
            if not selected:
                return False

            # Display book information
            self.display_book_info(selected)

            # Process the file using core logic
            success = self._process_file_core(file_path, selected)

            if success:
                print(
                    f"{Fore.GREEN}✅ Successfully processed: {file_path.name}{Style.RESET_ALL}"
                )
            else:
                print(
                    f"{Fore.RED}❌ Failed to process: {file_path.name}{Style.RESET_ALL}"
                )

            return success

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
            print(
                f"{Fore.YELLOW}No .m4b files found in {self.incoming_dir}{Style.RESET_ALL}"
            )
            return

        print(f"{Fore.GREEN}Found {len(m4b_files)} .m4b file(s){Style.RESET_ALL}")

        # Process each file
        processed = 0
        for file_path in tqdm(m4b_files, desc="Processing files"):
            if self.process_file_with_auto_fallback(file_path):
                processed += 1

        print(f"\n{Fore.GREEN}🎉 Processing complete!{Style.RESET_ALL}")
        print(f"Successfully processed: {processed}/{len(m4b_files)} files")
        print(f"Check the library directory for organized files.")

    def extract_asin_from_file(self, file_path: Path) -> Optional[str]:
        """Extract ASIN from existing tags in an M4B file"""
        try:
            audio = MP4(file_path)
            if not audio.tags:
                return None

            # Check for ASIN in various possible tag locations
            asin_candidates = [
                TagConstants.ASIN,  # Primary ASIN tag
                TagConstants.AUDIBLE_ASIN,  # Audible ASIN tag
                TagConstants.SIMPLE_ASIN,  # Simple ASIN tag
                TagConstants.CDEK_ASIN,  # Alternative ASIN tag
            ]

            for tag_name in asin_candidates:
                if tag_name in audio.tags:
                    asin_value = audio.tags[tag_name]
                    if isinstance(asin_value, list) and len(asin_value) > 0:
                        # Handle MP4FreeForm objects
                        if hasattr(asin_value[0], "decode"):
                            asin = asin_value[0].decode("utf-8", errors="replace")
                        else:
                            asin = str(asin_value[0])

                        # Clean up the ASIN value
                        asin = asin.strip()
                        if (
                            asin and len(asin) >= 10
                        ):  # ASINs are typically 10 characters
                            self.logger.info(f"Found ASIN in {file_path.name}: {asin}")
                            return asin

            return None

        except Exception as e:
            self.logger.warning(f"Error extracting ASIN from {file_path}: {e}")
            return None

    def auto_process_file(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """Automatically process a file if it has an ASIN tag. Returns (success, asin)"""
        try:
            # Extract ASIN from existing tags
            asin = self.extract_asin_from_file(file_path)
            if not asin:
                return False, None

            self.logger.info(f"Auto-processing {file_path.name} with ASIN: {asin}")

            # Get book details using the ASIN
            book_data = self.get_book_details(
                asin, self.config.get("preferred_locale", "com")
            )
            if not book_data:
                self.logger.error(f"Failed to get book details for ASIN: {asin}")
                return False, None

            # Download cover
            cover_path = None
            if book_data.get("cover_url"):
                cover_path = self.download_cover(
                    book_data["cover_url"], book_data["asin"]
                )

            # Tag the file
            if self.tag_file(file_path, book_data, cover_path):
                # Move to library
                self.move_to_library(file_path, book_data, cover_path)
                self.logger.info(f"Successfully auto-processed: {file_path.name}")
                return True, asin
            else:
                self.logger.error(
                    f"Failed to tag file during auto-processing: {file_path}"
                )
                return False, None

        except Exception as e:
            self.logger.error(f"Error in auto-processing for {file_path}: {e}")
            import traceback

            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return False, None

    def process_file_with_auto_fallback(self, file_path: Path) -> bool:
        """Process a file with auto-tagging fallback - try auto first, then interactive if no ASIN"""
        # First try auto-processing
        if self.config.get("auto_tag_enabled", False):
            success, _ = self.auto_process_file(file_path)
            if success:
                return True
            else:
                self.logger.info(
                    f"Auto-processing failed for {file_path.name}, falling back to interactive mode"
                )

        # Fall back to interactive processing
        return self.process_file(file_path)


if __name__ == "__main__":
    tagger = AudibleTagger()
    tagger.run()
