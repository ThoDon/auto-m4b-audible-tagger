#!/usr/bin/env python3
"""
Translations for the Telegram Bot
Supports French, English, Spanish, Italian, and German
"""

TRANSLATIONS = {
    "en": {
        # Welcome messages
        "welcome_title": "🎧 Audiobook Processor Bot",
        "welcome_commands": "Available commands:",
        "welcome_list": "/list - List pending audiobooks",
        "welcome_getnewreleases": "/getnewreleases - Trigger new releases workflow",
        "welcome_help": "The bot will help you manage your audiobook processing workflow!",
        "welcome_buttons": "Use the buttons in the list to search, process, or skip audiobooks.",
        # List command
        "list_no_books": "📚 No pending audiobooks found.",
        "list_found_books": "📚 Found {} pending audiobook(s):",
        "list_book_entry": "{}. **{}** by {}",
        "list_file_info": "   📁 `{}`",
        "list_id_info": "   🆔 ID: `{}`",
        "list_error": "❌ Error: {}",
        # Search results
        "search_no_results": "❌ No search results found for `{}`",
        "search_query_used": "Query used: `{}`",
        "search_try_custom": "🔍 Try a custom search with different terms:",
        "search_results_title": "🔍 Search results for `{}`:",
        "search_query": "Query: {}",
        "search_result_entry": "{}. **{}** by {}",
        "search_narrated_by": "   Narrated by: {}",
        "search_series": "   Series: {}",
        "search_asin": "   ASIN: `{}`",
        "search_custom_option": "🔍 Custom Search",
        "search_select_option": "✅ Select {}",
        # Custom search
        "custom_search_title": "🔍 Custom Search for file ID: `{}`",
        "custom_search_original": "Original search: `{}`",
        "custom_search_instructions": "Please type your search terms below.",
        "custom_search_examples": "Examples:",
        "custom_search_book_title": "• Book title only",
        "custom_search_author": "• Author name",
        "custom_search_title_author": "• Title + Author",
        "custom_search_series": "• Series name",
        "custom_search_spelling": "• Different spelling",
        "custom_search_type_now": "Type your search query now:",
        "custom_search_processing": "🔍 Searching for: `{}`...",
        "custom_search_no_results": "❌ No results found for: `{}`",
        "custom_search_try_different": "Try different search terms or check the spelling.",
        "custom_search_results_title": "🔍 Custom search results for `{}`:",
        # Processing
        "processing_start": "⏳ Processing audiobook... Please wait.",
        "processing_success": "✅ Successfully processed: {}",
        "processing_metadata": "📚 Metadata:",
        "processing_title": "• Title: {}",
        "processing_author": "• Author: {}",
        "processing_narrator": "• Narrator: {}",
        "processing_series": "• Series: {}",
        "processing_series_part": " #{}",
        "processing_standalone": "Standalone",
        "processing_moved_to": "📁 Moved to: {}",
        "processing_error": "❌ Error: {}",
        # Skip
        "skip_success": "⏭️ Skipped: {}",
        "skip_moved_to": "Moved to: {}",
        # Get new releases
        "getnewreleases_not_configured": "❌ New releases webhook not configured",
        "getnewreleases_success": "✅ New releases workflow triggered successfully!",
        "getnewreleases_failed": "❌ Workflow trigger failed (HTTP {})",
        "getnewreleases_timeout": "⏰ Workflow trigger timed out",
        "getnewreleases_connection_error": "🔌 Connection error - check if n8n is running",
        # Errors
        "error_generic": "❌ Error: {}",
        "error_debug_info": "Debug info: {}",
        "error_unknown": "Unknown error",
        "error_please_provide_query": "❌ Please provide a search query.",
        # Buttons
        "button_search": "🔍 Search {}",
        "button_skip": "⏭️ Skip {}",
        "button_process": "✅ Process {}",
        # Language
        "language_name": "{}",
        # Bot Commands
        "cmd_start": "🚀 Start the bot and see available commands",
        "cmd_list": "📚 List pending audiobooks",
        "cmd_language": "🌍 Change bot language",
        "cmd_getnewreleases": "🆕 Trigger new releases workflow",
        # Auto processing
        "auto_start": "🤖 Starting batch auto-processing...",
        "auto_processing_file": "🔄 Processing: {}",
        "auto_complete": "🤖 **Batch Auto-Processing Complete**",
        "auto_results": "📊 **Results:**",
        "auto_processed": "✅ Processed: {}",
        "auto_failed": "❌ Failed: {}",
        "auto_skipped": "⏭️ Skipped: {}",
        "auto_total": "📁 Total: {}",
        "auto_success_message": "🎉 Successfully auto-processed audiobooks with ASIN tags!",
        "auto_failed_message": "⚠️ Some files failed (no ASIN tags found)",
        "auto_skipped_message": "⏭️ Some files were skipped (no longer exist)",
        "auto_failed_files": "**Failed Files:**",
        "auto_processed_files": "**Processed Files:**",
        "auto_failed_file_entry": "• {} - {}",
        "auto_error": "❌ Auto-processing failed: {}",
    },
    "fr": {
        # Welcome messages
        "welcome_title": "🎧 Bot de Traitement d'Audiobooks",
        "welcome_commands": "Commandes disponibles :",
        "welcome_list": "/list - Lister les audiobooks en attente",
        "welcome_getnewreleases": "/getnewreleases - Déclencher le workflow des nouvelles sorties",
        "welcome_help": "Le bot vous aidera à gérer votre workflow de traitement d'audiobooks !",
        "welcome_buttons": "Utilisez les boutons dans la liste pour rechercher, traiter ou ignorer les audiobooks.",
        # List command
        "list_no_books": "📚 Aucun audiobook en attente trouvé.",
        "list_found_books": "📚 {} audiobook(s) en attente trouvé(s) :",
        "list_book_entry": "{}. **{}** par {}",
        "list_file_info": "   📁 `{}`",
        "list_id_info": "   🆔 ID : `{}`",
        "list_error": "❌ Erreur : {}",
        # Search results
        "search_no_results": "❌ Aucun résultat de recherche trouvé pour `{}`",
        "search_query_used": "Requête utilisée : `{}`",
        "search_try_custom": "🔍 Essayez une recherche personnalisée avec des termes différents :",
        "search_results_title": "🔍 Résultats de recherche pour `{}` :",
        "search_query": "Requête : {}",
        "search_result_entry": "{}. **{}** par {}",
        "search_narrated_by": "   Narré par : {}",
        "search_series": "   Série : {}",
        "search_asin": "   ASIN : `{}`",
        "search_custom_option": "🔍 Recherche Personnalisée",
        "search_select_option": "✅ Sélectionner {}",
        # Custom search
        "custom_search_title": "🔍 Recherche Personnalisée pour l'ID de fichier : `{}`",
        "custom_search_original": "Recherche originale : `{}`",
        "custom_search_instructions": "Veuillez taper vos termes de recherche ci-dessous.",
        "custom_search_examples": "Exemples :",
        "custom_search_book_title": "• Titre du livre uniquement",
        "custom_search_author": "• Nom de l'auteur",
        "custom_search_title_author": "• Titre + Auteur",
        "custom_search_series": "• Nom de la série",
        "custom_search_spelling": "• Orthographe différente",
        "custom_search_type_now": "Tapez votre requête de recherche maintenant :",
        "custom_search_processing": "🔍 Recherche pour : `{}`...",
        "custom_search_no_results": "❌ Aucun résultat trouvé pour : `{}`",
        "custom_search_try_different": "Essayez des termes de recherche différents ou vérifiez l'orthographe.",
        "custom_search_results_title": "🔍 Résultats de recherche personnalisée pour `{}` :",
        # Processing
        "processing_start": "⏳ Traitement de l'audiobook... Veuillez patienter.",
        "processing_success": "✅ Traité avec succès : {}",
        "processing_metadata": "📚 Métadonnées :",
        "processing_title": "• Titre : {}",
        "processing_author": "• Auteur : {}",
        "processing_narrator": "• Narrateur : {}",
        "processing_series": "• Série : {}",
        "processing_series_part": " #{}",
        "processing_standalone": "Autonome",
        "processing_moved_to": "📁 Déplacé vers : {}",
        "processing_error": "❌ Erreur : {}",
        # Skip
        "skip_success": "⏭️ Ignoré : {}",
        "skip_moved_to": "Déplacé vers : {}",
        # Get new releases
        "getnewreleases_not_configured": "❌ Webhook des nouvelles sorties non configuré",
        "getnewreleases_success": "✅ Workflow des nouvelles sorties déclenché avec succès !",
        "getnewreleases_failed": "❌ Échec du déclenchement du workflow (HTTP {})",
        "getnewreleases_timeout": "⏰ Déclenchement du workflow expiré",
        "getnewreleases_connection_error": "🔌 Erreur de connexion - vérifiez si n8n fonctionne",
        # Errors
        "error_generic": "❌ Erreur : {}",
        "error_debug_info": "Info de débogage : {}",
        "error_unknown": "Erreur inconnue",
        "error_please_provide_query": "❌ Veuillez fournir une requête de recherche.",
        # Buttons
        "button_search": "🔍 Rechercher {}",
        "button_skip": "⏭️ Ignorer {}",
        "button_process": "✅ Traiter {}",
        # Language
        "language_name": "{}",
        # Bot Commands
        "cmd_start": "🚀 Démarrer le bot et voir les commandes disponibles",
        "cmd_list": "📚 Lister les audiobooks en attente",
        "cmd_language": "🌍 Changer la langue du bot",
        "cmd_getnewreleases": "🆕 Déclencher le workflow des nouvelles sorties",
        # Auto processing
        "auto_start": "🤖 Démarrage du traitement automatique par lot...",
        "auto_processing_file": "🔄 Traitement : {}",
        "auto_complete": "🤖 **Traitement Automatique par Lot Terminé**",
        "auto_results": "📊 **Résultats :**",
        "auto_processed": "✅ Traités : {}",
        "auto_failed": "❌ Échoués : {}",
        "auto_skipped": "⏭️ Ignorés : {}",
        "auto_total": "📁 Total : {}",
        "auto_success_message": "🎉 Audiobooks avec étiquettes ASIN traités automatiquement avec succès !",
        "auto_failed_message": "⚠️ Certains fichiers ont échoué (aucune étiquette ASIN trouvée)",
        "auto_skipped_message": "⏭️ Certains fichiers ont été ignorés (n'existent plus)",
        "auto_failed_files": "**Fichiers Échoués :**",
        "auto_processed_files": "**Fichiers Traités :**",
        "auto_failed_file_entry": "• {} - {}",
        "auto_error": "❌ Le traitement automatique a échoué : {}",
    },
    "es": {
        # Welcome messages
        "welcome_title": "🎧 Bot de Procesamiento de Audiolibros",
        "welcome_commands": "Comandos disponibles:",
        "welcome_list": "/list - Listar audiolibros pendientes",
        "welcome_getnewreleases": "/getnewreleases - Activar flujo de trabajo de nuevos lanzamientos",
        "welcome_help": "¡El bot te ayudará a gestionar tu flujo de trabajo de procesamiento de audiolibros!",
        "welcome_buttons": "Usa los botones en la lista para buscar, procesar o saltar audiolibros.",
        # List command
        "list_no_books": "📚 No se encontraron audiolibros pendientes.",
        "list_found_books": "📚 Se encontraron {} audiolibro(s) pendiente(s):",
        "list_book_entry": "{}. **{}** por {}",
        "list_file_info": "   📁 `{}`",
        "list_id_info": "   🆔 ID: `{}`",
        "list_error": "❌ Error: {}",
        # Search results
        "search_no_results": "❌ No se encontraron resultados de búsqueda para `{}`",
        "search_query_used": "Consulta utilizada: `{}`",
        "search_try_custom": "🔍 Intenta una búsqueda personalizada con términos diferentes:",
        "search_results_title": "🔍 Resultados de búsqueda para `{}`:",
        "search_query": "Consulta: {}",
        "search_result_entry": "{}. **{}** por {}",
        "search_narrated_by": "   Narrado por: {}",
        "search_series": "   Serie: {}",
        "search_asin": "   ASIN: `{}`",
        "search_custom_option": "🔍 Búsqueda Personalizada",
        "search_select_option": "✅ Seleccionar {}",
        # Custom search
        "custom_search_title": "🔍 Búsqueda Personalizada para ID de archivo: `{}`",
        "custom_search_original": "Búsqueda original: `{}`",
        "custom_search_instructions": "Por favor, escribe tus términos de búsqueda a continuación.",
        "custom_search_examples": "Ejemplos:",
        "custom_search_book_title": "• Solo título del libro",
        "custom_search_author": "• Nombre del autor",
        "custom_search_title_author": "• Título + Autor",
        "custom_search_series": "• Nombre de la serie",
        "custom_search_spelling": "• Ortografía diferente",
        "custom_search_type_now": "Escribe tu consulta de búsqueda ahora:",
        "custom_search_processing": "🔍 Buscando: `{}`...",
        "custom_search_no_results": "❌ No se encontraron resultados para: `{}`",
        "custom_search_try_different": "Intenta términos de búsqueda diferentes o verifica la ortografía.",
        "custom_search_results_title": "🔍 Resultados de búsqueda personalizada para `{}`:",
        # Processing
        "processing_start": "⏳ Procesando audiolibro... Por favor espera.",
        "processing_success": "✅ Procesado exitosamente: {}",
        "processing_metadata": "📚 Metadatos:",
        "processing_title": "• Título: {}",
        "processing_author": "• Autor: {}",
        "processing_narrator": "• Narrador: {}",
        "processing_series": "• Serie: {}",
        "processing_series_part": " #{}",
        "processing_standalone": "Independiente",
        "processing_moved_to": "📁 Movido a: {}",
        "processing_error": "❌ Error: {}",
        # Skip
        "skip_success": "⏭️ Saltado: {}",
        "skip_moved_to": "Movido a: {}",
        # Get new releases
        "getnewreleases_not_configured": "❌ Webhook de nuevos lanzamientos no configurado",
        "getnewreleases_success": "✅ ¡Flujo de trabajo de nuevos lanzamientos activado exitosamente!",
        "getnewreleases_failed": "❌ Fallo en la activación del flujo de trabajo (HTTP {})",
        "getnewreleases_timeout": "⏰ Activación del flujo de trabajo agotada",
        "getnewreleases_connection_error": "🔌 Error de conexión - verifica si n8n está funcionando",
        # Errors
        "error_generic": "❌ Error: {}",
        "error_debug_info": "Info de depuración: {}",
        "error_unknown": "Error desconocido",
        "error_please_provide_query": "❌ Por favor proporciona una consulta de búsqueda.",
        # Buttons
        "button_search": "🔍 Buscar {}",
        "button_skip": "⏭️ Saltar {}",
        "button_process": "✅ Procesar {}",
        # Language
        "language_name": "{}",
        # Bot Commands
        "cmd_start": "🚀 Iniciar el bot y ver comandos disponibles",
        "cmd_list": "📚 Listar audiolibros pendientes",
        "cmd_language": "🌍 Cambiar idioma del bot",
        "cmd_getnewreleases": "🆕 Activar flujo de trabajo de nuevas publicaciones",
        # Auto processing
        "auto_start": "🤖 Iniciando procesamiento automático por lotes...",
        "auto_processing_file": "🔄 Procesando: {}",
        "auto_complete": "🤖 **Procesamiento Automático por Lotes Completado**",
        "auto_results": "📊 **Resultados:**",
        "auto_processed": "✅ Procesados: {}",
        "auto_failed": "❌ Fallidos: {}",
        "auto_skipped": "⏭️ Omitidos: {}",
        "auto_total": "📁 Total: {}",
        "auto_success_message": "🎉 ¡Audiolibros con etiquetas ASIN procesados automáticamente con éxito!",
        "auto_failed_message": "⚠️ Algunos archivos fallaron (no se encontraron etiquetas ASIN)",
        "auto_skipped_message": "⏭️ Algunos archivos fueron omitidos (ya no existen)",
        "auto_failed_files": "**Archivos Fallidos:**",
        "auto_processed_files": "**Archivos Procesados:**",
        "auto_failed_file_entry": "• {} - {}",
        "auto_error": "❌ El procesamiento automático falló: {}",
    },
    "it": {
        # Welcome messages
        "welcome_title": "🎧 Bot di Elaborazione Audiolibri",
        "welcome_commands": "Comandi disponibili:",
        "welcome_list": "/list - Elenca audiolibri in attesa",
        "welcome_getnewreleases": "/getnewreleases - Attiva flusso di lavoro nuove uscite",
        "welcome_help": "Il bot ti aiuterà a gestire il tuo flusso di lavoro di elaborazione audiolibri!",
        "welcome_buttons": "Usa i pulsanti nella lista per cercare, elaborare o saltare audiolibri.",
        # List command
        "list_no_books": "📚 Nessun audiolibro in attesa trovato.",
        "list_found_books": "📚 Trovati {} audiolibro/i in attesa:",
        "list_book_entry": "{}. **{}** di {}",
        "list_file_info": "   📁 `{}`",
        "list_id_info": "   🆔 ID: `{}`",
        "list_error": "❌ Errore: {}",
        # Search results
        "search_no_results": "❌ Nessun risultato di ricerca trovato per `{}`",
        "search_query_used": "Query utilizzata: `{}`",
        "search_try_custom": "🔍 Prova una ricerca personalizzata con termini diversi:",
        "search_results_title": "🔍 Risultati di ricerca per `{}`:",
        "search_query": "Query: {}",
        "search_result_entry": "{}. **{}** di {}",
        "search_narrated_by": "   Narrato da: {}",
        "search_series": "   Serie: {}",
        "search_asin": "   ASIN: `{}`",
        "search_custom_option": "🔍 Ricerca Personalizzata",
        "search_select_option": "✅ Seleziona {}",
        # Custom search
        "custom_search_title": "🔍 Ricerca Personalizzata per ID file: `{}`",
        "custom_search_original": "Ricerca originale: `{}`",
        "custom_search_instructions": "Per favore digita i tuoi termini di ricerca qui sotto.",
        "custom_search_examples": "Esempi:",
        "custom_search_book_title": "• Solo titolo del libro",
        "custom_search_author": "• Nome dell'autore",
        "custom_search_title_author": "• Titolo + Autore",
        "custom_search_series": "• Nome della serie",
        "custom_search_spelling": "• Ortografia diversa",
        "custom_search_type_now": "Digita la tua query di ricerca ora:",
        "custom_search_processing": "🔍 Ricerca per: `{}`...",
        "custom_search_no_results": "❌ Nessun risultato trovato per: `{}`",
        "custom_search_try_different": "Prova termini di ricerca diversi o verifica l'ortografia.",
        "custom_search_results_title": "🔍 Risultati di ricerca personalizzata per `{}`:",
        # Processing
        "processing_start": "⏳ Elaborazione audiolibro... Per favore attendi.",
        "processing_success": "✅ Elaborato con successo: {}",
        "processing_metadata": "📚 Metadati:",
        "processing_title": "• Titolo: {}",
        "processing_author": "• Autore: {}",
        "processing_narrator": "• Narratore: {}",
        "processing_series": "• Serie: {}",
        "processing_series_part": " #{}",
        "processing_standalone": "Autonomo",
        "processing_moved_to": "📁 Spostato in: {}",
        "processing_error": "❌ Errore: {}",
        # Skip
        "skip_success": "⏭️ Saltato: {}",
        "skip_moved_to": "Spostato in: {}",
        # Get new releases
        "getnewreleases_not_configured": "❌ Webhook nuove uscite non configurato",
        "getnewreleases_success": "✅ Flusso di lavoro nuove uscite attivato con successo!",
        "getnewreleases_failed": "❌ Fallimento attivazione flusso di lavoro (HTTP {})",
        "getnewreleases_timeout": "⏰ Attivazione flusso di lavoro scaduta",
        "getnewreleases_connection_error": "🔌 Errore di connessione - verifica se n8n è in esecuzione",
        # Errors
        "error_generic": "❌ Errore: {}",
        "error_debug_info": "Info di debug: {}",
        "error_unknown": "Errore sconosciuto",
        "error_please_provide_query": "❌ Per favore fornisci una query di ricerca.",
        # Buttons
        "button_search": "🔍 Cerca {}",
        "button_skip": "⏭️ Salta {}",
        "button_process": "✅ Elabora {}",
        # Language
        "language_name": "{}",
        # Bot Commands
        "cmd_start": "🚀 Avvia il bot e vedi i comandi disponibili",
        "cmd_list": "📚 Elenca audiolibri in attesa",
        "cmd_language": "🌍 Cambia lingua del bot",
        "cmd_getnewreleases": "🆕 Attiva flusso di lavoro nuove uscite",
        # Auto processing
        "auto_start": "🤖 Avvio elaborazione automatica in batch...",
        "auto_processing_file": "🔄 Elaborazione: {}",
        "auto_complete": "🤖 **Elaborazione Automatica in Batch Completata**",
        "auto_results": "📊 **Risultati:**",
        "auto_processed": "✅ Elaborati: {}",
        "auto_failed": "❌ Falliti: {}",
        "auto_skipped": "⏭️ Saltati: {}",
        "auto_total": "📁 Totale: {}",
        "auto_success_message": "🎉 Audiolibri con tag ASIN elaborati automaticamente con successo!",
        "auto_failed_message": "⚠️ Alcuni file sono falliti (nessun tag ASIN trovato)",
        "auto_skipped_message": "⏭️ Alcuni file sono stati saltati (non esistono più)",
        "auto_failed_files": "**File Falliti:**",
        "auto_processed_files": "**File Elaborati:**",
        "auto_failed_file_entry": "• {} - {}",
        "auto_error": "❌ Elaborazione automatica fallita: {}",
    },
    "de": {
        # Welcome messages
        "welcome_title": "🎧 Hörbuch-Verarbeitungs-Bot",
        "welcome_commands": "Verfügbare Befehle:",
        "welcome_list": "/list - Ausstehende Hörbücher auflisten",
        "welcome_getnewreleases": "/getnewreleases - Neue Veröffentlichungen Workflow auslösen",
        "welcome_help": "Der Bot hilft Ihnen bei der Verwaltung Ihres Hörbuch-Verarbeitungs-Workflows!",
        "welcome_buttons": "Verwenden Sie die Schaltflächen in der Liste, um Hörbücher zu suchen, zu verarbeiten oder zu überspringen.",
        # List command
        "list_no_books": "📚 Keine ausstehenden Hörbücher gefunden.",
        "list_found_books": "📚 {} ausstehende(s) Hörbuch(e) gefunden:",
        "list_book_entry": "{}. **{}** von {}",
        "list_file_info": "   📁 `{}`",
        "list_id_info": "   🆔 ID: `{}`",
        "list_error": "❌ Fehler: {}",
        # Search results
        "search_no_results": "❌ Keine Suchergebnisse für `{}` gefunden",
        "search_query_used": "Verwendete Abfrage: `{}`",
        "search_try_custom": "🔍 Versuchen Sie eine benutzerdefinierte Suche mit anderen Begriffen:",
        "search_results_title": "🔍 Suchergebnisse für `{}`:",
        "search_query": "Abfrage: {}",
        "search_result_entry": "{}. **{}** von {}",
        "search_narrated_by": "   Gelesen von: {}",
        "search_series": "   Serie: {}",
        "search_asin": "   ASIN: `{}`",
        "search_custom_option": "🔍 Benutzerdefinierte Suche",
        "search_select_option": "✅ Auswählen {}",
        # Custom search
        "custom_search_title": "🔍 Benutzerdefinierte Suche für Datei-ID: `{}`",
        "custom_search_original": "Ursprüngliche Suche: `{}`",
        "custom_search_instructions": "Bitte geben Sie Ihre Suchbegriffe unten ein.",
        "custom_search_examples": "Beispiele:",
        "custom_search_book_title": "• Nur Buchtitel",
        "custom_search_author": "• Autor-Name",
        "custom_search_title_author": "• Titel + Autor",
        "custom_search_series": "• Serienname",
        "custom_search_spelling": "• Andere Schreibweise",
        "custom_search_type_now": "Geben Sie jetzt Ihre Suchanfrage ein:",
        "custom_search_processing": "🔍 Suche nach: `{}`...",
        "custom_search_no_results": "❌ Keine Ergebnisse für: `{}` gefunden",
        "custom_search_try_different": "Versuchen Sie andere Suchbegriffe oder überprüfen Sie die Schreibweise.",
        "custom_search_results_title": "🔍 Benutzerdefinierte Suchergebnisse für `{}`:",
        # Processing
        "processing_start": "⏳ Hörbuch wird verarbeitet... Bitte warten.",
        "processing_success": "✅ Erfolgreich verarbeitet: {}",
        "processing_metadata": "📚 Metadaten:",
        "processing_title": "• Titel: {}",
        "processing_author": "• Autor: {}",
        "processing_narrator": "• Sprecher: {}",
        "processing_series": "• Serie: {}",
        "processing_series_part": " #{}",
        "processing_standalone": "Einzelband",
        "processing_moved_to": "📁 Verschoben nach: {}",
        "processing_error": "❌ Fehler: {}",
        # Skip
        "skip_success": "⏭️ Übersprungen: {}",
        "skip_moved_to": "Verschoben nach: {}",
        # Get new releases
        "getnewreleases_not_configured": "❌ Neue Veröffentlichungen Webhook nicht konfiguriert",
        "getnewreleases_success": "✅ Neue Veröffentlichungen Workflow erfolgreich ausgelöst!",
        "getnewreleases_failed": "❌ Workflow-Auslösung fehlgeschlagen (HTTP {})",
        "getnewreleases_timeout": "⏰ Workflow-Auslösung abgelaufen",
        "getnewreleases_connection_error": "🔌 Verbindungsfehler - überprüfen Sie, ob n8n läuft",
        # Errors
        "error_generic": "❌ Fehler: {}",
        "error_debug_info": "Debug-Info: {}",
        "error_unknown": "Unbekannter Fehler",
        "error_please_provide_query": "❌ Bitte geben Sie eine Suchanfrage an.",
        # Buttons
        "button_search": "🔍 Suchen {}",
        "button_skip": "⏭️ Überspringen {}",
        "button_process": "✅ Verarbeiten {}",
        # Language
        "language_name": "{}",
        # Bot Commands
        "cmd_start": "🚀 Bot starten und verfügbare Befehle anzeigen",
        "cmd_list": "📚 Ausstehende Hörbücher auflisten",
        "cmd_language": "🌍 Bot-Sprache ändern",
        "cmd_getnewreleases": "🆕 Neue Veröffentlichungen Workflow auslösen",
        # Auto processing
        "auto_start": "🤖 Starte Batch-Autoverarbeitung...",
        "auto_processing_file": "🔄 Verarbeite: {}",
        "auto_complete": "🤖 **Batch-Autoverarbeitung Abgeschlossen**",
        "auto_results": "📊 **Ergebnisse:**",
        "auto_processed": "✅ Verarbeitet: {}",
        "auto_failed": "❌ Fehlgeschlagen: {}",
        "auto_skipped": "⏭️ Übersprungen: {}",
        "auto_total": "📁 Gesamt: {}",
        "auto_success_message": "🎉 Hörbücher mit ASIN-Tags erfolgreich automatisch verarbeitet!",
        "auto_failed_message": "⚠️ Einige Dateien fehlgeschlagen (keine ASIN-Tags gefunden)",
        "auto_skipped_message": "⏭️ Einige Dateien übersprungen (existieren nicht mehr)",
        "auto_failed_files": "**Fehlgeschlagene Dateien:**",
        "auto_processed_files": "**Verarbeitete Dateien:**",
        "auto_failed_file_entry": "• {} - {}",
        "auto_error": "❌ Autoverarbeitung fehlgeschlagen: {}",
    },
}


def get_text(key: str, language: str = "en", *args) -> str:
    """
    Get translated text for a given key and language

    Args:
        key: Translation key
        language: Language code (en, fr, es, it, de)
        *args: Format arguments for the text

    Returns:
        Translated text, or English fallback if translation not found
    """
    # Default to English if language not supported
    if language not in TRANSLATIONS:
        language = "en"

    # Get translation, fallback to English if key not found
    text = TRANSLATIONS.get(language, {}).get(
        key, TRANSLATIONS.get("en", {}).get(key, key)
    )

    # Format with arguments if provided
    if args:
        try:
            return text.format(*args)
        except (IndexError, KeyError):
            return text

    return text


def get_supported_languages() -> list:
    """Get list of supported language codes"""
    return list(TRANSLATIONS.keys())
