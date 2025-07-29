#!/usr/bin/env python3
"""
Test script for translations
"""

from translations import get_text, get_supported_languages

def test_translations():
    """Test that all translations work correctly"""
    print("🌍 Testing translations...")
    
    # Test supported languages
    languages = get_supported_languages()
    print(f"Supported languages: {', '.join(languages)}")
    
    # Test some key translations
    test_keys = [
        'welcome_title',
        'list_no_books',
        'search_no_results',
        'processing_start',
        'error_generic'
    ]
    
    for key in test_keys:
        print(f"\nTesting key: {key}")
        for lang in languages:
            try:
                text = get_text(key, lang)
                print(f"  {lang}: {text[:50]}{'...' if len(text) > 50 else ''}")
            except Exception as e:
                print(f"  {lang}: ERROR - {e}")
    
    # Test formatting
    print(f"\nTesting formatting:")
    for lang in languages:
        try:
            formatted = get_text('list_found_books', lang, 5)
            print(f"  {lang}: {formatted}")
        except Exception as e:
            print(f"  {lang}: ERROR - {e}")
    
    print("\n✅ Translation test completed!")

if __name__ == "__main__":
    test_translations() 