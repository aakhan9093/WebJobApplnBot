"""
Framework Scorer - Rates strategic frameworks against the job description.
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass

from src.types import FrameworkScore
from src.utils import TextProcessor


class FrameworkScorer:
    """Scores strategic frameworks based on alignment with JD."""

    def __init__(self):
        self.text_processor = TextProcessor()

    def score_framework(self, framework: Dict[str, Any], jd_content: str,
                       pain_point: Dict[str, Any]) -> FrameworkScore:
        """
        Score a framework against the job description.

        Args:
            framework: The generated framework dictionary
            jd_content: Full job description text
            pain_point: The pain point this framework addresses

        Returns:
            FrameworkScore object with component scores and total
        """
        alignment_score = self._score_alignment(framework, jd_content, pain_point)
        business_value_score = self._score_business_value(framework, jd_content)
        skills_score = self._score_skills_demonstration(framework, jd_content)
        fear_score = self._score_addresses_hiring_manager_fear(framework, jd_content, pain_point)

        total_score = FrameworkScore.calculate_total(
            alignment_score, business_value_score, skills_score, fear_score
        )

        return FrameworkScore(
            alignment_score=alignment_score,
            business_value_score=business_value_score,
            skills_score=skills_score,
            fear_score=fear_score,
            total_score=total_score
        )

    def _score_alignment(self, framework: Dict[str, Any], jd_content: str,
                        pain_point: Dict[str, Any]) -> int:
        """Score how directly the framework addresses a primary function of the role (0-5)."""
        score = 0

        # Check if framework title and pain point align with JD keywords
        jd_lower = jd_content.lower()
        pain_desc = pain_point['description'].lower()

        # Extract key terms from pain point
        pain_keywords = self.text_processor.extract_keywords(pain_desc, min_length=4)

        # Count how many pain keywords appear in JD
        matches = sum(1 for kw in pain_keywords if kw in jd_lower)
        keyword_ratio = matches / len(pain_keywords) if pain_key_words else 0

        if keyword_ratio >= 0.7:
            score += 2
        elif keyword_ratio >= 0.4:
            score += 1

        # Check if framework phases address the pain point
        framework_content = framework['raw_content'].lower()
        pain_terms = self.text_processor.extract_keywords(pain_desc, min_length=4)
        framework_matches = sum(1 for term in pain_terms if term in framework_content)

        if framework_matches >= len(pain_terms) * 0.5:
            score += 2

        # Bonus for using JD-specific terminology
        jd_keywords = self.text_processor.extract_keywords(jd_content, min_length=4)[:20]
        jd_term_matches = sum(1 for kw in jd_keywords if kw in framework_content)
        if jd_term_matches >= 5:
            score += 1

        return min(score, 5)

    def _score_business_value(self, framework: Dict[str, Any], jd_content: str) -> int:
        """Score how critical solving this problem is to the business (0-5)."""
        score = 0

        jd_lower = jd_content.lower()
        framework_content = framework['raw_content'].lower()

        # Look for business value indicators in JD
        value_indicators = [
            'revenue', 'profit', 'cost', 'efficiency', 'growth', 'customer',
            'competitive', 'market', 'roi', 'investment', 'budget', 'financial',
            'bottom line', 'top line', 'profitability', 'savings', 'increase',
            'decrease', 'improve', 'optimize'
        ]

        # Count value indicators in JD
        jd_value_count = sum(1 for indicator in value_indicators if indicator in jd_lower)

        if jd_value_count >= 10:
            score += 2  # High business value indicated
        elif jd_value_count >= 5:
            score += 1

        # Check if framework includes measurable outcomes
        if 'baseline' in framework_content and 'target' in framework_content:
            score += 1

        # Check for quantified results
        if re.search(r'\d+%', framework_content):
            score += 1

        # Check for time-bound outcomes
        if re.search(r'\b(quarter|month|week|year|day)\b', framework_content):
            score += 1

        return min(score, 5)

    def _score_skills_demonstration(self, framework: Dict[str, Any], jd_content: str) -> int:
        """Score how well the framework demonstrates required skills (0-5)."""
        score = 0

        jd_lower = jd_content.lower()
        framework_content = framework['raw_content'].lower()

        # Extract skill indicators from JD
        skill_categories = {
            'analytical': ['analyze', 'data', 'metrics', 'measure', 'evaluate', 'assess', 'research'],
            'technical': ['develop', 'build', 'implement', 'design', 'architecture', 'system', 'technical'],
            'leadership': ['lead', 'manage', 'team', 'collaborate', 'stakeholder', 'influence', 'direct'],
            'communication': ['communicate', 'present', 'document', 'report', 'share', 'align'],
            'strategic': ['strategy', 'planning', 'roadmap', 'vision', 'long-term', 'goals']
        }

        # Check which skill categories are mentioned in JD
        jd_skills = []
        for category, terms in skill_categories.items():
            if any(term in jd_lower for term in terms):
                jd_skills.append(category)

        # Check if framework demonstrates these skills
        framework_skills = []
        for category, terms in skill_categories.items():
            if any(term in framework_content for term in terms):
                framework_skills.append(category)

        # Score based on overlap
        overlap = set(jd_skills) & set(framework_skills)
        if len(overlap) >= 3:
            score += 3
        elif len(overlap) >= 2:
            score += 2
        elif len(overlap) >= 1:
            score += 1

        # Bonus for showing specific methodologies
        methodologies = ['agile', 'scrum', 'lean', 'six sigma', 'sdlc', 'waterfall',
                         'iterative', 'kanban', 'devops', 'ci/cd', 'sprint']

        if any(method in framework_content for method in methodologies):
            score += 1

        # Bonus for showing collaboration
        if 'collaborat' in framework_content or 'team' in framework_content:
            score += 1

        return min(score, 5)

    def _score_addresses_hiring_manager_fear(self, framework: Dict[str, Any],
                                            jd_content: str, pain_point: Dict[str, Any]) -> int:
        """
        Score how effectively the framework mitigates a primary concern about
        an industry outsider (0-5).
        """
        score = 0

        framework_content = framework['raw_content'].lower()
        jd_lower = jd_content.lower()

        # Common hiring manager fears for external candidates:
        fears = {
            'learning_curve': ['learn', 'understand', 'quickly', 'ramp', 'onboarding', 'familiar'],
            'cultural_fit': ['collaborate', 'team', 'stakeholder', 'culture', 'work with'],
            'domain_knowledge': ['industry', 'domain', 'regulatory', 'compliance', 'standards'],
            'execution_risk': ['proven', 'track record', 'experience', 'success', 'delivered'],
            'integration': ['integrate', 'align', 'coordinate', 'cross-functional', 'silo']
        }

        # Check which fears are relevant based on JD content
        relevant_fears = []
        for fear_type, indicators in fears.items():
            if any(indicator in jd_lower for indicator in indicators[:2]):
                relevant_fears.append(fear_type)

        # Check if framework addresses these fears
        for fear_type in relevant_fears:
            indicators = fears[fear_type]
            if any(indicator in framework_content for indicator in indicators):
                score += 1

        # Bonus for showing collaborative approach (addresses "lone wolf" fear)
        if 'we' in framework_content or 'team' in framework_content or 'collaborative' in framework_content:
            score += 1

        # Bonus for showing structured approach (addresses "unproven" fear)
        if 'phase' in framework_content and 'governance' in framework_content:
            score += 1

        # Bonus for showing measurable outcomes (addresses "results" fear)
        if 'kpi' in framework_content or 'metric' in framework_content or 'baseline' in framework_content:
            score += 1

        return min(score, 5)