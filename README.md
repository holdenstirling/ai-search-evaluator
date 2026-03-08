# AI Search Evaluator

Evaluate search result quality using Claude as a judge. Implements the LLM-as-judge evaluation pattern to systematically measure how well search systems satisfy user intent across multiple quality dimensions.

Built for teams implementing AI-powered search who need a repeatable, scalable way to measure result quality — without relying on manual human review for every query.

## The Problem

AI search systems are only as good as their results, but measuring search quality is hard. Traditional approaches rely on manual human evaluation (expensive, slow, inconsistent) or simple metrics like click-through rate (lagging, noisy). Teams building AI search need a way to systematically evaluate result quality during development, catch regressions before deployment, and compare different search configurations.

## The Solution

This evaluator uses Claude as a calibrated judge to score search results across 6 quality dimensions. It supports single-query evaluation, full test suite runs, and head-to-head comparison between two search systems.

## Features

- **Single query evaluation** — Score any set of search results against defined expectations
- **Head-to-head comparison** — Compare two search systems on the same queries
- **Test suite runner** — Run batches of test cases with category breakdowns
- **6 quality dimensions** — Relevance, completeness, local accuracy, intent match, freshness, actionability
- **Pre-built test suites** — Includes a local search quality suite with 10 real-world test cases
- **Structured reports** — JSON reports with per-query scores and recommendations
- **Extensible** — Define custom test suites in JSON or build programmatically

## Quick Start
```bash
git clone https://github.com/holdenstirling/ai-search-evaluator.git
cd ai-search-evaluator
pip3 install -r requirements.txt
export ANTHROPIC_API_KEY='your-key-here'
python3 examples/demo.py
```

## Usage

### Evaluate search results for a single query
```python
from src.evaluator import SearchEvaluator
from src.test_suite import TestCase

evaluator = SearchEvaluator(api_key="your-key")

test_case = TestCase(
    query="physical therapy near downtown Denver",
    expected_results=["Nearby PT clinics", "Ratings", "Insurance info"],
    expected_intent="Find a physical therapy provider near downtown",
    category="local_discovery",
    location_context="Denver, CO"
)

search_results = [
    {"title": "Summit PT - Denver", "snippet": "Expert PT in downtown Denver...", "url": "https://..."},
    {"title": "Denver PT & Wellness", "snippet": "Comprehensive PT services...", "url": "https://..."},
]

result = evaluator.evaluate_query(test_case, search_results)
print(f"Overall score: {result['overall_score']}/10")
```

### Compare two search systems
```python
comparison = evaluator.compare_systems(
    test_case=test_case,
    results_a=system_a_results,
    results_b=system_b_results
)
print(f"Winner: System {comparison['winner']}")
```

### Create custom test suites
```python
from src.test_suite import TestSuite

suite = TestSuite("My Search Tests")
suite.add_cases([
    {
        "query": "best coffee shop with wifi downtown",
        "expected_results": ["Coffee shops with wifi", "Downtown locations"],
        "expected_intent": "Find a coffee shop to work from",
        "category": "local_filtered",
        "location_context": "Denver, CO",
    },
])
suite.to_json("my_suite.json")
```

## Evaluation Dimensions

| Dimension | What It Measures |
|---|---|
| **Relevance** | Do results match what the user is looking for? |
| **Completeness** | Are all expected result types present? |
| **Local Accuracy** | Are results actually in/near the specified location? |
| **Intent Match** | Do results align with the user's underlying goal? |
| **Freshness** | Is information current and up to date? |
| **Actionability** | Can the user take immediate action from the results? |

## Architecture
```
src/
  evaluator.py       # SearchEvaluator - Claude as judge for search quality
  test_suite.py      # TestSuite and TestCase - define evaluation criteria
examples/
  demo.py            # Interactive demo with sample evaluations and comparisons
```

### The LLM-as-Judge Pattern

1. **Define expectations** — Each test case specifies what good results look like
2. **Capture actual results** — Results collected from the system under test
3. **Judge with LLM** — Claude evaluates actual vs expected across calibrated dimensions
4. **Aggregate and report** — Scores roll up into category and suite-level metrics

This is the same pattern used by teams at companies building AI search and retrieval systems.

## Why This Exists

After years of implementing AI search for enterprise clients at [Arc4](https://arc4.com), I found that the hardest part is not building the search — it is measuring whether it is actually good. Most teams eyeball results manually or wait for user complaints. This evaluator brings structure and repeatability to search quality measurement.

## License

MIT

## Author

**Holden Ottolini** — [LinkedIn](https://linkedin.com/in/holden-stirling-ottolini) | [GitHub](https://github.com/holdenstirling)

Solutions Architect and Co-Founder at Arc4. 10+ years building and evaluating enterprise search systems for multi-location brands.
