"""
French chef voice command parser logic.
Ported and refactored from mayda-ai/voice/VoiceScript.py.
"""
from difflib import SequenceMatcher
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def calculate_similarity(text1: str, text2: str) -> int:
    """Calculate text similarity percentage (0-100%)."""
    return int(SequenceMatcher(None, text1.lower(), text2.lower()).ratio() * 100)


def parse_chef_command(text: str) -> Optional[Dict[str, Any]]:
    """
    Parses French chef commands to identify order number and action type ('lance' or 'prete').
    
    Args:
        text (str): The raw transcribed command text.
        
    Returns:
        Optional[Dict]: Parser result dictionary or None if match failed.
    """
    text_lower = text.lower().strip()
    logger.info("📝 Parsing chef transcription: '%s'", text)
    
    # Extract numbers from text
    numbers = re.findall(r"\d+", text_lower)
    
    if not numbers:
        # Detect French word numbers
        number_words = {
            "un": "1", "deux": "2", "trois": "3", "quatre": "4", "cinq": "5",
            "six": "6", "sept": "7", "huit": "8", "neuf": "9", "dix": "10",
            "onze": "11", "douze": "12", "treize": "13", "quatorze": "14", "quinze": "15",
            "seize": "16", "dix-sept": "17", "dix-huit": "18", "dix-neuf": "19", "vingt": "20"
        }
        
        for word, num in number_words.items():
            if word in text_lower:
                numbers = [num]
                logger.info("📊 French word-number recognized: '%s' -> %s", word, num)
                break
                
    if not numbers:
        logger.warning("❌ No order number detected in transcription.")
        return None
        
    order_number = numbers[0]
    logger.info("📊 Extracted Order ID: %s", order_number)
    
    # Expected commands for similarity comparisons
    expected_lance_phrases = [
        f"commande {order_number} lance",
        f"commande {order_number} lancé",
        f"commande {order_number} lancée",
        f"commande numéro {order_number} lance",
        f"lance la commande {order_number}",
    ]
    
    expected_prete_phrases = [
        f"commande {order_number} prete",
        f"commande {order_number} prête",
        f"commande {order_number} prêt",
        f"commande numéro {order_number} prête",
        f"prête la commande {order_number}",
        f"commande {order_number} est prête",
    ]
    
    similarity_threshold = 65  # Slightly more relaxed threshold for vocal variations
    
    # Compare with LANCE commands
    best_lance_similarity = 0
    best_lance_phrase = ""
    for expected in expected_lance_phrases:
        sim = calculate_similarity(text_lower, expected)
        if sim > best_lance_similarity:
            best_lance_similarity = sim
            best_lance_phrase = expected
            
    # Compare with PRETE commands
    best_prete_similarity = 0
    best_prete_phrase = ""
    for expected in expected_prete_phrases:
        sim = calculate_similarity(text_lower, expected)
        if sim > best_prete_similarity:
            best_prete_similarity = sim
            best_prete_phrase = expected

    logger.info("Best Lance: %s%% ('%s') | Best Prete: %s%% ('%s')", 
                best_lance_similarity, best_lance_phrase, best_prete_similarity, best_prete_phrase)

    # Decide action type
    if best_lance_similarity >= similarity_threshold and best_lance_similarity >= best_prete_similarity:
        logger.info("✅ Parsed as LANCE (%d%% similarity)", best_lance_similarity)
        return {
            "type": "lance",
            "order_number": order_number,
            "confidence": best_lance_similarity,
            "matched_phrase": best_lance_phrase,
            "message": f"✅ Commande {order_number} - Préparation lancée! (similarité: {best_lance_similarity}%)",
        }
    elif best_prete_similarity >= similarity_threshold:
        logger.info("✅ Parsed as PRETE (%d%% similarity)", best_prete_similarity)
        return {
            "type": "prete",
            "order_number": order_number,
            "confidence": best_prete_similarity,
            "matched_phrase": best_prete_phrase,
            "message": f"🍽️ Commande {order_number} - Prête à servir! (similarité: {best_prete_similarity}%)",
        }
    
    logger.warning("❌ Command rejected due to low similarity (below %d%% threshold)", similarity_threshold)
    return None
