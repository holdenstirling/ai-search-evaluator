"""
Test Suite - Define evaluation test cases for AI search quality.

A TestCase represents a single search query with expected results,
and a TestSuite is a collection of test cases that can be loaded
from JSON or constructed programmatically.

Author: Holden Ottolini (holdenstirling)
"""

import json
import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """
    A single search evaluation test case.
    
    Attributes:
        query: The search query to evaluate
        expected_results: List of results that should appear (titles, URLs, or key phrases)
        expected_intent: What the user is trying to accomplish
        category: Test category for grouping (e.g., "navigational", "informational", "transactional")
        location_context: Optional location for local search queries
        priority: Importance weighting (1-5, default 3)
        tags: Optional tags for filtering test cases
    """
    query: str
    expected_results: list = field(default_factory=list)
    expected_intent: str = ""
    category: str = "general"
    location_context: str = ""
    priority: int = 3
    tags: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class TestSuite:
    """
    A collection of test cases for evaluating search quality.
    
    Usage:
        suite = TestSuite("Local Search Tests")
        suite.add_case(TestCase(
            query="best pizza near downtown Denver",
            expected_results=["Joe's Pizza", "Marco's Pizzeria"],
            expected_intent="Find highly-rated pizza restaurants nearby",
            category="local",
            location_context="Denver, CO"
        ))
        
        # Or load from JSON
        suite = TestSuite.from_json("test_cases.json")
    """

    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.cases = []

    def add_case(self, test_case):
        """Add a test case to the suite."""
        if not isinstance(test_case, TestCase):
            test_case = TestCase.from_dict(test_case)
        self.cases.append(test_case)
        return self

    def add_cases(self, cases):
        """Add multiple test cases."""
        for case in cases:
            self.add_case(case)
        return self

    def filter_by_category(self, category):
        """Return test cases matching a category."""
        return [c for c in self.cases if c.category == category]

    def filter_by_tag(self, tag):
        """Return test cases with a specific tag."""
        return [c for c in self.cases if tag in c.tags]

    def filter_by_priority(self, min_priority=1, max_priority=5):
        """Return test cases within a priority range."""
        return [c for c in self.cases if min_priority <= c.priority <= max_priority]

    def get_categories(self):
        """Return all unique categories in the suite."""
        return list(set(c.category for c in self.cases))

    def summary(self):
        """Return a summary of the test suite."""
        categories = {}
        for c in self.cases:
            categories[c.category] = categories.get(c.category, 0) + 1
        return {
            "name": self.name,
            "description": self.description,
            "total_cases": len(self.cases),
            "categories": categories,
            "avg_priority": round(sum(c.priority for c in self.cases) / max(len(self.cases), 1), 1),
        }

    def to_json(self, filepath):
        """Save the test suite to a JSON file."""
        data = {
            "name": self.name,
            "description": self.description,
            "cases": [c.to_dict() for c in self.cases],
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(self.cases)} test cases to {filepath}")

    @classmethod
    def from_json(cls, filepath):
        """Load a test suite from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        suite = cls(name=data.get("name", ""), description=data.get("description", ""))
        for case_data in data.get("cases", []):
            suite.add_case(TestCase.from_dict(case_data))
        logger.info(f"Loaded {len(suite.cases)} test cases from {filepath}")
        return suite

    @classmethod
    def create_local_search_suite(cls):
        """Create a pre-built test suite for evaluating local search quality."""
        suite = cls(
            name="Local Search Quality",
            description="Evaluates search result quality for common local business queries across multiple categories and intents."
        )
        suite.add_cases([
            {
                "query": "physical therapy near me",
                "expected_results": ["Nearby PT clinics with addresses", "Ratings and reviews", "Insurance information", "Specialties offered"],
                "expected_intent": "Find a physical therapy provider close to the user's location",
                "category": "local_discovery",
                "location_context": "Denver, CO",
                "priority": 5,
                "tags": ["healthcare", "near_me", "high_intent"],
            },
            {
                "query": "best dentist downtown Denver",
                "expected_results": ["Dental practices in downtown Denver", "Patient ratings", "Services offered", "Accepting new patients status"],
                "expected_intent": "Find a highly-rated dentist in a specific area",
                "category": "local_discovery",
                "location_context": "Denver, CO",
                "priority": 5,
                "tags": ["healthcare", "best_of", "location_specific"],
            },
            {
                "query": "Summit Physical Therapy Denver hours",
                "expected_results": ["Business hours for Denver location", "Address", "Phone number", "Holiday hours if applicable"],
                "expected_intent": "Find operating hours for a specific business location",
                "category": "navigational",
                "location_context": "Denver, CO",
                "priority": 4,
                "tags": ["hours", "specific_business", "navigational"],
            },
            {
                "query": "does Summit Physical Therapy accept Blue Cross",
                "expected_results": ["Insurance acceptance information", "Blue Cross specific details", "Contact for verification"],
                "expected_intent": "Verify insurance coverage at a specific provider",
                "category": "informational",
                "location_context": "Denver, CO",
                "priority": 4,
                "tags": ["insurance", "specific_business", "pre_visit"],
            },
            {
                "query": "sports injury rehab Boulder Colorado",
                "expected_results": ["Sports rehabilitation providers in Boulder", "Specialization details", "Athletic-focused services"],
                "expected_intent": "Find sports-specialized physical therapy in Boulder",
                "category": "local_discovery",
                "location_context": "Boulder, CO",
                "priority": 4,
                "tags": ["healthcare", "specialty", "location_specific"],
            },
            {
                "query": "pizza restaurant with outdoor seating Capitol Hill Denver",
                "expected_results": ["Pizza places in Capitol Hill", "Outdoor seating availability", "Specific neighborhood results"],
                "expected_intent": "Find a pizza restaurant with specific amenities in a specific neighborhood",
                "category": "local_filtered",
                "location_context": "Denver, CO",
                "priority": 3,
                "tags": ["restaurant", "amenity_filter", "neighborhood"],
            },
            {
                "query": "emergency plumber available now Denver",
                "expected_results": ["24/7 plumbers", "Emergency service availability", "Phone numbers for immediate contact"],
                "expected_intent": "Find an immediately available emergency service provider",
                "category": "urgent_local",
                "location_context": "Denver, CO",
                "priority": 5,
                "tags": ["emergency", "immediate_need", "service"],
            },
            {
                "query": "compare auto repair shops in Lakewood CO",
                "expected_results": ["Multiple auto repair shops", "Ratings comparison", "Price ranges", "Specialties"],
                "expected_intent": "Compare options before choosing an auto repair provider",
                "category": "comparison",
                "location_context": "Lakewood, CO",
                "priority": 3,
                "tags": ["automotive", "comparison", "research"],
            },
            {
                "query": "yoga studio first class free Denver",
                "expected_results": ["Studios offering free first class", "Promotional offers", "Class schedules"],
                "expected_intent": "Find a yoga studio with a free trial offer",
                "category": "transactional",
                "location_context": "Denver, CO",
                "priority": 3,
                "tags": ["fitness", "promotion", "trial"],
            },
            {
                "query": "how to choose a good physical therapist",
                "expected_results": ["Selection criteria", "What to look for", "Credentials to verify", "Questions to ask"],
                "expected_intent": "Learn how to evaluate and select a physical therapist",
                "category": "educational",
                "priority": 2,
                "tags": ["healthcare", "educational", "pre_purchase"],
            },
        ])
        return suite

    def __len__(self):
        return len(self.cases)

    def __repr__(self):
        return f"TestSuite(name='{self.name}', cases={len(self.cases)})"
