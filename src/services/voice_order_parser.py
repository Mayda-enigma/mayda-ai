"""
Customer voice menu order parser using SequenceMatcher fuzzy comparisons.
Implements VC-006.
"""

import logging
import re
from typing import Any

from src.services.voice_chef_parser import calculate_similarity

logger = logging.getLogger(__name__)


def parse_order(text: str, menu_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Parses a user order transcript to find menu items and quantities.
    E.g. "two burgers and a coke" -> [{"menu_item_id": 1, "quantity": 2, "confidence": 100}]

    Args:
        text (str): Transcription of customer's order.
        menu_items (List[Dict]): List of available menu items, e.g., [{"id": 1, "name": "Burger"}]

    Returns:
        List[Dict]: List of parsed items with menu_item_id, quantity, and similarity confidence.
    """
    text_lower = text.lower().strip()
    logger.info("📝 Parsing customer order transcript: '%s'", text)

    # Split text by conjunction words to isolate individual item segments
    # Splitting by "and", "et", "with", "avec", ",", "+", "plus"
    split_pattern = r"\s+(?:and|et|with|avec|\+|\bplus\b)\s+|,\s*"
    segments = re.split(split_pattern, text_lower)

    number_words = {
        # English numbers
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "a": 1,
        "an": 1,
        # French numbers
        "un": 1,
        "une": 1,
        "deux": 2,
        "trois": 3,
        "quatre": 4,
        "cinq": 5,
        "six_fr": 6,
        "sept": 7,
        "huit": 8,
        "neuf": 9,
        "dix": 10,
        "le": 1,
        "la": 1,
        "des": 1,
    }

    parsed_items = []

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        logger.info("Analyzing segment: '%s'", segment)

        # 1. Detect and extract quantity
        quantity = 1  # Default to 1 if no quantity is specified

        # Check for digit patterns (e.g. "2 burgers", "burgers 3")
        digits = re.findall(r"\d+", segment)
        if digits:
            quantity = int(digits[0])
            # Strip digits out of item name candidate
            item_text = re.sub(r"\d+", "", segment).strip()
        else:
            # Check for written number words (e.g. "two burgers")
            item_words = segment.split()
            for i, word in enumerate(item_words):
                # Clean word from plural endings like 's' for language checks
                clean_word = word.rstrip("s")
                if clean_word in number_words:
                    quantity = number_words[clean_word]
                    # Remove the word from item name candidate
                    item_words.pop(i)
                    break

            item_text = " ".join(item_words)

        # Clean item text (remove plurals, double spaces, and standard stop words)
        item_text = re.sub(r"\s+", " ", item_text).strip()
        # Clean trailing plural 's' or 'x' (for French)
        item_clean = item_text.rstrip("sx")

        if not item_clean:
            continue

        # 2. Fuzzy match against menu items
        best_match = None
        best_confidence = 0

        # Tokenize the spoken item text for word-level comparisons
        item_tokens = re.split(r"[\s\-]+", item_clean)

        for menu_item in menu_items:
            item_name = menu_item["name"].lower()
            item_name_clean = item_name.rstrip("sx")

            # Full-string SequenceMatcher similarity
            similarity = calculate_similarity(item_clean, item_name_clean)

            # Substring containment boost (e.g. "burger" in "cheeseburger")
            if item_clean in item_name_clean or item_name_clean in item_clean:
                similarity = max(similarity, 85)

            # Word-level matching: split menu item name by spaces/hyphens
            # and compare each token against each spoken token.
            # This catches "coke" matching "Coca-Cola" or "nuggets" matching "Chicken Nuggets"
            menu_tokens = re.split(r"[\s\-]+", item_name_clean)
            for spoken_tok in item_tokens:
                spoken_tok_clean = spoken_tok.rstrip("sx")
                if not spoken_tok_clean:
                    continue
                for menu_tok in menu_tokens:
                    menu_tok_clean = menu_tok.rstrip("sx")
                    if not menu_tok_clean:
                        continue
                    tok_sim = calculate_similarity(spoken_tok_clean, menu_tok_clean)
                    # Substring containment at token level
                    if spoken_tok_clean in menu_tok_clean or menu_tok_clean in spoken_tok_clean:
                        tok_sim = max(tok_sim, 80)
                    # If any individual token matches strongly, boost overall similarity
                    if tok_sim >= 70:
                        similarity = max(similarity, tok_sim)

            if similarity > best_confidence:
                best_confidence = similarity
                best_match = menu_item

        # Only accept matches above similarity threshold (e.g. 50%)
        if best_match and best_confidence >= 50:
            parsed_items.append(
                {
                    "menu_item_id": best_match["id"],
                    "menu_item_name": best_match["name"],
                    "quantity": quantity,
                    "confidence": best_confidence,
                }
            )
            logger.info(
                "Matched segment '%s' -> Item '%s' (ID=%d, Qty=%d, Conf=%d%%)",
                segment,
                best_match["name"],
                best_match["id"],
                quantity,
                best_confidence,
            )
        else:
            logger.warning(
                "Could not find a reliable match for segment '%s' (Best similarity: %d%%)", segment, best_confidence
            )

    return parsed_items
