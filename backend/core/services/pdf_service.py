# backend/core/services/pdf_service.py
import fitz  # PyMuPDF
import re
import logging
from typing import List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QuestionMatch:
    question_id: int
    question_text: str
    confidence: float

class QuestionExtractor:
    """Enhanced question extraction with multiple pattern matching strategies"""
    
    # Common question patterns with named groups
    PATTERNS = [
        # Standard question formats
        r'(?:^|\n)(?P<marker>Q|Question)[\s.]?(?P<id>\d+)[.:\s]+(?P<text>.*?)(?=(?:\n(?:Q|Question)[\s.]?\d+)|$)',
        
        # Numbered format
        r'(?:^|\n)(?P<id>\d+)[.:\s]+(?P<text>.*?)(?=(?:\n\d+[.:\s]+)|$)',
        
        # Bracketed format
        r'(?:^|\n)\[(?P<marker>Q\.?)?(?P<id>\d+)\][.:\s]+(?P<text>.*?)(?=(?:\n\[(?:Q\.?)?\d+\])|$)',
        
        # Problem/Exercise format
        r'(?:^|\n)(?P<marker>Problem|Exercise)[\s.]?(?P<id>\d+)[.:\s]+(?P<text>.*?)(?=(?:\n(?:Problem|Exercise)[\s.]?\d+)|$)'
    ]

    # Noise patterns to clean
    NOISE_PATTERNS = [
        r'Here is the answer to the question.*',
        r'I hope this helps!',
        r'Let me know if you have any further questions.*',
        r'In summary,.*',
        r'The following are key points.*',
        r'Please note that.*',
        r'Answer in HTML format:',
        r'know if you need any changes.*'
    ]

    @staticmethod
    def extract_questions(pdf_path: str) -> List[Dict[str, str]]:
        """Main entry point for question extraction"""
        try:
            # Extract raw text with improved formatting
            text_blocks = QuestionExtractor._extract_text_blocks(pdf_path)
            
            # Clean and normalize text
            cleaned_text = QuestionExtractor._clean_text(text_blocks)
            
            # Extract questions using multiple patterns
            questions = QuestionExtractor._extract_with_confidence(cleaned_text)
            
            # Post-process and validate questions
            validated_questions = QuestionExtractor._post_process_questions(questions)
            
            return validated_questions

        except Exception as e:
            logger.error(f"Question extraction failed: {str(e)}")
            raise

    @staticmethod
    def _extract_text_blocks(pdf_path: str) -> str:
        """Extract text while preserving structure"""
        doc = fitz.open(pdf_path)
        text_blocks = []
        
        for page in doc:
            # Get blocks with their bounding boxes and text
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_blocks.append(span["text"])
                            
                            # Preserve natural line breaks
                            if span.get("flags", 0) & 2**0:  # Check for hardline break
                                text_blocks.append("\n")
        
        return " ".join(text_blocks)

    @staticmethod
    def _clean_text(text: str) -> str:
        """Enhanced text cleaning with noise removal"""
        # Remove noise patterns
        for pattern in QuestionExtractor.NOISE_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Normalize question markers
        text = re.sub(r'Q\s*\.\s*', 'Q.', text)
        text = re.sub(r'Question\s+', 'Question ', text)
        
        # Remove unwanted characters while preserving essential punctuation
        text = re.sub(r'[^\w\s\n.?,:;()\[\]-]', '', text)
        
        return text.strip()

    @staticmethod
    def _extract_with_confidence(text: str) -> List[QuestionMatch]:
        """Extract questions with confidence scoring"""
        question_matches = []
        seen_questions = set()
        
        for pattern in QuestionExtractor.PATTERNS:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                q_id = int(match.group('id'))
                q_text = match.group('text').strip()
                
                # Skip if we've seen this question ID with better confidence
                if q_id in seen_questions:
                    continue
                
                # Calculate confidence based on various factors
                confidence = QuestionExtractor._calculate_confidence(q_text, match)
                
                if confidence > 0.5:  # Minimum confidence threshold
                    question_matches.append(QuestionMatch(
                        question_id=q_id,
                        question_text=q_text,
                        confidence=confidence
                    ))
                    seen_questions.add(q_id)
        
        return sorted(question_matches, key=lambda x: x.question_id)

    @staticmethod
    def _calculate_confidence(text: str, match: re.Match) -> float:
        """Calculate confidence score for a question match"""
        confidence = 1.0
        
        # Length-based confidence
        if len(text) < 10:
            confidence *= 0.5
        elif len(text) > 500:
            confidence *= 0.8
            
        # Pattern-based confidence
        if match.group('marker'):
            confidence *= 1.2
            
        # Question mark presence
        if '?' in text:
            confidence *= 1.1
            
        # Structural indicators
        if re.search(r'^[A-Z]', text):  # Starts with capital letter
            confidence
            
        return min(confidence, 1.0)  # Cap at 1.0

    @staticmethod
    def _post_process_questions(matches: List[QuestionMatch]) -> List[Dict[str, str]]:
        """Convert matches to final format with validation"""
        processed_questions = []
        
        for match in matches:
            # Final cleaning of question text
            cleaned_text = QuestionExtractor._final_clean(match.question_text)
            
            if cleaned_text:  # Only include non-empty questions
                processed_questions.append({
                    'question_id': match.question_id,
                    'question': cleaned_text
                })
        
        return processed_questions

    @staticmethod
    def _final_clean(text: str) -> str:
        """Final cleaning pass for question text"""
        # Remove any remaining noise
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Ensure proper ending punctuation
        if text and not text[-1] in '.?':
            text += '.'
            
        return text
