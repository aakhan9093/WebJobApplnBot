"""
Utility functions for text processing, file handling, and prompt building.
"""

import re
import os
import requests
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse
import json
from pathlib import Path


class TextProcessor:
    """Process and analyze text content."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-"]', '', text)
        return text.strip()

    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting on punctuation
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def extract_keywords(text: str, min_length: int = 3) -> List[str]:
        """Extract potential keywords from text."""
        # Remove common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
            'might', 'must', 'can', 'this', 'that', 'these', 'those', 'a', 'an',
            'as', 'it', 'its', 'they', 'them', 'their', 'we', 'us', 'our', 'you',
            'your', 'i', 'my', 'me', 'mine', 'am', 'not', 'from', 'into', 'during',
            'including', 'until', 'against', 'among', 'throughout', 'despite'
        }

        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) >= min_length and w not in stop_words]
        return keywords

    @staticmethod
    def calculate_word_frequency(text: str) -> Dict[str, int]:
        """Calculate frequency of each word in text."""
        words = re.findall(r'\b\w+\b', text.lower())
        freq = {}
        for word in words:
            freq[word] = freq.get(word, 0) + 1
        return freq

    @staticmethod
    def find_pattern_matches(text: str, patterns: List[str]) -> List[str]:
        """Find all occurrences of patterns in text."""
        matches = []
        for pattern in patterns:
            # Case-insensitive search for whole words
            regex = re.compile(r'\b' + re.escape(pattern) + r'\b', re.IGNORECASE)
            found = regex.findall(text)
            matches.extend(found)
        return matches

    @staticmethod
    def extract_bullet_points(text: str) -> List[str]:
        """Extract bullet points from text."""
        # Match lines starting with bullet characters or numbers
        bullet_pattern = r'^[\s]*([•\-*→]|\d+\.|\d+\)|\w+\))\s+(.+)$'
        bullets = []

        for line in text.split('\n'):
            line = line.strip()
            if re.match(bullet_pattern, line, re.MULTILINE):
                # Remove the bullet marker
                clean_line = re.sub(bullet_pattern, r'\2', line)
                bullets.append(clean_line)

        return bullets

    @staticmethod
    def estimate_reading_level(text: str) -> str:
        """Estimate reading level based on average sentence length and word complexity."""
        sentences = TextProcessor.extract_sentences(text)
        if not sentences:
            return "Unknown"

        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

        # Count complex words (more than 3 syllables - simplified)
        words = re.findall(r'\b\w+\b', text.lower())
        complex_words = sum(1 for w in words if len(w) > 8)  # Rough proxy

        complexity_ratio = complex_words / len(words) if words else 0

        if avg_sentence_length < 15 and complexity_ratio < 0.1:
            return "8th-10th grade"
        elif avg_sentence_length < 20 and complexity_ratio < 0.15:
            return "11th-12th grade"
        else:
            return "College level"


class FileHandler:
    """Handle file operations and URL scraping."""

    @staticmethod
    def read_file(filepath: str, encoding: str = "utf-8") -> str:
        """Read content from a file (supports .txt, .md, .pdf, .docx)."""
        path = Path(filepath) if isinstance(filepath, str) else filepath

        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Check file size
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > 10:
            raise ValueError(f"File too large: {size_mb:.1f}MB (max 10MB)")

        extension = path.suffix.lower()

        if extension == '.pdf':
            try:
                from pypdf import PdfReader
                reader = PdfReader(path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
            except ImportError:
                raise ImportError("pypdf is required to read PDF files. Run 'pip install pypdf'.")
        
        elif extension == '.docx':
            try:
                import docx
                doc = docx.Document(path)
                return "\n".join([para.text for para in doc.paragraphs]).strip()
            except ImportError:
                raise ImportError("python-docx is required to read DOCX files. Run 'pip install python-docx'.")

        # Default to text reading
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Try alternate encoding if utf-8 fails
            with open(path, 'r', encoding='latin-1') as f:
                return f.read()

    @staticmethod
    def write_file(content: str, filepath: str, encoding: str = "utf-8"):
        """Write content to a file."""
        path = Path(filepath) if isinstance(filepath, str) else filepath

        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding=encoding) as f:
            f.write(content)

    @staticmethod
    def scrape_url(url: str, timeout: int = 30) -> str:
        """Scrape text content from a URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            # Basic HTML cleaning - remove tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', response.text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text)

            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to scrape URL {url}: {str(e)}")

    @staticmethod
    def extract_company_name(text: str) -> Optional[str]:
        """Try to extract company name from text."""
        # Look for common patterns
        patterns = [
            r'at\s+([A-Z][a-zA-Z0-9\s]+?)(?:\s+is|\s+we|\s+seeks|\s+looking|\s*\.)',
            r'([A-Z][a-zA-Z0-9\s]+?)\s+(?:is|we|seeks|hiring|looking)',
            r'Company:\s*([A-Z][a-zA-Z0-9\s]+)',
            r'Organization:\s*([A-Z][a-zA-Z0-9\s]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Filter out common false positives
                if company and len(company) > 2 and company.lower() not in ['the', 'a', 'an']:
                    return company

        return None

    @staticmethod
    def ensure_dir(directory: str):
        """Ensure a directory exists."""
        Path(directory).mkdir(parents=True, exist_ok=True)


# Import path here to avoid circular imports
from pathlib import Path