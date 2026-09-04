"""Subtitle cleaner with domain glossary terminology correction."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class SubtitleCleaner:
    """Clean subtitles and correct domain terminology based on glossary."""

    def __init__(
        self,
        glossary: Optional[Union[str, Path, Dict[str, Any]]] = None,
        domain: Optional[str] = "motor-control",
    ):
        """Initialize cleaner with glossary dictionary or path."""
        self.domain = domain
        self.glossary_map = self._load_glossary(glossary)
        self._compiled_patterns = self._compile_patterns(self.glossary_map)

    def _load_glossary(
        self, glossary: Optional[Union[str, Path, Dict[str, Any]]]
    ) -> Dict[str, str]:
        """Load and normalize glossary dictionary."""
        raw_data: Dict[str, Any] = {}
        if glossary is None:
            default_path = Path("config/glossary.json")
            if default_path.exists():
                with open(default_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            else:
                raw_data = {}
        elif isinstance(glossary, (str, Path)):
            with open(glossary, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        elif isinstance(glossary, dict):
            raw_data = glossary

        term_map: Dict[str, str] = {}
        if self.domain and self.domain in raw_data:
            term_map.update(raw_data[self.domain])
            if "general-tech" in raw_data and self.domain != "general-tech":
                term_map.update(raw_data["general-tech"])
        else:
            # Flatten all domain dictionaries or handle direct key-value map
            for k, v in raw_data.items():
                if isinstance(v, dict):
                    term_map.update(v)
                else:
                    term_map[k] = str(v)

        return term_map

    def _compile_patterns(
        self, term_map: Dict[str, str]
    ) -> List[Tuple[re.Pattern, str, str]]:
        """Compile regex patterns sorted by term length descending."""
        patterns = []
        # Sort terms by length descending to match longer phrases first
        sorted_terms = sorted(term_map.keys(), key=lambda x: len(x), reverse=True)

        for term in sorted_terms:
            target = term_map[term]
            escaped_term = re.escape(term)
            # If term contains space, allow flexible whitespace
            escaped_term = escaped_term.replace(r"\ ", r"\s+")

            # Check if term starts/ends with ASCII word characters for \b boundaries
            has_word_start = bool(re.match(r"^\w", term, re.ASCII))
            has_word_end = bool(re.search(r"\w$", term, re.ASCII))

            pattern_str = ""
            if has_word_start:
                pattern_str += r"\b"
            pattern_str += escaped_term
            if has_word_end:
                pattern_str += r"\b"

            pattern = re.compile(pattern_str, re.IGNORECASE)
            patterns.append((pattern, target, term))

        return patterns

    def clean_text(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Clean plain text and return cleaned text and replacement statistics."""
        if not text:
            return "", []

        cleaned_text = text
        stats_map: Dict[str, Dict[str, Any]] = {}

        for pattern, replacement, original_term in self._compiled_patterns:
            matches = list(pattern.finditer(cleaned_text))
            if matches:
                count = len(matches)
                cleaned_text = pattern.sub(replacement, cleaned_text)
                if original_term not in stats_map:
                    stats_map[original_term] = {
                        "original": original_term,
                        "replacement": replacement,
                        "count": 0,
                    }
                stats_map[original_term]["count"] += count

        return cleaned_text, list(stats_map.values())

    def clean_srt(self, srt_content: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Clean an SRT file while strictly preserving timestamps and indices."""
        if not srt_content or not srt_content.strip():
            return "", []

        # Standardize line breaks
        normalized = srt_content.replace("\r\n", "\n").replace("\r", "\n")
        raw_blocks = re.split(r"\n\s*\n", normalized.strip())

        cleaned_blocks = []
        aggregated_stats: Dict[str, Dict[str, Any]] = {}

        timestamp_pattern = re.compile(
            r"^\d{1,2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,\.]\d{3}"
        )

        for block in raw_blocks:
            lines = block.strip().split("\n")
            if not lines:
                continue

            cleaned_lines = []
            is_text_section = False

            for i, line in enumerate(lines):
                line_stripped = line.strip()
                # Check if it is an index line (e.g. "1")
                if i == 0 and line_stripped.isdigit():
                    cleaned_lines.append(line)
                    continue

                # Check if it is a timestamp line (e.g. "00:00:01,000 --> 00:00:04,000")
                if timestamp_pattern.search(line_stripped):
                    cleaned_lines.append(line)
                    is_text_section = True
                    continue

                # Subtitle text lines
                if is_text_section or (i >= 2):
                    cleaned_line, block_stats = self.clean_text(line)
                    cleaned_lines.append(cleaned_line)
                    for stat in block_stats:
                        term = stat["original"]
                        if term not in aggregated_stats:
                            aggregated_stats[term] = {
                                "original": stat["original"],
                                "replacement": stat["replacement"],
                                "count": 0,
                            }
                        aggregated_stats[term]["count"] += stat["count"]
                else:
                    # Fallback for irregular block headers
                    cleaned_lines.append(line)

            cleaned_blocks.append("\n".join(cleaned_lines))

        result_srt = "\n\n".join(cleaned_blocks) + "\n"
        return result_srt, list(aggregated_stats.values())
