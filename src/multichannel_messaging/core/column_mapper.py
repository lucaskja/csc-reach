"""
Intelligent column mapping system with pattern recognition and user-friendly interface.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import difflib

from ..utils.logger import get_logger
from ..utils.exceptions import CSVProcessingError

logger = get_logger(__name__)


class MappingConfidence(Enum):
    """Column mapping confidence levels."""
    EXACT = "exact"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class ColumnMapping:
    """Individual column mapping with confidence and metadata."""
    source_column: str
    target_field: str
    confidence: MappingConfidence
    confidence_score: float
    detection_method: str
    suggestions: List[str] = field(default_factory=list)
    user_confirmed: bool = False
    transformation_rules: List[str] = field(default_factory=list)


@dataclass
class MappingTemplate:
    """Reusable mapping template for similar datasets."""
    name: str
    description: str
    mappings: Dict[str, str]  # field -> column pattern
    patterns: Dict[str, List[str]]  # field -> list of regex patterns
    created_at: str
    usage_count: int = 0
    success_rate: float = 0.0


@dataclass
class MappingResult:
    """Complete column mapping result."""
    mappings: Dict[str, ColumnMapping]
    unmapped_columns: List[str]
    missing_required_fields: List[str]
    confidence_score: float
    suggested_templates: List[MappingTemplate]
    transformation_suggestions: Dict[str, List[str]]


class IntelligentColumnMapper:
    """
    Intelligent column mapping system with machine learning-based pattern recognition.
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the intelligent column mapper.
        
        Args:
            templates_dir: Directory to store mapping templates
        """
        self.templates_dir = templates_dir or Path.home() / '.csc-reach' / 'mapping_templates'
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Enhanced field definitions with patterns and weights
        self.field_definitions = {
            'name': {
                'required': True,
                'weight': 1.0,
                'exact_matches': [
                    'name', 'customer_name', 'full_name', 'client_name', 'contact_name',
                    'nome', 'nombre', 'nom', 'person_name', 'individual_name'
                ],
                'pattern_matches': [
                    r'.*name.*', r'.*cliente.*', r'.*customer.*', r'.*contact.*',
                    r'.*person.*', r'.*individual.*', r'.*full.*name.*'
                ],
                'fuzzy_matches': [
                    'first_name', 'last_name', 'firstname', 'lastname', 'fname', 'lname'
                ],
                'data_patterns': [
                    r'^[A-Za-z\s\-\'\.]{2,50}$',  # Typical name pattern
                    r'^[A-Z][a-z]+\s+[A-Z][a-z]+.*$'  # First Last format
                ],
                'negative_patterns': [
                    r'^\d+$',  # Pure numbers
                    r'^[^@]+@[^@]+\.[^@]+$',  # Email addresses
                    r'^\+?\d[\d\s\-\(\)]{7,}$'  # Phone numbers
                ]
            },
            'company': {
                'required': True,
                'weight': 1.0,
                'exact_matches': [
                    'company', 'company_name', 'organization', 'org', 'business',
                    'empresa', 'compañía', 'société', 'corporation', 'corp'
                ],
                'pattern_matches': [
                    r'.*company.*', r'.*organization.*', r'.*business.*', r'.*corp.*',
                    r'.*empresa.*', r'.*firm.*', r'.*agency.*'
                ],
                'fuzzy_matches': [
                    'employer', 'workplace', 'office'
                ],
                'data_patterns': [
                    r'^[A-Za-z0-9\s\-\&\.\,]{2,100}$',  # Company name pattern
                    r'.*\b(Inc|LLC|Corp|Ltd|Co)\b.*'  # Company suffixes
                ],
                'negative_patterns': [
                    r'^[^@]+@[^@]+\.[^@]+$',  # Email addresses
                    r'^\+?\d[\d\s\-\(\)]{7,}$'  # Phone numbers
                ]
            },
            'email': {
                'required': True,
                'weight': 1.0,
                'exact_matches': [
                    'email', 'email_address', 'e-mail', 'mail', 'correo',
                    'courriel', 'electronic_mail', 'e_mail'
                ],
                'pattern_matches': [
                    r'.*email.*', r'.*mail.*', r'.*@.*', r'.*correo.*'
                ],
                'fuzzy_matches': [
                    'contact_email', 'work_email', 'business_email'
                ],
                'data_patterns': [
                    r'^[^@]+@[^@]+\.[^@]+$',  # Email format
                    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'  # Strict email
                ],
                'negative_patterns': [
                    r'^\d+$',  # Pure numbers
                    r'^[A-Za-z\s\-\'\.]{2,50}$'  # Names
                ]
            },
            'phone': {
                'required': True,
                'weight': 1.0,
                'exact_matches': [
                    'phone', 'telephone', 'mobile', 'cell', 'telefone', 'teléfono',
                    'téléphone', 'phone_number', 'tel', 'cellular'
                ],
                'pattern_matches': [
                    r'.*phone.*', r'.*tel.*', r'.*mobile.*', r'.*cell.*',
                    r'.*contact.*number.*'
                ],
                'fuzzy_matches': [
                    'contact_phone', 'work_phone', 'business_phone', 'home_phone'
                ],
                'data_patterns': [
                    r'^\+?\d[\d\s\-\(\)]{7,}$',  # Phone number pattern
                    r'^\(\d{3}\)\s?\d{3}-?\d{4}$',  # US format
                    r'^\+\d{1,3}\s?\d{4,14}$'  # International format
                ],
                'negative_patterns': [
                    r'^[^@]+@[^@]+\.[^@]+$',  # Email addresses
                    r'^[A-Za-z\s\-\'\.]{2,50}$'  # Names
                ]
            }
        }
        
        # Load existing templates
        self.templates = self._load_templates()
        
        # Pattern learning cache
        self._pattern_cache: Dict[str, List[str]] = {}
    
    def map_columns(
        self, 
        headers: List[str], 
        sample_data: Optional[List[Dict[str, Any]]] = None,
        use_templates: bool = True,
        learn_patterns: bool = True
    ) -> MappingResult:
        """
        Intelligently map CSV columns to required fields.
        
        Args:
            headers: List of column headers
            sample_data: Sample data for pattern analysis
            use_templates: Whether to use existing templates
            learn_patterns: Whether to learn new patterns from data
            
        Returns:
            Complete mapping result with confidence scores
        """
        logger.info(f"Starting intelligent column mapping for {len(headers)} columns")
        
        # Initialize result
        mappings: Dict[str, ColumnMapping] = {}
        unmapped_columns = headers.copy()
        missing_required_fields = []
        
        # Step 1: Try template matching if enabled
        template_mappings = {}
        if use_templates and self.templates:
            template_mappings = self._apply_template_matching(headers, sample_data)
            logger.debug(f"Template matching found {len(template_mappings)} mappings")
        
        # Step 2: Exact matching
        exact_mappings = self._perform_exact_matching(headers)
        logger.debug(f"Exact matching found {len(exact_mappings)} mappings")
        
        # Step 3: Pattern matching
        pattern_mappings = self._perform_pattern_matching(headers)
        logger.debug(f"Pattern matching found {len(pattern_mappings)} mappings")
        
        # Step 4: Fuzzy matching
        fuzzy_mappings = self._perform_fuzzy_matching(headers)
        logger.debug(f"Fuzzy matching found {len(fuzzy_mappings)} mappings")
        
        # Step 5: Data pattern analysis if sample data available
        data_mappings = {}
        if sample_data and learn_patterns:
            data_mappings = self._analyze_data_patterns(headers, sample_data)
            logger.debug(f"Data pattern analysis found {len(data_mappings)} mappings")
        
        # Step 6: Combine and resolve conflicts
        all_mappings = {
            'template': template_mappings,
            'exact': exact_mappings,
            'pattern': pattern_mappings,
            'fuzzy': fuzzy_mappings,
            'data': data_mappings
        }
        
        mappings = self._resolve_mapping_conflicts(all_mappings, headers)
        
        # Step 7: Identify unmapped and missing
        mapped_columns = {mapping.source_column for mapping in mappings.values()}
        unmapped_columns = [col for col in headers if col not in mapped_columns]
        
        mapped_fields = set(mappings.keys())
        required_fields = {field for field, config in self.field_definitions.items() if config['required']}
        missing_required_fields = list(required_fields - mapped_fields)
        
        # Step 8: Calculate overall confidence
        confidence_score = self._calculate_overall_confidence(mappings)
        
        # Step 9: Generate suggestions
        transformation_suggestions = self._generate_transformation_suggestions(mappings, sample_data)
        suggested_templates = self._suggest_similar_templates(mappings)
        
        result = MappingResult(
            mappings=mappings,
            unmapped_columns=unmapped_columns,
            missing_required_fields=missing_required_fields,
            confidence_score=confidence_score,
            suggested_templates=suggested_templates,
            transformation_suggestions=transformation_suggestions
        )
        
        logger.info(f"Column mapping complete: {len(mappings)} mapped, "
                   f"{len(unmapped_columns)} unmapped, "
                   f"{len(missing_required_fields)} missing required, "
                   f"confidence: {confidence_score:.2f}")
        
        return result
    
    def _perform_exact_matching(self, headers: List[str]) -> Dict[str, ColumnMapping]:
        """Perform exact string matching for column headers."""
        mappings = {}
        
        for header in headers:
            header_lower = header.lower().strip()
            
            for field, config in self.field_definitions.items():
                if field in mappings:
                    continue  # Field already mapped
                
                for exact_match in config['exact_matches']:
                    if header_lower == exact_match.lower():
                        mappings[field] = ColumnMapping(
                            source_column=header,
                            target_field=field,
                            confidence=MappingConfidence.EXACT,
                            confidence_score=1.0,
                            detection_method='exact_match'
                        )
                        break
        
        return mappings
    
    def _perform_pattern_matching(self, headers: List[str]) -> Dict[str, ColumnMapping]:
        """Perform regex pattern matching for column headers."""
        mappings = {}
        
        for header in headers:
            header_lower = header.lower().strip()
            
            for field, config in self.field_definitions.items():
                if field in mappings:
                    continue  # Field already mapped
                
                best_score = 0.0
                for pattern in config['pattern_matches']:
                    if re.search(pattern, header_lower):
                        # Score based on pattern specificity
                        score = 0.8 + (len(pattern) / 100.0)  # More specific patterns get higher scores
                        if score > best_score:
                            best_score = score
                
                if best_score > 0.0:
                    confidence = MappingConfidence.HIGH if best_score > 0.85 else MappingConfidence.MEDIUM
                    mappings[field] = ColumnMapping(
                        source_column=header,
                        target_field=field,
                        confidence=confidence,
                        confidence_score=min(0.95, best_score),
                        detection_method='pattern_match'
                    )
        
        return mappings
    
    def _perform_fuzzy_matching(self, headers: List[str]) -> Dict[str, ColumnMapping]:
        """Perform fuzzy string matching for column headers."""
        mappings = {}
        
        for header in headers:
            header_lower = header.lower().strip()
            
            for field, config in self.field_definitions.items():
                if field in mappings:
                    continue  # Field already mapped
                
                best_score = 0.0
                best_match = None
                
                # Check fuzzy matches
                for fuzzy_match in config['fuzzy_matches']:
                    similarity = difflib.SequenceMatcher(None, header_lower, fuzzy_match.lower()).ratio()
                    if similarity > best_score and similarity > 0.7:
                        best_score = similarity
                        best_match = fuzzy_match
                
                # Also check against exact matches with fuzzy logic
                for exact_match in config['exact_matches']:
                    similarity = difflib.SequenceMatcher(None, header_lower, exact_match.lower()).ratio()
                    if similarity > best_score and similarity > 0.7:
                        best_score = similarity
                        best_match = exact_match
                
                if best_score > 0.7:
                    confidence = MappingConfidence.HIGH if best_score > 0.9 else MappingConfidence.MEDIUM
                    mappings[field] = ColumnMapping(
                        source_column=header,
                        target_field=field,
                        confidence=confidence,
                        confidence_score=best_score * 0.9,  # Slight penalty for fuzzy matching
                        detection_method='fuzzy_match',
                        suggestions=[f"Similar to: {best_match}"]
                    )
        
        return mappings
    
    def _analyze_data_patterns(self, headers: List[str], sample_data: List[Dict[str, Any]]) -> Dict[str, ColumnMapping]:
        """Analyze actual data patterns to infer column types."""
        mappings = {}
        
        if not sample_data:
            return mappings
        
        # Analyze each column's data
        column_analysis = {}
        for header in headers:
            values = []
            for row in sample_data:
                value = row.get(header, '')
                if value and str(value).strip():
                    values.append(str(value).strip())
            
            if values:
                column_analysis[header] = self._analyze_column_values(values)
        
        # Match patterns to fields
        for header, analysis in column_analysis.items():
            best_field = None
            best_score = 0.0
            
            for field, config in self.field_definitions.items():
                if field in mappings:
                    continue  # Field already mapped
                
                # Check positive patterns
                positive_score = 0.0
                for pattern in config['data_patterns']:
                    matches = sum(1 for value in analysis['values'] if re.match(pattern, value))
                    if analysis['total_values'] > 0:
                        match_ratio = matches / analysis['total_values']
                        positive_score = max(positive_score, match_ratio)
                
                # Check negative patterns (should NOT match)
                negative_score = 0.0
                for pattern in config['negative_patterns']:
                    matches = sum(1 for value in analysis['values'] if re.match(pattern, value))
                    if analysis['total_values'] > 0:
                        match_ratio = matches / analysis['total_values']
                        negative_score = max(negative_score, match_ratio)
                
                # Combined score (positive patterns good, negative patterns bad)
                combined_score = positive_score - (negative_score * 0.5)
                
                if combined_score > best_score and combined_score > 0.6:
                    best_score = combined_score
                    best_field = field
            
            if best_field and best_score > 0.6:
                confidence = MappingConfidence.HIGH if best_score > 0.8 else MappingConfidence.MEDIUM
                mappings[best_field] = ColumnMapping(
                    source_column=header,
                    target_field=best_field,
                    confidence=confidence,
                    confidence_score=best_score,
                    detection_method='data_pattern',
                    suggestions=[f"Based on data pattern analysis ({best_score:.2f} confidence)"]
                )
        
        return mappings
    
    def _analyze_column_values(self, values: List[str]) -> Dict[str, Any]:
        """Analyze a column's values to determine patterns."""
        analysis = {
            'values': values,
            'total_values': len(values),
            'unique_values': len(set(values)),
            'avg_length': sum(len(v) for v in values) / len(values) if values else 0,
            'patterns': {}
        }
        
        # Common pattern checks
        patterns = {
            'email': r'^[^@]+@[^@]+\.[^@]+$',
            'phone': r'^\+?\d[\d\s\-\(\)]{7,}$',
            'name': r'^[A-Za-z\s\-\'\.]{2,50}$',
            'numeric': r'^\d+$',
            'alphanumeric': r'^[A-Za-z0-9\s]+$'
        }
        
        for pattern_name, pattern in patterns.items():
            matches = sum(1 for value in values if re.match(pattern, value))
            analysis['patterns'][pattern_name] = matches / len(values) if values else 0
        
        return analysis
    
    def _apply_template_matching(self, headers: List[str], sample_data: Optional[List[Dict[str, Any]]]) -> Dict[str, ColumnMapping]:
        """Apply existing mapping templates to headers."""
        mappings = {}
        
        if not self.templates:
            return mappings
        
        # Score each template against the headers
        template_scores = []
        for template in self.templates:
            score = self._score_template_match(template, headers, sample_data)
            if score > 0.5:  # Minimum threshold for template consideration
                template_scores.append((template, score))
        
        # Use the best matching template
        if template_scores:
            best_template, best_score = max(template_scores, key=lambda x: x[1])
            logger.debug(f"Using template '{best_template.name}' with score {best_score:.2f}")
            
            # Apply template mappings
            for field, column_pattern in best_template.mappings.items():
                # Find matching column
                for header in headers:
                    if self._matches_template_pattern(header, column_pattern, best_template.patterns.get(field, [])):
                        mappings[field] = ColumnMapping(
                            source_column=header,
                            target_field=field,
                            confidence=MappingConfidence.HIGH,
                            confidence_score=best_score,
                            detection_method='template_match',
                            suggestions=[f"From template: {best_template.name}"]
                        )
                        break
        
        return mappings
    
    def _score_template_match(self, template: MappingTemplate, headers: List[str], sample_data: Optional[List[Dict[str, Any]]]) -> float:
        """Score how well a template matches the given headers."""
        if not template.mappings:
            return 0.0
        
        matches = 0
        total_fields = len(template.mappings)
        
        for field, column_pattern in template.mappings.items():
            for header in headers:
                if self._matches_template_pattern(header, column_pattern, template.patterns.get(field, [])):
                    matches += 1
                    break
        
        base_score = matches / total_fields if total_fields > 0 else 0.0
        
        # Bonus for template success rate and usage
        bonus = (template.success_rate / 100.0) * 0.1 + min(template.usage_count / 100.0, 0.1)
        
        return min(1.0, base_score + bonus)
    
    def _matches_template_pattern(self, header: str, column_pattern: str, regex_patterns: List[str]) -> bool:
        """Check if a header matches a template pattern."""
        header_lower = header.lower().strip()
        
        # Exact match
        if header_lower == column_pattern.lower():
            return True
        
        # Regex patterns
        for pattern in regex_patterns:
            if re.search(pattern.lower(), header_lower):
                return True
        
        # Fuzzy match
        similarity = difflib.SequenceMatcher(None, header_lower, column_pattern.lower()).ratio()
        return similarity > 0.8
    
    def _resolve_mapping_conflicts(self, all_mappings: Dict[str, Dict[str, ColumnMapping]], headers: List[str]) -> Dict[str, ColumnMapping]:
        """Resolve conflicts when multiple methods map to the same field or column."""
        final_mappings = {}
        
        # Priority order for mapping methods
        method_priority = ['exact', 'template', 'pattern', 'data', 'fuzzy']
        
        # Track which columns have been used
        used_columns = set()
        
        # Process each field
        for field in self.field_definitions.keys():
            best_mapping = None
            best_priority = len(method_priority)
            
            # Find the best mapping for this field
            for method in method_priority:
                if field in all_mappings[method]:
                    mapping = all_mappings[method][field]
                    
                    # Skip if column already used (unless this is higher priority)
                    if mapping.source_column in used_columns:
                        continue
                    
                    # This method has higher priority
                    if method_priority.index(method) < best_priority:
                        best_mapping = mapping
                        best_priority = method_priority.index(method)
            
            # Add the best mapping if found
            if best_mapping:
                final_mappings[field] = best_mapping
                used_columns.add(best_mapping.source_column)
        
        return final_mappings
    
    def _calculate_overall_confidence(self, mappings: Dict[str, ColumnMapping]) -> float:
        """Calculate overall confidence score for the mapping result."""
        if not mappings:
            return 0.0
        
        # Weight by field importance
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for field, mapping in mappings.items():
            field_weight = self.field_definitions[field]['weight']
            total_weight += field_weight
            weighted_confidence += mapping.confidence_score * field_weight
        
        base_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.0
        
        # Penalty for missing required fields
        required_fields = {field for field, config in self.field_definitions.items() if config['required']}
        mapped_required = set(mappings.keys()) & required_fields
        completeness_ratio = len(mapped_required) / len(required_fields) if required_fields else 1.0
        
        return base_confidence * completeness_ratio
    
    def _generate_transformation_suggestions(self, mappings: Dict[str, ColumnMapping], sample_data: Optional[List[Dict[str, Any]]]) -> Dict[str, List[str]]:
        """Generate suggestions for data transformations."""
        suggestions = {}
        
        if not sample_data:
            return suggestions
        
        for field, mapping in mappings.items():
            field_suggestions = []
            column = mapping.source_column
            
            # Analyze sample values
            values = []
            for row in sample_data:
                value = row.get(column, '')
                if value and str(value).strip():
                    values.append(str(value).strip())
            
            if not values:
                continue
            
            # Field-specific transformation suggestions
            if field == 'phone':
                # Check phone number formats
                formats = set()
                for value in values[:5]:  # Check first 5 values
                    if re.match(r'^\d{10}$', value):
                        formats.add('10-digit')
                    elif re.match(r'^\+\d', value):
                        formats.add('international')
                    elif re.match(r'^\(\d{3}\)', value):
                        formats.add('us-formatted')
                
                if '10-digit' in formats:
                    field_suggestions.append("Consider adding country code (+1) for US numbers")
                if len(formats) > 1:
                    field_suggestions.append("Standardize phone number format")
            
            elif field == 'email':
                # Check email case consistency
                mixed_case = any(c.isupper() for value in values for c in value)
                if mixed_case:
                    field_suggestions.append("Convert emails to lowercase for consistency")
            
            elif field == 'name':
                # Check name formatting
                all_caps = any(value.isupper() for value in values)
                all_lower = any(value.islower() for value in values)
                
                if all_caps:
                    field_suggestions.append("Convert names from ALL CAPS to proper case")
                elif all_lower:
                    field_suggestions.append("Convert names from lowercase to proper case")
            
            if field_suggestions:
                suggestions[field] = field_suggestions
        
        return suggestions
    
    def _suggest_similar_templates(self, mappings: Dict[str, ColumnMapping]) -> List[MappingTemplate]:
        """Suggest similar templates based on current mappings."""
        if not self.templates:
            return []
        
        # Score templates based on similarity to current mappings
        template_scores = []
        current_columns = {mapping.source_column.lower() for mapping in mappings.values()}
        
        for template in self.templates:
            template_columns = set(template.mappings.values())
            template_columns_lower = {col.lower() for col in template_columns}
            
            # Calculate similarity
            intersection = len(current_columns & template_columns_lower)
            union = len(current_columns | template_columns_lower)
            
            if union > 0:
                similarity = intersection / union
                if similarity > 0.3:  # Minimum similarity threshold
                    template_scores.append((template, similarity))
        
        # Return top 3 most similar templates
        template_scores.sort(key=lambda x: x[1], reverse=True)
        return [template for template, score in template_scores[:3]]
    
    def create_mapping_template(self, name: str, description: str, mappings: Dict[str, ColumnMapping]) -> MappingTemplate:
        """
        Create a new mapping template from current mappings.
        
        Args:
            name: Template name
            description: Template description
            mappings: Current column mappings
            
        Returns:
            Created mapping template
        """
        # Extract patterns from mappings
        template_mappings = {}
        template_patterns = {}
        
        for field, mapping in mappings.items():
            template_mappings[field] = mapping.source_column
            
            # Generate patterns based on the column name
            column_lower = mapping.source_column.lower()
            patterns = [
                f"^{re.escape(column_lower)}$",  # Exact match
                f".*{re.escape(column_lower)}.*"  # Contains match
            ]
            template_patterns[field] = patterns
        
        template = MappingTemplate(
            name=name,
            description=description,
            mappings=template_mappings,
            patterns=template_patterns,
            created_at=str(pd.Timestamp.now()),
            usage_count=0,
            success_rate=0.0
        )
        
        # Save template
        self.save_template(template)
        self.templates.append(template)
        
        logger.info(f"Created mapping template: {name}")
        return template
    
    def save_template(self, template: MappingTemplate) -> None:
        """Save a mapping template to disk."""
        try:
            template_file = self.templates_dir / f"{template.name.replace(' ', '_').lower()}.json"
            
            template_data = {
                'name': template.name,
                'description': template.description,
                'mappings': template.mappings,
                'patterns': template.patterns,
                'created_at': template.created_at,
                'usage_count': template.usage_count,
                'success_rate': template.success_rate
            }
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved template to {template_file}")
            
        except Exception as e:
            logger.error(f"Failed to save template {template.name}: {e}")
    
    def _load_templates(self) -> List[MappingTemplate]:
        """Load existing mapping templates from disk."""
        templates = []
        
        try:
            if not self.templates_dir.exists():
                return templates
            
            for template_file in self.templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    template = MappingTemplate(
                        name=data['name'],
                        description=data['description'],
                        mappings=data['mappings'],
                        patterns=data['patterns'],
                        created_at=data['created_at'],
                        usage_count=data.get('usage_count', 0),
                        success_rate=data.get('success_rate', 0.0)
                    )
                    
                    templates.append(template)
                    
                except Exception as e:
                    logger.warning(f"Failed to load template from {template_file}: {e}")
            
            logger.info(f"Loaded {len(templates)} mapping templates")
            
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
        
        return templates
    
    def update_template_usage(self, template_name: str, success: bool) -> None:
        """Update template usage statistics."""
        for template in self.templates:
            if template.name == template_name:
                template.usage_count += 1
                
                # Update success rate using exponential moving average
                if template.usage_count == 1:
                    template.success_rate = 100.0 if success else 0.0
                else:
                    alpha = 0.1  # Learning rate
                    new_success = 100.0 if success else 0.0
                    template.success_rate = (1 - alpha) * template.success_rate + alpha * new_success
                
                # Save updated template
                self.save_template(template)
                break
    
    def get_mapping_suggestions(self, unmapped_columns: List[str], missing_fields: List[str]) -> Dict[str, List[str]]:
        """
        Get suggestions for mapping unmapped columns to missing fields.
        
        Args:
            unmapped_columns: Columns that haven't been mapped
            missing_fields: Required fields that are missing
            
        Returns:
            Dictionary of field -> list of suggested columns
        """
        suggestions = {}
        
        for field in missing_fields:
            if field not in self.field_definitions:
                continue
            
            field_config = self.field_definitions[field]
            field_suggestions = []
            
            for column in unmapped_columns:
                column_lower = column.lower().strip()
                
                # Check against exact matches
                for exact_match in field_config['exact_matches']:
                    similarity = difflib.SequenceMatcher(None, column_lower, exact_match.lower()).ratio()
                    if similarity > 0.6:
                        field_suggestions.append((column, similarity, 'exact_similarity'))
                
                # Check against patterns
                for pattern in field_config['pattern_matches']:
                    if re.search(pattern, column_lower):
                        field_suggestions.append((column, 0.8, 'pattern_match'))
                
                # Check against fuzzy matches
                for fuzzy_match in field_config['fuzzy_matches']:
                    similarity = difflib.SequenceMatcher(None, column_lower, fuzzy_match.lower()).ratio()
                    if similarity > 0.7:
                        field_suggestions.append((column, similarity * 0.9, 'fuzzy_similarity'))
            
            # Sort by confidence and take top suggestions
            field_suggestions.sort(key=lambda x: x[1], reverse=True)
            suggestions[field] = [col for col, score, method in field_suggestions[:3]]
        
        return suggestions
    
    def validate_mapping(self, mappings: Dict[str, str], sample_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, List[str]]:
        """
        Validate a proposed column mapping.
        
        Args:
            mappings: Dictionary of field -> column mappings
            sample_data: Sample data for validation
            
        Returns:
            Dictionary of validation issues by field
        """
        issues = {}
        
        # Check for required fields
        required_fields = {field for field, config in self.field_definitions.items() if config['required']}
        missing_required = required_fields - set(mappings.keys())
        
        if missing_required:
            issues['_general'] = [f"Missing required fields: {', '.join(missing_required)}"]
        
        # Check for duplicate column usage
        used_columns = {}
        for field, column in mappings.items():
            if column in used_columns:
                field_issues = issues.setdefault(field, [])
                field_issues.append(f"Column '{column}' is already mapped to field '{used_columns[column]}'")
            else:
                used_columns[column] = field
        
        # Validate against sample data if available
        if sample_data:
            for field, column in mappings.items():
                field_issues = []
                
                # Check if column exists in sample data
                if not any(column in row for row in sample_data):
                    field_issues.append(f"Column '{column}' not found in sample data")
                    continue
                
                # Get sample values
                values = []
                for row in sample_data:
                    value = row.get(column, '')
                    if value and str(value).strip():
                        values.append(str(value).strip())
                
                if not values:
                    field_issues.append(f"Column '{column}' appears to be empty")
                    continue
                
                # Field-specific validation
                if field in self.field_definitions:
                    config = self.field_definitions[field]
                    
                    # Check positive patterns
                    positive_matches = 0
                    for pattern in config.get('data_patterns', []):
                        matches = sum(1 for value in values if re.match(pattern, value))
                        positive_matches = max(positive_matches, matches)
                    
                    if positive_matches < len(values) * 0.5:
                        field_issues.append(f"Less than 50% of values match expected {field} patterns")
                    
                    # Check negative patterns
                    for pattern in config.get('negative_patterns', []):
                        matches = sum(1 for value in values if re.match(pattern, value))
                        if matches > len(values) * 0.3:
                            field_issues.append(f"More than 30% of values match patterns that should NOT be {field}")
                
                if field_issues:
                    issues[field] = field_issues
        
        return issues


# Import pandas for timestamp functionality
try:
    import pandas as pd
except ImportError:
    # Fallback for timestamp functionality
    from datetime import datetime
    class pd:
        class Timestamp:
            @staticmethod
            def now():
                return datetime.now()