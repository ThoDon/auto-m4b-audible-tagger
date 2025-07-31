#!/usr/bin/env python3
"""
REST API Server for Audiobook Processor
Provides API endpoints for automation and integration
"""

import logging
import traceback
import json
from pathlib import Path
from typing import List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

# Import from the same directory
from tagger import AudibleTagger
from database import AudiobookDatabase


class AudiobookAPI:
    """REST API for audiobook processing"""

    def __init__(
        self, input_folder: str, output_folder: str, config_path: str = "config.json"
    ):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for API integration

        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.config_path = Path(config_path)

        # Initialize the tagger
        self.tagger = AudibleTagger()

        # Initialize database
        self.db = AudiobookDatabase()

        # Setup logging
        self.setup_logging()

        # Register routes
        self.register_routes()

        # Run initial cleanup
        self.run_cleanup()

    def setup_logging(self):
        """Setup logging for API server"""
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Use absolute path for log file
        log_file = logs_dir / "api_server.log"

        # Clear any existing handlers to avoid duplicates
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Try to set up file logging, fallback to console only if permission denied
        try:
            # Configure root logger
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
                force=True,  # Force reconfiguration
            )

            # Configure Flask logger to also write to our file
            flask_logger = logging.getLogger("werkzeug")
            flask_logger.setLevel(logging.INFO)

            # Add file handler to Flask logger
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            flask_logger.addHandler(file_handler)

            self.logger = logging.getLogger(__name__)
            self.logger.info(f"API Server logging initialized. Log file: {log_file}")
        except PermissionError:
            # Fallback to console logging only
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[logging.StreamHandler()],
                force=True,
            )
            self.logger = logging.getLogger(__name__)
            self.logger.warning(
                f"Permission denied writing to {log_file}, using console logging only"
            )
        except Exception as e:
            # Fallback to console logging only
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[logging.StreamHandler()],
                force=True,
            )
            self.logger = logging.getLogger(__name__)
            self.logger.error(
                f"Error setting up file logging: {e}, using console logging only"
            )

    def generate_file_id(self, file_path: Path) -> str:
        """Generate a unique ID for a file using UUID based on path"""
        # Create a deterministic UUID based on the file path
        relative_path = str(file_path.relative_to(self.input_folder))
        # Use UUID5 (SHA-1 based) with a namespace for deterministic generation
        namespace = uuid.NAMESPACE_DNS  # Use DNS namespace as a base
        return str(uuid.uuid5(namespace, relative_path))[:8]

    def find_audiobooks(self, folder: Path) -> List[Path]:
        """Find all .m4b files in the given folder and subfolders"""
        audiobooks = []
        if folder.exists():
            # Use rglob to recursively search for .m4b files
            for file_path in folder.rglob("*.m4b"):
                audiobooks.append(file_path)
        return audiobooks

    def run_cleanup(self):
        """Run automatic cleanup of incoming folder"""
        try:
            from cleanup import cleanup_incoming_folder

            temp_files, invalid_files, empty_folders = cleanup_incoming_folder(
                str(self.input_folder), auto_mode=True
            )
            self.logger.info(
                f"🧹 Automatic cleanup completed: {temp_files} temp files, {invalid_files} invalid files, {empty_folders} empty folders removed"
            )
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def update_file_registry(self):
        """Update the file registry with current files using database"""
        audiobooks = self.find_audiobooks(self.input_folder)

        self.logger.info(f"Found {len(audiobooks)} audiobooks")

        for file_path in audiobooks:
            file_id = self.generate_file_id(file_path)
            # Add to database if not already present
            self.db.add_audiobook(file_path, file_id)

        # Clean up old sessions
        self.db.cleanup_old_sessions()

    def get_file_by_id(self, file_id: str) -> Optional[Path]:
        """Get file path by ID from database"""
        audiobook = self.db.get_audiobook(file_id)
        if audiobook and self.db.verify_file_exists(file_id):
            return Path(audiobook["file_path"])
        return None

    def register_routes(self):
        """Register API routes"""

        @self.app.route("/health", methods=["GET"])
        def health_check():
            """Health check endpoint"""
            self.logger.info("Health check requested")
            return jsonify(
                {
                    "status": "healthy",
                    "input_folder": str(self.input_folder),
                    "output_folder": str(self.output_folder),
                    "input_folder_exists": self.input_folder.exists(),
                    "output_folder_exists": self.output_folder.exists(),
                }
            )

        @self.app.route("/audiobooks", methods=["GET"])
        def list_audiobooks():
            """List all untagged audiobooks in the input folder and subfolders"""
            self.logger.info("List audiobooks requested")
            try:
                # Update file registry
                self.update_file_registry()

                # Get all audiobooks from database
                audiobooks = self.db.get_all_audiobooks()

                books_info = []
                for audiobook in audiobooks:
                    file_path = Path(audiobook["file_path"])
                    if file_path.exists():  # Only include files that still exist
                        # Get relative path from input folder
                        relative_path = file_path.relative_to(self.input_folder)
                        title, author = self.tagger.parse_filename(file_path.name)

                        books_info.append(
                            {
                                "id": audiobook["file_id"],
                                "filename": str(
                                    relative_path
                                ),  # Include subfolder path
                                "path": str(file_path),
                                "size": audiobook["file_size"],
                                "status": audiobook["status"],
                                "parsed_title": title,
                                "parsed_author": author,
                                "search_query": (
                                    title
                                    if author == "Unknown Author"
                                    else f"{title} {author}"
                                ),
                                "created_at": audiobook["created_at"],
                                "processed_at": audiobook["processed_at"],
                            }
                        )

                return jsonify(
                    {
                        "status": "success",
                        "count": len(books_info),
                        "audiobooks": books_info,
                    }
                )

            except Exception as e:
                error_details = traceback.format_exc()
                self.logger.error(f"Error listing audiobooks: {e}")
                self.logger.error(f"Full traceback: {error_details}")
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": str(e),
                            "error_type": type(e).__name__,
                            "debug_info": error_details,
                        }
                    ),
                    500,
                )

        @self.app.route("/audiobooks/<file_id>/search", methods=["GET"])
        def search_audiobook(file_id: str):
            """Search for metadata and return results with selection IDs for processing"""
            try:
                # Get file by ID
                file_path = self.get_file_by_id(file_id)
                if not file_path:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"File not found with ID: {file_id}",
                            }
                        ),
                        404,
                    )

                # Parse filename (just the filename, not the full path)
                title, author = self.tagger.parse_filename(file_path.name)

                # Build search query
                if author == "Unknown Author":
                    search_query = title.strip()
                else:
                    search_query = f"{title} {author}".strip()

                # Search Audible
                results = self.tagger.search_audible(search_query)

                # Create selection IDs for each result
                selection_id = str(uuid.uuid4())

                # Store session data in database
                self.db.save_search_session(selection_id, file_id, results)

                # Add selection IDs to results
                results_with_ids = []
                for i, result in enumerate(results):
                    result_with_id = result.copy()
                    result_with_id["selection_id"] = f"{selection_id}_{i}"
                    result_with_id["display_text"] = (
                        f"{result.get('title', 'Unknown')} by {result.get('author', 'Unknown')} ({result.get('narrator', 'Unknown narrator')})"
                    )
                    results_with_ids.append(result_with_id)

                return jsonify(
                    {
                        "status": "success",
                        "file_id": file_id,
                        "filename": str(file_path.relative_to(self.input_folder)),
                        "parsed_title": title,
                        "parsed_author": author,
                        "search_query": search_query,
                        "selection_id": selection_id,
                        "results": results_with_ids,
                        "instructions": "Use the selection_id from any result to process with GET /audiobooks/{file_id}/process?selection_id={selection_id}",
                    }
                )

            except Exception as e:
                error_details = traceback.format_exc()
                self.logger.error(f"Error searching audiobook {file_id}: {e}")
                self.logger.error(f"Full traceback: {error_details}")
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": str(e),
                            "error_type": type(e).__name__,
                            "debug_info": error_details,
                        }
                    ),
                    500,
                )

        @self.app.route("/audiobooks/<file_id>/search/custom", methods=["POST"])
        def custom_search_audiobook(file_id: str):
            """Search for metadata using a custom search query"""
            try:
                # Get file by ID
                file_path = self.get_file_by_id(file_id)
                if not file_path:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"File not found with ID: {file_id}",
                            }
                        ),
                        404,
                    )

                # Get custom search query from request body
                data = request.get_json()
                if not data or "search_query" not in data:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "No search_query provided in request body",
                            }
                        ),
                        400,
                    )

                custom_query = data["search_query"].strip()
                if not custom_query:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "Search query cannot be empty",
                            }
                        ),
                        400,
                    )

                # Search Audible with custom query
                results = self.tagger.search_audible(custom_query)

                # Create selection IDs for each result
                selection_id = str(uuid.uuid4())

                # Store session data in database
                self.db.save_search_session(selection_id, file_id, results)

                # Add selection IDs to results
                results_with_ids = []
                for i, result in enumerate(results):
                    result_with_id = result.copy()
                    result_with_id["selection_id"] = f"{selection_id}_{i}"
                    result_with_id["display_text"] = (
                        f"{result.get('title', 'Unknown')} by {result.get('author', 'Unknown')} ({result.get('narrator', 'Unknown narrator')})"
                    )
                    results_with_ids.append(result_with_id)

                return jsonify(
                    {
                        "status": "success",
                        "file_id": file_id,
                        "filename": str(file_path.relative_to(self.input_folder)),
                        "custom_query": custom_query,
                        "selection_id": selection_id,
                        "results": results_with_ids,
                        "instructions": "Use the selection_id from any result to process with GET /audiobooks/{file_id}/process?selection_id={selection_id}",
                    }
                )

            except Exception as e:
                error_details = traceback.format_exc()
                self.logger.error(
                    f"Error in custom search for audiobook {file_id}: {e}"
                )
                self.logger.error(f"Full traceback: {error_details}")
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": str(e),
                            "error_type": type(e).__name__,
                            "debug_info": error_details,
                        }
                    ),
                    500,
                )

        @self.app.route("/audiobooks/<file_id>/process", methods=["GET"])
        def process_audiobook(file_id: str):
            """Process a specific audiobook using selection ID from search results"""
            try:
                # Get selection ID from URL parameter
                selection_id = request.args.get("selection_id")
                if not selection_id:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "No selection_id provided in URL parameters",
                            }
                        ),
                        400,
                    )

                # Parse selection ID to get session ID and result index
                try:
                    session_id, result_index = selection_id.rsplit("_", 1)
                    result_index = int(result_index)
                except (ValueError, IndexError):
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "Invalid selection_id format",
                            }
                        ),
                        400,
                    )

                # Get session data from database
                session_data = self.db.get_search_session(session_id)
                if not session_data:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "Selection session expired or not found",
                            }
                        ),
                        404,
                    )

                # Verify file ID matches
                if session_data["file_id"] != file_id:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "File ID mismatch with selection session",
                            }
                        ),
                        400,
                    )

                # Get the selected result
                if result_index >= len(session_data["search_results"]):
                    return (
                        jsonify({"status": "error", "message": "Invalid result index"}),
                        400,
                    )

                selected_result = session_data["search_results"][result_index]

                # Find the file
                file_path = self.get_file_by_id(file_id)
                if not file_path or not file_path.exists():
                    return (
                        jsonify(
                            {"status": "error", "message": f"File not found: {file_id}"}
                        ),
                        404,
                    )

                # Update status to processing
                self.db.update_audiobook_status(file_id, "processing")

                # Get detailed book information
                details = self.tagger.get_book_details(
                    selected_result["asin"], selected_result["locale"]
                )

                if not details:
                    self.db.update_audiobook_status(
                        file_id,
                        "error",
                        error_message=f"Could not get details for ASIN: {selected_result['asin']}",
                    )
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f'Could not get details for ASIN: {selected_result["asin"]}',
                            }
                        ),
                        500,
                    )

                # Download cover if available
                cover_path = None
                if details.get("cover_url"):
                    cover_path = self.tagger.download_cover(
                        details["cover_url"], details["asin"]
                    )

                # Tag the file
                try:
                    if not self.tagger.tag_file(file_path, details, cover_path):
                        self.db.update_audiobook_status(
                            file_id, "error", error_message="Failed to tag file"
                        )
                        return (
                            jsonify(
                                {
                                    "status": "error",
                                    "message": f"Failed to tag file: {file_id}",
                                }
                            ),
                            500,
                        )
                except Exception as tag_error:
                    self.logger.error(f"Error tagging file {file_id}: {tag_error}")
                    import traceback

                    self.logger.error(f"Tag error traceback: {traceback.format_exc()}")
                    self.db.update_audiobook_status(
                        file_id, "error", error_message=f"Tag error: {str(tag_error)}"
                    )
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"Error tagging file: {str(tag_error)}",
                                "error_type": type(tag_error).__name__,
                            }
                        ),
                        500,
                    )

                # Move to library
                try:
                    result_path = self.tagger.move_to_library(
                        file_path, details, cover_path
                    )

                    # Update database with success
                    self.db.update_audiobook_status(
                        file_id,
                        "processed",
                        metadata=details,
                        cover_path=cover_path,
                        final_path=str(result_path),
                    )

                    # Run cleanup after successful processing
                    self.run_cleanup()

                    return jsonify(
                        {
                            "status": "success",
                            "message": f"Successfully processed: {file_id}",
                            "original_path": str(file_path),
                            "final_path": str(result_path),
                            "metadata": details,
                            "selected_result": selected_result,
                        }
                    )

                except Exception as e:
                    self.logger.error(f"Error moving file to library: {e}")
                    import traceback

                    self.logger.error(f"Move error traceback: {traceback.format_exc()}")
                    self.db.update_audiobook_status(
                        file_id, "error", error_message=f"Move error: {str(e)}"
                    )
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"Failed to move file to library: {str(e)}",
                                "error_type": type(e).__name__,
                            }
                        ),
                        500,
                    )

            except Exception as e:
                error_details = traceback.format_exc()
                self.logger.error(f"Error processing audiobook {file_id}: {e}")
                self.logger.error(f"Full traceback: {error_details}")
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": str(e),
                            "error_type": type(e).__name__,
                            "debug_info": error_details,
                        }
                    ),
                    500,
                )

        @self.app.route("/audiobooks/auto/batch", methods=["POST"])
        def batch_auto_process_audiobooks():
            """Automatically process all audiobooks that have ASIN tags"""
            try:
                # Get all pending audiobooks
                audiobooks = self.db.get_all_audiobooks(status="pending")
                if not audiobooks:
                    return jsonify(
                        {
                            "status": "success",
                            "message": "No pending audiobooks found",
                            "processed": 0,
                            "failed": 0,
                            "skipped": 0,
                            "results": [],
                        }
                    )

                processed_count = 0
                failed_count = 0
                skipped_count = 0
                results = []

                for audiobook in audiobooks:
                    file_id = audiobook["file_id"]
                    file_path = Path(audiobook["file_path"])

                    if not file_path.exists():
                        # File no longer exists, skip
                        skipped_count += 1
                        results.append(
                            {
                                "file_id": file_id,
                                "filename": audiobook.get("filename", "unknown"),
                                "status": "skipped",
                                "reason": "File no longer exists",
                            }
                        )
                        continue

                    try:
                        # Update status to processing
                        self.db.update_audiobook_status(file_id, "processing")

                        # Try auto-processing
                        success = self.tagger.auto_process_file(file_path)

                        if success:
                            # Get the ASIN that was used for processing
                            asin = self.tagger.extract_asin_from_file(file_path)

                            # Update database with success
                            self.db.update_audiobook_status(
                                file_id,
                                "processed",
                                metadata={"asin": asin, "auto_processed": True},
                                final_path="auto_processed",
                            )

                            processed_count += 1
                            results.append(
                                {
                                    "file_id": file_id,
                                    "filename": audiobook.get("filename", "unknown"),
                                    "status": "processed",
                                    "asin": asin,
                                    "auto_processed": True,
                                }
                            )
                        else:
                            # Auto-processing failed - no ASIN found
                            self.db.update_audiobook_status(
                                file_id,
                                "error",
                                error_message="Auto-processing failed - no ASIN found",
                            )

                            failed_count += 1
                            results.append(
                                {
                                    "file_id": file_id,
                                    "filename": audiobook.get("filename", "unknown"),
                                    "status": "failed",
                                    "reason": "No ASIN found in file tags",
                                }
                            )

                    except Exception as auto_error:
                        self.logger.error(
                            f"Error in auto-processing {file_id}: {auto_error}"
                        )
                        import traceback

                        self.logger.error(
                            f"Auto-processing error traceback: {traceback.format_exc()}"
                        )
                        self.db.update_audiobook_status(
                            file_id,
                            "error",
                            error_message=f"Auto-processing error: {str(auto_error)}",
                        )

                        failed_count += 1
                        results.append(
                            {
                                "file_id": file_id,
                                "filename": audiobook.get("filename", "unknown"),
                                "status": "failed",
                                "reason": str(auto_error),
                                "error_type": type(auto_error).__name__,
                            }
                        )

                # Run cleanup after batch processing
                self.run_cleanup()

                return jsonify(
                    {
                        "status": "success",
                        "message": f"Batch auto-processing completed",
                        "processed": processed_count,
                        "failed": failed_count,
                        "skipped": skipped_count,
                        "total": len(audiobooks),
                        "results": results,
                    }
                )

            except Exception as e:
                error_details = traceback.format_exc()
                self.logger.error(f"Error in batch auto-processing: {e}")
                self.logger.error(f"Full traceback: {error_details}")
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": str(e),
                            "error_type": type(e).__name__,
                            "debug_info": error_details,
                        }
                    ),
                    500,
                )

        @self.app.route("/audiobooks/<file_id>/skip", methods=["POST"])
        def skip_audiobook(file_id: str):
            """Skip processing for a specific audiobook"""
            try:
                # Get file by ID
                file_path = self.get_file_by_id(file_id)
                if not file_path:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"File not found with ID: {file_id}",
                            }
                        ),
                        404,
                    )

                # Create skipped directory outside of input folder
                skipped_dir = Path("/app/skipped")
                skipped_dir.mkdir(exist_ok=True)

                # Move file to skipped directory (preserve subfolder structure)
                relative_path = file_path.relative_to(self.input_folder)
                skipped_path = skipped_dir / relative_path
                # Create parent directories if they don't exist
                skipped_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.rename(skipped_path)

                # Update database status
                self.db.update_audiobook_status(
                    file_id, "skipped", final_path=str(skipped_path)
                )

                # Run cleanup after skipping
                self.run_cleanup()

                return jsonify(
                    {
                        "status": "success",
                        "message": f"Skipped: {file_id}",
                        "moved_to": str(skipped_path),
                    }
                )

            except Exception as e:
                error_details = traceback.format_exc()
                self.logger.error(f"Error skipping audiobook {file_id}: {e}")
                self.logger.error(f"Full traceback: {error_details}")
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": str(e),
                            "error_type": type(e).__name__,
                            "debug_info": error_details,
                        }
                    ),
                    500,
                )

    def run(self, host="0.0.0.0", port=5000, debug=False):
        """Run the API server"""
        self.logger.info(f"Starting API server on {host}:{port}")
        self.logger.info(f"Input folder: {self.input_folder}")
        self.logger.info(f"Output folder: {self.output_folder}")
        self.logger.info(f"Debug mode: {debug}")

        self.app.run(host=host, port=port, debug=debug)


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Audiobook API Server")
    parser.add_argument("input_folder", help="Input folder for audiobooks")
    parser.add_argument("output_folder", help="Output folder for processed audiobooks")
    parser.add_argument(
        "--config", default="config.json", help="Configuration file path"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Create API server
    api = AudiobookAPI(args.input_folder, args.output_folder, args.config)

    # Run server
    api.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
