import pytest

from src.services.voice_chef_parser import calculate_similarity, parse_chef_command
from src.services.voice_order_parser import parse_order


class TestChefParser:
    """AI accuracy tests for French chef command parsing."""

    @pytest.mark.parametrize(
        "command,expected_type,expected_order",
        [
            ("commande 12 lance", "lance", "12"),
            ("commande 5 lancé", "lance", "5"),
            ("commande 8 lancée", "lance", "8"),
            ("lance la commande 3", "lance", "3"),
            ("commande numéro 7 lance", "lance", "7"),
        ],
    )
    def test_lance_commands(self, command, expected_type, expected_order):
        result = parse_chef_command(command)
        assert result is not None, f"Expected match for: {command}"
        assert result["type"] == expected_type
        assert result["order_number"] == expected_order
        assert result["confidence"] >= 65

    @pytest.mark.parametrize(
        "command,expected_type,expected_order",
        [
            ("commande 12 prete", "prete", "12"),
            ("commande 5 prête", "prete", "5"),
            ("commande 8 prêt", "prete", "8"),
            ("commande numéro 7 prête", "prete", "7"),
            ("prête la commande 3", "prete", "3"),
            ("commande 15 est prête", "prete", "15"),
        ],
    )
    def test_prete_commands(self, command, expected_type, expected_order):
        result = parse_chef_command(command)
        assert result is not None, f"Expected match for: {command}"
        assert result["type"] == expected_type
        assert result["order_number"] == expected_order
        assert result["confidence"] >= 65

    @pytest.mark.parametrize(
        "command",
        [
            "bonjour",
            "merci",
            "",
            "au revoir",
        ],
    )
    def test_unrelated_commands_return_none(self, command):
        result = parse_chef_command(command)
        assert result is None

    def test_similarity_calculation(self):
        assert calculate_similarity("hello", "hello") == 100
        assert calculate_similarity("abc", "xyz") < 50
        assert calculate_similarity("", "") == 100


class TestOrderParser:
    """AI accuracy tests for customer order parsing."""

    menu = [
        {"id": 1, "name": "Burger"},
        {"id": 2, "name": "Cheeseburger"},
        {"id": 3, "name": "Coca-Cola"},
        {"id": 4, "name": "French Fries"},
        {"id": 5, "name": "Salad"},
    ]

    def test_simple_order(self):
        result = parse_order("a burger", self.menu)
        assert len(result) >= 1
        item = result[0]
        assert item["menu_item_name"] == "Burger"
        assert item["quantity"] == 1
        assert item["confidence"] >= 50

    def test_order_with_quantity(self):
        result = parse_order("two burgers", self.menu)
        assert len(result) >= 1
        assert result[0]["quantity"] == 2

    def test_multiple_items(self):
        result = parse_order("a burger and a coca", self.menu)
        assert len(result) >= 2
        names = {r["menu_item_name"] for r in result}
        assert "Burger" in names

    def test_order_with_numbers(self):
        result = parse_order("3 cheeseburgers", self.menu)
        assert len(result) >= 1
        assert result[0]["quantity"] == 3

    def test_empty_text(self):
        result = parse_order("", self.menu)
        assert result == []

    def test_no_match(self):
        result = parse_order("xyzzy", self.menu)
        assert result == []
