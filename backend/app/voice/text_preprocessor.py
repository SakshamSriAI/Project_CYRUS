"""CYRUS Natural Speech Text Preprocessor.

Prepares text for the Kokoro TTS engine:
1. Strips markdown tags, code block wrappers, and URLs.
2. Expands technical abbreviations and acronyms for natural human pronunciation.
3. Segments long sentences into conversational breathing chunks.
4. Inserts micro-pauses for articulate, expressive pacing.
"""

import re
from typing import List

# Technical abbreviations mapped to natural spoken equivalents
PRONUNCIATION_DICTIONARY = {
    r"\bAPI\b": "A P I",
    r"\bAPIs\b": "A P Eyes",
    r"\bSQL\b": "S Q L",
    r"\bSQLite\b": "S Q L lite",
    r"\bWAL\b": "W A L",
    r"\bRAM\b": "R A M",
    r"\bCPU\b": "C P U",
    r"\bGPU\b": "G P U",
    r"\bPID\b": "P I D",
    r"\bPIDs\b": "P I Dees",
    r"\bUI\b": "U I",
    r"\bCLI\b": "C L I",
    r"\bOS\b": "O S",
    r"\bTTS\b": "T T S",
    r"\bSTT\b": "S T T",
    r"\bLLM\b": "L L M",
    r"\bLLMs\b": "L L Emms",
    r"\bJSON\b": "Jay-sawn",
    r"\bHTML\b": "H T M L",
    r"\bCSS\b": "C S S",
    r"\bREST\b": "Rest",
    r"\bCRUD\b": "Crud",
    r"\bGB\b": "gigabytes",
    r"\bMB\b": "megabytes",
    r"\bKB\b": "kilobytes",
    r"\bms\b": "milliseconds",
    r"\bsec\b": "seconds",
    r"\bGitHub\b": "Git Hub",
    r"\bmacOS\b": "Mac O S",
    r"\bB\.Tech\b": "B Tech",
    r"\bCYRUS\b": "Cyrus",
    r"\bvs\b": "versus",
    r"\be\.g\.\b": "for example",
    r"\bi\.e\.\b": "that is",
    r"\betc\.\b": "etcetera",
}


class TextPreprocessor:
    """Prepares raw LLM response text for human-like neural speech synthesis."""

    def clean_markdown_and_code(self, text: str) -> str:
        """Removes code blocks, markdown symbols, and technical formatting."""
        # 1. Replace multi-line code blocks with brief spoken summaries
        clean = re.sub(r"```[\w]*\n[\s\S]*?\n```", ", code block omitted for speech, ", text)

        # 2. Replace inline code `code`
        clean = re.sub(r"`([^`]+)`", r"\1", clean)

        # 3. Strip markdown links [text](url) -> text
        clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean)

        # 4. Strip markdown bold / italics (*, **, _, __)
        clean = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", clean)

        # 5. Strip heading hashes and bullets
        clean = re.sub(r"^#{1,6}\s*", "", clean, flags=re.MULTILINE)
        clean = re.sub(r"^\s*[-*•]\s*", "", clean, flags=re.MULTILINE)

        # 6. Normalize multiple newlines and spaces
        clean = re.sub(r"\n+", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def apply_pronunciation_rules(self, text: str) -> str:
        """Substitutes technical terms with their phonetic spoken representation."""
        processed = text
        for pattern, replacement in PRONUNCIATION_DICTIONARY.items():
            processed = re.sub(pattern, replacement, processed)
        return processed

    def segment_for_conversational_cadence(self, text: str, max_chunk_chars: int = 180) -> List[str]:
        """Segments text into natural sentence and clause units for expressive Kokoro speech."""
        # Split on sentence boundaries (. ! ?) and major clause breaks (;, :)
        raw_sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: List[str] = []

        for sentence in raw_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(sentence) <= max_chunk_chars:
                chunks.append(sentence)
            else:
                # Break long sentence at commas or pauses
                sub_parts = re.split(r"(?<=[,;])\s+", sentence)
                current_chunk = ""
                for part in sub_parts:
                    if len(current_chunk) + len(part) < max_chunk_chars:
                        current_chunk = f"{current_chunk} {part}".strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = part
                if current_chunk:
                    chunks.append(current_chunk)

        return chunks

    def segment_text(self, text: str, max_chunk_chars: int = 180) -> List[str]:
        """Alias for segment_for_conversational_cadence."""
        return self.segment_for_conversational_cadence(text, max_chunk_chars)

    def prepare_for_synthesis(self, raw_text: str) -> str:
        """Full preparation pipeline: returns clean, phonetically accurate text."""
        clean = self.clean_markdown_and_code(raw_text)
        phonetic = self.apply_pronunciation_rules(clean)
        return phonetic


text_preprocessor = TextPreprocessor()
