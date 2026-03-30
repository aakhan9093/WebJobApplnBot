"""
CV Modifier - Aligns CV content with job description requirements.
"""

import re
from typing import List, Dict, Any, Tuple
from collections import Counter

from src.types import ModifiedCV
from src.config import BotConfig
from src.utils import TextProcessor


class CVModifier:
    """Modifies CV to align with job description keywords and requirements."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.text_processor = TextProcessor()

    def modify(self, cv_content: str, jd_content: str, pain_points: List[Dict[str, Any]]) -> str:
        """
        Modify CV to better align with the job description.

        Args:
            cv_content: Original CV content
            jd_content: Job description content
            pain_points: Ranked pain points from JD analysis

        Returns:
            Modified CV content as string
        """
        # Extract keywords from JD
        jd_keywords = self._extract_jd_keywords(jd_content, pain_points)

        # Analyze current CV alignment
        current_alignment = self._calculate_alignment(cv_content, jd_keywords)

        # Modify CV sections
        modified_cv = cv_content

        # 1. Enhance summary/objective section if present
        modified_cv = self._enhance_summary(modified_cv, jd_keywords, pain_points)

        # 2. Modify experience bullet points to include keywords
        modified_cv = self._enhance_experience(modified_cv, jd_keywords)

        # 3. Ensure skills section includes relevant keywords
        modified_cv = self._enhance_skills(modified_cv, jd_keywords)

        # 4. Add a targeted cover letter intro (optional)
        modified_cv = self._add_targeted_intro(modified_cv, pain_points)

        # Calculate new alignment
        new_alignment = self._calculate_alignment(modified_cv, jd_keywords)

        return modified_cv

    def _extract_jd_keywords(self, jd_content: str, pain_points: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract and weight keywords from the JD."""
        keywords = {}

        # Get keywords from full JD
        all_keywords = self.text_processor.extract_keywords(jd_content, min_length=3)
        word_freq = self.text_processor.calculate_word_frequency(jd_content)

        for keyword in all_keywords:
            # Weight by frequency
            freq = word_freq.get(keyword, 0)
            if freq >= 2:
                keywords[keyword] = freq

        # Boost keywords from pain points (high-priority)
        for pain_point in pain_points[:3]:  # Top 3 pain points
            pain_text = pain_point['description']
            pain_keywords = self.text_processor.extract_keywords(pain_text, min_length=3)
            for keyword in pain_keywords:
                keywords[keyword] = keywords.get(keyword, 0) + 3  # Extra weight

        # Sort by weight
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)

        return dict(sorted_keywords[:30])  # Top 30 keywords

    def _calculate_alignment(self, cv_content: str, jd_keywords: Dict[str, int]) -> float:
        """Calculate how well the CV aligns with JD keywords."""
        cv_lower = cv_content.lower()
        matches = 0
        total_weight = sum(jd_keywords.values())

        for keyword, weight in jd_keywords.items():
            if keyword.lower() in cv_lower:
                matches += weight

        if total_weight == 0:
            return 0.0

        alignment = (matches / total_weight) * 100
        return round(alignment, 1)

    def _enhance_summary(self, cv: str, jd_keywords: Dict[str, int], pain_points: List[Dict[str, Any]]) -> str:
        """Enhance the summary section with JD keywords."""
        # Look for summary/objective section
        summary_patterns = [
            r'(summary|objective|profile|about\s+me|professional\s+summary)[:\n]+(.*?)(?=\n\s*\n|\n\s*[A-Z][a-z]+\s*[A-Z][a-z]+:)',
            r'(^.*?(?:summary|objective).*?$)(.*?)(?=\n\s*\n)'
        ]

        for pattern in summary_patterns:
            match = re.search(pattern, cv, re.IGNORECASE | re.DOTALL)
            if match:
                summary_header = match.group(1)
                summary_content = match.group(2).strip()

                # Add top 3-5 JD keywords naturally
                top_keywords = list(jd_keywords.keys())[:5]
                keyword_phrase = ", ".join(top_keywords)

                enhanced_summary = f"{summary_header}\n{summary_content}\n\nSkilled in {keyword_phrase} with a proven track record of delivering results in dynamic environments."

                # Replace in CV
                cv = cv.replace(match.group(0), enhanced_summary)
                break

        return cv

    def _enhance_experience(self, cv: str, jd_keywords: Dict[str, int]) -> str:
        """Enhance experience bullet points with relevant keywords."""
        # Find experience section
        experience_pattern = r'(experience|work\s+experience|professional\s+experience)[:\n]+(.*?)(?=\n\s*\n|\n\s*[A-Z][a-z]+\s*[A-Z][a-z]+:)'

        match = re.search(experience_pattern, cv, re.IGNORECASE | re.DOTALL)
        if not match:
            return cv

        experience_section = match.group(0)
        experience_content = match.group(1) + "\n" + match.group(2)

        # Find bullet points and enhance them
        lines = experience_content.split('\n')
        enhanced_lines = []

        for i, line in enumerate(lines):
            if re.match(r'^[\s]*[•\-*→]|\d+\.|\d+\)|\w+\)', line.strip()):
                # This is a bullet point
                bullet = line.strip()
                enhanced_bullet = self._enhance_bullet_point(bullet, jd_keywords)
                enhanced_lines.append(enhanced_bullet)
            else:
                enhanced_lines.append(line)

        enhanced_experience = '\n'.join(enhanced_lines)
        cv = cv.replace(experience_content, enhanced_experience)

        return cv

    def _enhance_bullet_point(self, bullet: str, jd_keywords: Dict[str, int]) -> str:
        """Enhance a single bullet point with relevant keywords."""
        bullet_lower = bullet.lower()

        # Check which keywords are missing
        missing_keywords = []
        for keyword in jd_keywords.keys():
            if keyword.lower() not in bullet_lower and len(keyword) > 3:
                missing_keywords.append(keyword)

        # If we have missing high-weight keywords, try to incorporate one
        if missing_keywords:
            # Sort missing keywords by weight in JD
            sorted_missing = sorted(missing_keywords, key=lambda k: jd_keywords.get(k, 0), reverse=True)

            for keyword in sorted_missing[:2]:  # Try top 2 missing keywords
                # Check if the keyword is semantically relevant
                if self._is_relevant_to_bullet(keyword, bullet):
                    # Add it naturally
                    enhanced = f"{bullet} Utilized {keyword} to drive results."
                    if len(enhanced) < 200:  # Keep within reasonable length
                        return enhanced

        return bullet

    def _is_relevant_to_bullet(self, keyword: str, bullet: str) -> bool:
        """Check if a keyword is semantically relevant to a bullet point."""
        # Simple heuristic: check if bullet contains related terms
        bullet_lower = bullet.lower()

        # Define some semantic groups
        semantic_groups = {
            'data': ['analysis', 'analytics', 'database', 'sql', 'report', 'dashboard'],
            'manage': ['team', 'lead', 'direct', 'supervise', 'oversee'],
            'develop': ['build', 'create', 'design', 'implement', 'code'],
            'optimize': ['improve', 'enhance', 'streamline', 'reduce', 'increase'],
            'strategic': ['plan', 'roadmap', 'vision', 'long-term', 'goals']
        }

        # Check if keyword is in any group and bullet has related terms
        for group_key, group_terms in semantic_groups.items():
            if keyword.lower() in group_terms or group_key in keyword.lower():
                if any(term in bullet_lower for term in group_terms):
                    return True

        return False

    def _enhance_skills(self, cv: str, jd_keywords: Dict[str, int]) -> str:
        """Ensure skills section includes relevant JD keywords."""
        # Find skills section
        skills_pattern = r'(skills|technical\s+skills|competencies|expertise)[:\n]+(.*?)(?=\n\s*\n|\n\s*[A-Z][a-z]+\s*[A-Z][a-z]+:)'

        match = re.search(skills_pattern, cv, re.IGNORECASE | re.DOTALL)
        if not match:
            return cv

        skills_section = match.group(0)
        skills_content = match.group(2)

        # Extract current skills
        current_skills = set()
        for line in skills_content.split('\n'):
            skills = re.findall(r'[\w\s]+', line.strip())
            current_skills.update([s.lower() for s in skills if len(s) > 2])

        # Find missing high-priority keywords
        missing_skills = []
        for keyword, weight in jd_keywords.items():
            if weight >= 2 and keyword.lower() not in current_skills:
                missing_skills.append(keyword)

        # Add missing skills to the section
        if missing_skills:
            additional_skills = ", ".join(missing_skills[:5])
            enhanced_skills = f"{skills_content}\n{additional_skills}"

            cv = cv.replace(skills_content, enhanced_skills)

        return cv

    def _add_targeted_intro(self, cv: str, pain_points: List[Dict[str, Any]]) -> str:
        """Add a targeted introductory paragraph at the top."""
        if pain_points:
            top_pain = pain_points[0]
            # Create a brief intro referencing the top challenge
            intro = f"""## Targeted Approach

Understanding the need to {top_pain['title'].lower()}, I bring extensive experience in addressing similar challenges. My background includes:

- Proven success in {top_pain['description'][:80]}...
- Data-driven decision making with measurable outcomes
- Collaborative leadership style focused on team success

---

"""
            return intro + cv

        return cv