"""
Job Description Analyzer - Extracts and ranks pain points from JDs.
"""

import re
from typing import List, Dict, Any, Optional
from collections import defaultdict

from src.types import PainPoint
from src.config import BotConfig
from src.utils import TextProcessor


class JDAnalyzer:
    """Analyzes job descriptions to extract and rank pain points."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.text_processor = TextProcessor()

    def analyze(self, jd_text: str) -> List[Dict[str, Any]]:
        """
        Analyze a job description and return ranked pain points.

        Args:
            jd_text: Raw job description text

        Returns:
            List of pain point dictionaries, ranked by score
        """
        # Clean and prepare text
        clean_text = self.text_processor.clean_text(jd_text)

        # Extract key sections
        sections = self._extract_sections(clean_text)

        # Identify potential pain points
        pain_points = self._identify_pain_points(clean_text, sections)

        # Score and rank pain points
        scored_pain_points = self._score_pain_points(pain_points, clean_text, sections)

        # Sort by score descending and return top 3-5
        scored_pain_points.sort(key=lambda x: x['score'], reverse=True)

        # Return top 5 or all if fewer
        top_pain_points = scored_pain_points[:5]

        return top_pain_points

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract major sections from the JD."""
        sections = {}

        # Common section headers
        section_patterns = {
            'responsibilities': r'(?:key\s+)?responsibilities|duties|what\s+you\s+will\s+do|job\s+duties',
            'requirements': r'requirements|qualifications|what\s+you\s+need|must\s+have|required',
            'preferred': r'preferred|nice\s+to\s+have|desired|plus',
            'about': r'about\s+(?:us|the\s+role|the\s+company)|company|overview',
            'summary': r'summary|position\s+overview|role\s+overview'
        }

        lines = text.split('\n')
        current_section = None
        section_content = []

        for line in lines:
            line_lower = line.lower().strip()

            # Check if line is a section header
            for section_name, pattern in section_patterns.items():
                if re.search(pattern, line_lower, re.IGNORECASE):
                    if current_section and section_content:
                        sections[current_section] = ' '.join(section_content)
                    current_section = section_name
                    section_content = []
                    break

            if current_section:
                section_content.append(line)

        # Add the last section
        if current_section and section_content:
            sections[current_section] = ' '.join(section_content)

        return sections

    def _identify_pain_points(self, text: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Identify potential pain points from the JD."""
        pain_points = []

        # Extract bullet points from responsibilities and requirements
        for section_name in ['responsibilities', 'requirements']:
            if section_name in sections:
                bullets = self.text_processor.extract_bullet_points(sections[section_name])
                for bullet in bullets:
                    pain_point = self._analyze_bullet_point(bullet, section_name)
                    if pain_point:
                        pain_points.append(pain_point)

        # Also look for pain points in the full text based on keywords
        pain_keywords = self.config.pain_point_keywords
        for keyword in pain_keywords:
            pattern = rf'\b{re.escape(keyword)}\b.*?(?=[.!?]|\n)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.split()) >= 5:  # Minimum meaningful length
                    pain_points.append({
                        'title': self._generate_title(match),
                        'description': match.strip(),
                        'source': 'keyword_match',
                        'raw_text': match
                    })

        # Deduplicate based on description similarity
        unique_pain_points = self._deduplicate_pain_points(pain_points)

        return unique_pain_points

    def _analyze_bullet_point(self, bullet: str, section: str) -> Optional[Dict[str, Any]]:
        """Analyze a single bullet point for pain point indicators."""
        bullet_lower = bullet.lower()

        # Check for seniority signals
        has_seniority = any(indicator in bullet_lower for indicator in self.config.seniority_indicators)

        # Check for pain language
        pain_terms = self.config.pain_language_terms
        pain_score = sum(1 for term in pain_terms if term in bullet_lower)

        # Only consider if it has some significance
        if len(bullet.split()) < 5:
            return None

        # Generate a concise title
        title = self._generate_title(bullet)

        return {
            'title': title,
            'description': bullet,
            'section': section,
            'has_seniority': has_seniority,
            'pain_score': pain_score,
            'source': 'bullet_point'
        }

    def _generate_title(self, text: str) -> str:
        """Generate a concise title for a pain point."""
        # Extract the main action/verb
        verbs = ['improve', 'develop', 'create', 'establish', 'streamline',
                 'optimize', 'transform', 'lead', 'manage', 'design', 'implement']

        text_lower = text.lower()

        for verb in verbs:
            if verb in text_lower:
                # Find the context around the verb
                pattern = rf'{verb}\s+(\w+(?:\s+\w+){{0,3}})'
                match = re.search(pattern, text_lower)
                if match:
                    phrase = match.group(0)
                    # Capitalize first letter and clean up
                    title = phrase[0].upper() + phrase[1:]
                    if len(title) > 60:
                        title = title[:57] + "..."
                    return title

        # Fallback: use first 50 characters
        if len(text) > 50:
            return text[:50].strip() + "..."
        return text.strip()

    def _deduplicate_pain_points(self, pain_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or very similar pain points."""
        unique = []
        seen_descriptions = set()

        for pp in pain_points:
            desc = pp['description'].lower()
            # Simple deduplication based on first 100 chars
            desc_key = desc[:100]

            if desc_key not in seen_descriptions:
                seen_descriptions.add(desc_key)
                unique.append(pp)

        return unique

    def _score_pain_points(self, pain_points: List[Dict[str, Any]], full_text: str,
                          sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Score pain points based on the ranking criteria."""
        scored_points = []

        # Calculate total word count for frequency analysis
        total_words = len(full_text.split())

        for pp in pain_points:
            score = 0.0

            # 1. Frequency: How often is this type of responsibility mentioned?
            frequency = self._calculate_frequency(pp, full_text)
            if frequency >= 3:
                score += 5
            elif frequency >= 2:
                score += 3
            elif frequency >= 1:
                score += 1

            # 2. Emphasis: Is it in a key section?
            emphasis_score = self._calculate_emphasis(pp, sections)
            score += emphasis_score

            # 3. Seniority Signal: Does it start with Lead/Develop/Transform/Optimize?
            if pp.get('has_seniority', False):
                score += 4

            # 4. Pain Language: Does it contain pain-related words?
            pain_score = pp.get('pain_score', 0)
            if pain_score >= 3:
                score += 3
            elif pain_score >= 1:
                score += 1

            # Additional: Position in document (earlier = more important)
            position_score = self._calculate_position_score(pp, full_text)
            score += position_score

            # Create PainPoint object with final score
            pain_point_obj = PainPoint(
                title=pp['title'],
                description=pp['description'],
                score=score,
                frequency=frequency,
                emphasis_level=emphasis_score,
                seniority_signal=pp.get('has_seniority', False),
                pain_language_score=pain_score,
                raw_matches=[pp.get('raw_text', pp['description'])]
            )

            scored_points.append(pain_point_obj.to_dict())

        return scored_points

    def _calculate_frequency(self, pain_point: Dict[str, Any], text: str) -> int:
        """Calculate how many times this pain point's theme appears."""
        # Count occurrences of key terms from the pain point
        key_terms = self._extract_key_terms(pain_point['description'])
        total_occurrences = 0

        for term in key_terms:
            pattern = rf'\b{re.escape(term)}\b'
            occurrences = len(re.findall(pattern, text, re.IGNORECASE))
            total_occurrences += occurrences

        # Normalize by number of key terms
        if key_terms:
            return total_occurrences // len(key_terms)
        return 0

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text for frequency matching."""
        # Remove stop words and get meaningful terms
        words = re.findall(r'\b\w+\b', text.lower())
        stop_words = {'the', 'and', 'or', 'to', 'for', 'of', 'in', 'on', 'at', 'with',
                      'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
                      'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
                      'a', 'an', 'as', 'it', 'its', 'they', 'them', 'their', 'we',
                      'us', 'our', 'you', 'your', 'i', 'my', 'me', 'mine', 'am',
                      'not', 'from', 'into', 'this', 'that', 'these', 'those'}

        meaningful = [w for w in words if w not in stop_words and len(w) > 2]
        return meaningful[:5]  # Top 5 meaningful terms

    def _calculate_emphasis(self, pain_point: Dict[str, Any], sections: Dict[str, str]) -> int:
        """Calculate emphasis score based on which section the pain point appears in."""
        section = pain_point.get('section', '')

        # High emphasis sections
        if section in ['responsibilities', 'summary']:
            return 4
        elif section in ['requirements']:
            return 3
        elif section in ['preferred']:
            return 2
        else:
            return 1

    def _calculate_position_score(self, pain_point: Dict[str, Any], text: str) -> int:
        """Calculate score based on where the pain point appears in the document."""
        # Find first occurrence
        desc = pain_point['description']
        position = text.lower().find(desc.lower())

        if position == -1:
            return 0

        # Earlier positions get higher scores (first 30% of document)
        document_length = len(text)
        relative_position = position / document_length

        if relative_position < 0.3:
            return 2
        elif relative_position < 0.6:
            return 1
        else:
            return 0
