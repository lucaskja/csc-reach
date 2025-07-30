"""
Translation management utilities for CSC-Reach.
Provides tools for maintainers to manage translations, validate completeness,
and generate translation reports.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime

from ..core.i18n_manager import get_i18n_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TranslationManager:
    """
    Utility class for managing translations and providing tools for maintainers.
    """
    
    def __init__(self):
        """Initialize the translation manager."""
        self.i18n_manager = get_i18n_manager()
        self.translations_dir = self.i18n_manager.translations_dir
    
    def validate_all_translations(self) -> Dict[str, List[str]]:
        """
        Validate all translations for completeness and consistency.
        
        Returns:
            Dictionary with validation results for each language
        """
        results = {}
        
        for lang_code in self.i18n_manager.SUPPORTED_LANGUAGES.keys():
            results[lang_code] = self.validate_language(lang_code)
        
        return results
    
    def validate_language(self, lang_code: str) -> List[str]:
        """
        Validate translations for a specific language.
        
        Args:
            lang_code: Language code to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if lang_code not in self.i18n_manager.SUPPORTED_LANGUAGES:
            issues.append(f"Unsupported language code: {lang_code}")
            return issues
        
        # Get English translations as reference
        english_translations = self.i18n_manager.translations.get('en', {})
        target_translations = self.i18n_manager.translations.get(lang_code, {})
        
        # Check for missing translations
        missing_keys = set(english_translations.keys()) - set(target_translations.keys())
        for key in missing_keys:
            issues.append(f"Missing translation for key: {key}")
        
        # Check for extra translations
        extra_keys = set(target_translations.keys()) - set(english_translations.keys())
        for key in extra_keys:
            issues.append(f"Extra translation key (not in English): {key}")
        
        # Check for empty translations
        for key, value in target_translations.items():
            if not value or (isinstance(value, str) and not value.strip()):
                issues.append(f"Empty translation for key: {key}")
        
        # Check for variable consistency
        for key in english_translations.keys():
            if key in target_translations:
                english_vars = self._extract_variables(english_translations[key])
                target_vars = self._extract_variables(target_translations[key])
                
                if english_vars != target_vars:
                    issues.append(
                        f"Variable mismatch in key '{key}': "
                        f"English has {english_vars}, {lang_code} has {target_vars}"
                    )
        
        return issues
    
    def _extract_variables(self, text: str) -> Set[str]:
        """
        Extract variable names from a translation string.
        
        Args:
            text: Translation text
            
        Returns:
            Set of variable names
        """
        if not isinstance(text, str):
            return set()
        
        return set(re.findall(r'\{(\w+)\}', text))
    
    def generate_translation_report(self) -> Dict[str, any]:
        """
        Generate a comprehensive translation report.
        
        Returns:
            Dictionary with translation statistics and issues
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'languages': {},
            'summary': {
                'total_languages': len(self.i18n_manager.SUPPORTED_LANGUAGES),
                'total_keys': len(self.i18n_manager.translations.get('en', {})),
                'overall_completion': 0.0
            }
        }
        
        english_key_count = len(self.i18n_manager.translations.get('en', {}))
        total_completion = 0.0
        
        for lang_code, lang_info in self.i18n_manager.SUPPORTED_LANGUAGES.items():
            lang_translations = self.i18n_manager.translations.get(lang_code, {})
            missing_keys = self.i18n_manager.get_missing_translations(lang_code)
            validation_issues = self.validate_language(lang_code)
            
            completion_percentage = 0.0
            if english_key_count > 0:
                completion_percentage = ((english_key_count - len(missing_keys)) / english_key_count) * 100
            
            total_completion += completion_percentage
            
            report['languages'][lang_code] = {
                'name': lang_info['name'],
                'native_name': lang_info['native'],
                'total_keys': len(lang_translations),
                'missing_keys': len(missing_keys),
                'missing_key_list': missing_keys,
                'completion_percentage': completion_percentage,
                'validation_issues': validation_issues,
                'issue_count': len(validation_issues),
                'last_updated': self._get_file_last_modified(lang_code)
            }
        
        report['summary']['overall_completion'] = total_completion / len(self.i18n_manager.SUPPORTED_LANGUAGES)
        
        return report
    
    def _get_file_last_modified(self, lang_code: str) -> Optional[str]:
        """
        Get the last modified date of a translation file.
        
        Args:
            lang_code: Language code
            
        Returns:
            ISO format datetime string or None
        """
        try:
            file_path = self.translations_dir / f"{lang_code}.json"
            if file_path.exists():
                timestamp = file_path.stat().st_mtime
                return datetime.fromtimestamp(timestamp).isoformat()
        except Exception as e:
            logger.error(f"Error getting file modification time for {lang_code}: {e}")
        
        return None
    
    def export_missing_translations(self, lang_code: str, output_path: Path) -> bool:
        """
        Export missing translations for a language to a file for translation.
        
        Args:
            lang_code: Language code
            output_path: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if lang_code not in self.i18n_manager.SUPPORTED_LANGUAGES:
                logger.error(f"Unsupported language: {lang_code}")
                return False
            
            missing_keys = self.i18n_manager.get_missing_translations(lang_code)
            english_translations = self.i18n_manager.translations.get('en', {})
            
            export_data = {
                'language': lang_code,
                'language_name': self.i18n_manager.SUPPORTED_LANGUAGES[lang_code]['name'],
                'exported_at': datetime.now().isoformat(),
                'missing_count': len(missing_keys),
                'instructions': {
                    'en': 'Translate the values in the "translations" section to the target language.',
                    'es': 'Traduzca los valores en la sección "translations" al idioma de destino.',
                    'pt': 'Traduza os valores na seção "translations" para o idioma de destino.'
                },
                'translations': {}
            }
            
            # Add missing translations with English text as reference
            for key in sorted(missing_keys):
                export_data['translations'][key] = {
                    'english': english_translations.get(key, ''),
                    'translation': '',  # To be filled by translator
                    'context': self._get_key_context(key),
                    'variables': list(self._extract_variables(english_translations.get(key, '')))
                }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(missing_keys)} missing translations for {lang_code} to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export missing translations for {lang_code}: {e}")
            return False
    
    def import_completed_translations(self, import_path: Path) -> bool:
        """
        Import completed translations from a file.
        
        Args:
            import_path: Path to import file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            lang_code = import_data.get('language')
            if not lang_code or lang_code not in self.i18n_manager.SUPPORTED_LANGUAGES:
                logger.error(f"Invalid language in import file: {lang_code}")
                return False
            
            translations_to_import = import_data.get('translations', {})
            imported_count = 0
            
            for key, translation_data in translations_to_import.items():
                if isinstance(translation_data, dict):
                    translation = translation_data.get('translation', '').strip()
                else:
                    translation = str(translation_data).strip()
                
                if translation:
                    self.i18n_manager.add_translation(lang_code, key, translation)
                    imported_count += 1
            
            logger.info(f"Imported {imported_count} translations for {lang_code}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import translations from {import_path}: {e}")
            return False
    
    def _get_key_context(self, key: str) -> str:
        """
        Get context information for a translation key.
        
        Args:
            key: Translation key
            
        Returns:
            Context description
        """
        # Provide context based on key patterns
        if key.startswith('button.'):
            return 'Button text'
        elif key.startswith('menu.'):
            return 'Menu item'
        elif key.startswith('dialog.'):
            return 'Dialog title or message'
        elif key.startswith('status.'):
            return 'Status message'
        elif key.startswith('error_'):
            return 'Error message'
        elif key.startswith('success_'):
            return 'Success message'
        elif key.startswith('warning_'):
            return 'Warning message'
        elif key.startswith('validation_'):
            return 'Validation error message'
        elif key.startswith('template_'):
            return 'Template management'
        elif key.startswith('csv_'):
            return 'CSV import functionality'
        elif key.startswith('email_'):
            return 'Email functionality'
        elif key.startswith('whatsapp_'):
            return 'WhatsApp functionality'
        elif key.endswith('_one') or key.endswith('_other'):
            return 'Pluralization form'
        else:
            return 'General UI text'
    
    def generate_html_report(self, output_path: Path) -> bool:
        """
        Generate an HTML report of translation status.
        
        Args:
            output_path: Path to save HTML report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            report_data = self.generate_translation_report()
            
            html_content = self._generate_html_content(report_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated HTML translation report: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            return False
    
    def _generate_html_content(self, report_data: Dict) -> str:
        """
        Generate HTML content for the translation report.
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            HTML content string
        """
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSC-Reach Translation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .language {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
        .language-header {{ background-color: #e9e9e9; padding: 15px; font-weight: bold; }}
        .language-content {{ padding: 15px; }}
        .progress-bar {{ width: 100%; height: 20px; background-color: #f0f0f0; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background-color: #4CAF50; transition: width 0.3s; }}
        .issues {{ margin-top: 10px; }}
        .issue {{ color: #d32f2f; margin: 2px 0; }}
        .missing-key {{ color: #ff9800; margin: 2px 0; font-family: monospace; }}
        .stats {{ display: flex; gap: 20px; margin: 10px 0; }}
        .stat {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>CSC-Reach Translation Report</h1>
        <p>Generated on: {report_data['generated_at']}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="stats">
            <div class="stat">
                <strong>Total Languages:</strong> {report_data['summary']['total_languages']}
            </div>
            <div class="stat">
                <strong>Total Keys:</strong> {report_data['summary']['total_keys']}
            </div>
            <div class="stat">
                <strong>Overall Completion:</strong> {report_data['summary']['overall_completion']:.1f}%
            </div>
        </div>
    </div>
"""
        
        for lang_code, lang_data in report_data['languages'].items():
            completion = lang_data['completion_percentage']
            color = '#4CAF50' if completion >= 90 else '#ff9800' if completion >= 70 else '#d32f2f'
            
            html += f"""
    <div class="language">
        <div class="language-header">
            {lang_data['name']} ({lang_data['native_name']}) - {lang_code}
        </div>
        <div class="language-content">
            <div class="stats">
                <div class="stat">
                    <strong>Completion:</strong> {completion:.1f}%
                </div>
                <div class="stat">
                    <strong>Total Keys:</strong> {lang_data['total_keys']}
                </div>
                <div class="stat">
                    <strong>Missing:</strong> {lang_data['missing_keys']}
                </div>
                <div class="stat">
                    <strong>Issues:</strong> {lang_data['issue_count']}
                </div>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" style="width: {completion}%; background-color: {color};"></div>
            </div>
            
            {f'<p><strong>Last Updated:</strong> {lang_data["last_updated"]}</p>' if lang_data.get("last_updated") else ""}
            
            {f'''
            <div class="issues">
                <h4>Missing Keys ({len(lang_data["missing_key_list"])})</h4>
                {"".join(f'<div class="missing-key">{key}</div>' for key in lang_data["missing_key_list"][:10])}
                {f'<p>... and {len(lang_data["missing_key_list"]) - 10} more</p>' if len(lang_data["missing_key_list"]) > 10 else ""}
            </div>
            ''' if lang_data["missing_key_list"] else ""}
            
            {f'''
            <div class="issues">
                <h4>Validation Issues ({len(lang_data["validation_issues"])})</h4>
                {"".join(f'<div class="issue">{issue}</div>' for issue in lang_data["validation_issues"][:10])}
                {f'<p>... and {len(lang_data["validation_issues"]) - 10} more</p>' if len(lang_data["validation_issues"]) > 10 else ""}
            </div>
            ''' if lang_data["validation_issues"] else ""}
        </div>
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html
    
    def sync_translation_keys(self) -> Dict[str, int]:
        """
        Synchronize translation keys across all languages.
        Adds missing keys with empty values for translation.
        
        Returns:
            Dictionary with count of keys added per language
        """
        results = {}
        
        # Get all unique keys from all languages
        all_keys = set()
        for translations in self.i18n_manager.translations.values():
            all_keys.update(translations.keys())
        
        # Add missing keys to each language
        for lang_code in self.i18n_manager.SUPPORTED_LANGUAGES.keys():
            if lang_code not in self.i18n_manager.translations:
                self.i18n_manager.translations[lang_code] = {}
            
            lang_translations = self.i18n_manager.translations[lang_code]
            missing_keys = all_keys - set(lang_translations.keys())
            
            added_count = 0
            for key in missing_keys:
                # Skip comment keys
                if not key.startswith('_comment'):
                    lang_translations[key] = ""
                    added_count += 1
            
            if added_count > 0:
                self.i18n_manager._save_translation_file(lang_code)
            
            results[lang_code] = added_count
        
        return results


# Utility functions for command-line usage
def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CSC-Reach Translation Management Tool')
    parser.add_argument('command', choices=['validate', 'report', 'export-missing', 'import', 'sync'],
                       help='Command to execute')
    parser.add_argument('--language', '-l', help='Language code (for language-specific commands)')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--input', '-i', help='Input file path')
    
    args = parser.parse_args()
    
    manager = TranslationManager()
    
    if args.command == 'validate':
        if args.language:
            issues = manager.validate_language(args.language)
            print(f"Validation issues for {args.language}: {len(issues)}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            results = manager.validate_all_translations()
            for lang, issues in results.items():
                print(f"{lang}: {len(issues)} issues")
    
    elif args.command == 'report':
        if args.output:
            if args.output.endswith('.html'):
                manager.generate_html_report(Path(args.output))
            else:
                report = manager.generate_translation_report()
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
        else:
            report = manager.generate_translation_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))
    
    elif args.command == 'export-missing':
        if not args.language or not args.output:
            print("Error: --language and --output are required for export-missing")
            return
        
        success = manager.export_missing_translations(args.language, Path(args.output))
        print(f"Export {'successful' if success else 'failed'}")
    
    elif args.command == 'import':
        if not args.input:
            print("Error: --input is required for import")
            return
        
        success = manager.import_completed_translations(Path(args.input))
        print(f"Import {'successful' if success else 'failed'}")
    
    elif args.command == 'sync':
        results = manager.sync_translation_keys()
        print("Synchronization results:")
        for lang, count in results.items():
            print(f"  {lang}: {count} keys added")


if __name__ == '__main__':
    main()