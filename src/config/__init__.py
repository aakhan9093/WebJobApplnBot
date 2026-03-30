"""
Configuration settings for the Job Application Bot.
"""

import os
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class BotConfig:
    """Main configuration class for the bot."""

    # JD Analysis Settings
    pain_point_keywords: List[str] = None
    seniority_indicators: List[str] = None
    pain_language_terms: List[str] = None

    # CV Modification Settings
    cv_section_headers: List[str] = None
    keyword_match_threshold: int = 2  # Minimum occurrences to consider a keyword important
    max_cv_length: int = 2000  # Maximum characters for modified sections

    # Framework Generation Settings
    framework_phases: List[str] = None
    min_framework_score: int = 12  # Minimum score to include a framework (out of 20)
    language_complexity_target: str = "8th-10th grade"

    # Scoring Weights
    weight_alignment: float = 0.25
    weight_business_value: float = 0.25
    weight_skills: float = 0.25
    weight_fear: float = 0.25

    # File Settings
    default_encoding: str = "utf-8"
    max_file_size_mb: int = 10

    def __post_init__(self):
        """Initialize default values if None."""
        if self.pain_point_keywords is None:
            self.pain_point_keywords = [
                "improve", "establish", "streamline", "optimize", "transform",
                "evolving", "complex", "fast-paced", "challenge", "critical",
                "lead", "develop", "manage", "design", "implement", "enhance",
                "reduce", "increase", "drive", "strategic", "efficiency"
            ]

        if self.seniority_indicators is None:
            self.seniority_indicators = [
                "lead", "develop", "transform", "optimize", "design",
                "architect", "strategic", "direct", "oversee", "establish"
            ]

        if self.pain_language_terms is None:
            self.pain_language_terms = [
                "struggle", "difficult", "problem", "issue", "pain",
                "challenge", "bottleneck", "inefficient", "manual", "slow",
                "error-prone", "fragmented", "siloed", "duplication", "waste"
            ]

        if self.framework_phases is None:
            self.framework_phases = [
                "UNDERSTAND THE CURRENT SITUATION",
                "IDENTIFY KEY AREAS FOR IMPROVEMENT",
                "DEVELOP TARGETED SOLUTIONS",
                "IMPLEMENT WITH CLEAR GOVERNANCE",
                "BUILD FOR LONG-TERM SUCCESS"
            ]

    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Load configuration from environment variables."""
        return cls(
            keyword_match_threshold=int(os.getenv('KEYWORD_MATCH_THRESHOLD', 2)),
            min_framework_score=int(os.getenv('MIN_FRAMEWORK_SCORE', 12)),
            default_encoding=os.getenv('DEFAULT_ENCODING', 'utf-8'),
            max_file_size_mb=int(os.getenv('MAX_FILE_SIZE_MB', 10))
        )