"""
Type definitions for the Job Application Bot.
These dataclasses define the structure of data used throughout the application.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class PainPoint:
    """Represents a pain point extracted from a job description."""
    title: str
    description: str
    score: float  # 0-20 based on ranking criteria
    frequency: int  # How many times mentioned
    emphasis_level: int  # 1-3 based on placement/section
    seniority_signal: bool  # Lead/Develop/Transform/Optimize indicators
    pain_language_score: int  # 0-5 based on pain-related keywords
    raw_matches: List[str] = field(default_factory=list)  # Supporting text snippets

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'title': self.title,
            'description': self.description,
            'score': self.score,
            'frequency': self.frequency,
            'emphasis_level': self.emphasis_level,
            'seniority_signal': self.seniority_signal,
            'pain_language_score': self.pain_language_score,
            'raw_matches': self.raw_matches
        }


@dataclass
class FrameworkScore:
    """Scores for a strategic framework against the JD."""
    alignment_score: int  # 0-5
    business_value_score: int  # 0-5
    skills_score: int  # 0-5
    fear_score: int  # 0-5
    total_score: int  # Sum of above (0-20)

    @classmethod
    def calculate_total(cls, alignment: int, business_value: int, skills: int, fear: int) -> int:
        """Calculate total score from component scores."""
        return alignment + business_value + skills + fear

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            'alignment_score': self.alignment_score,
            'business_value_score': self.business_value_score,
            'skills_score': self.skills_score,
            'fear_score': self.fear_score,
            'total_score': self.total_score
        }


@dataclass
class StrategicFramework:
    """Complete strategic framework with all required sections."""
    title: str
    company_name: str
    executive_summary: Dict[str, str]  # challenge, core_principle, expected_outcome
    phases: List[Dict[str, Any]]  # List of phase objects
    measurable_outcomes: List[Dict[str, str]]  # KPIs with baseline/target
    strategic_advantages: List[str]
    next_steps: List[str]
    score: FrameworkScore
    raw_content: str  # Full markdown content

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'title': self.title,
            'company_name': self.company_name,
            'executive_summary': self.executive_summary,
            'phases': self.phases,
            'measurable_outcomes': self.measurable_outcomes,
            'strategic_advantages': self.strategic_advantages,
            'next_steps': self.next_steps,
            'score': self.score.to_dict(),
            'raw_content': self.raw_content
        }


@dataclass
class ModifiedCV:
    """Represents a CV modified to align with a job description."""
    original_content: str
    modified_content: str
    modifications_made: List[Dict[str, str]]  # List of changes with explanations
    keyword_matches: Dict[str, int]  # JD keywords found in CV with counts
    alignment_score: float  # 0-100 overall alignment

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'original_content': self.original_content,
            'modified_content': self.modified_content,
            'modifications_made': self.modifications_made,
            'keyword_matches': self.keyword_matches,
            'alignment_score': self.alignment_score
        }


@dataclass
class JobDescription:
    """Parsed job description data."""
    raw_text: str
    company: Optional[str]
    job_title: Optional[str]
    key_responsibilities: List[str]
    requirements: List[str]
    challenges: List[str]
    keywords: List[str]
    pain_points: List[PainPoint] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'raw_text': self.raw_text,
            'company': self.company,
            'job_title': self.job_title,
            'key_responsibilities': self.key_responsibilities,
            'requirements': self.requirements,
            'challenges': self.challenges,
            'keywords': self.keywords,
            'pain_points': [pp.to_dict() for pp in self.pain_points]
        }