"""
AI Search Evaluator - Core Module

Uses Claude as a judge to evaluate search result quality across
multiple dimensions. Implements the LLM-as-judge evaluation pattern
used in production AI systems.

Author: Holden Ottolini (holdenstirling)
"""

import json
import time
import logging
from anthropic import Anthropic
from .test_suite import TestCase, TestSuite

logger = logging.getLogger(__name__)

JUDGE_SYSTEM_PROMPT = """You are an expert search quality evaluator. Your job is to assess how well search results satisfy user intent across multiple quality dimensions.

You evaluate with precision and consistency. Your scores are calibrated:
- 9-10: Exceptional, best-in-class results
- 7-8: Good, meets expectations with minor gaps
- 5-6: Acceptable but notable room for improvement
- 3-4: Below expectations, significant gaps
- 1-2: Poor, fails to meet basic user needs

You always respond in valid JSON format as specified."""

EVALUATE_RESULTS_PROMPT = """Evaluate the following search results for the given query and context.

**Query:** {query}
**User Intent:** {expected_intent}
**Location Context:** {location_context}
**Expected Results Should Include:** {expected_results}

**Actual Search Results:**
{search_results}

Score each dimension from 1-10 with specific evidence-based feedback. Return ONLY valid JSON:
{{
  "scores": {{
    "relevance": {{
      "score": 0,
      "feedback": "Do results match what the user is looking for? Are top results the most relevant?"
    }},
    "completeness": {{
      "score": 0,
      "feedback": "Are all expected result types present? Is key information missing?"
    }},
    "local_accuracy": {{
      "score": 0,
      "feedback": "Are results actually in/near the specified location? Are addresses correct?"
    }},
    "intent_match": {{
      "score": 0,
      "feedback": "Do results align with the user's underlying goal, not just keywords?"
    }},
    "freshness": {{
      "score": 0,
      "feedback": "Is information current? Are business hours, status, offerings up to date?"
    }},
    "actionability": {{
      "score": 0,
      "feedback": "Can the user take immediate action? Are phone numbers, links, CTAs present?"
    }}
  }},
  "overall_score": 0,
  "result_ranking_assessment": "Are the results in the right order? Should any be ranked higher/lower?",
  "missing_results": ["Important result types or information that should appear but don't"],
  "false_positives": ["Results that appeared but shouldn't have or are misleading"],
  "recommendations": ["Specific improvement 1", "Specific improvement 2", "Specific improvement 3"]
}}

IMPORTANT: Return ONLY the JSON object. No markdown, no code fences."""

COMPARE_PROMPT = """Compare search results from two different systems for the same query.

**Query:** {query}
**User Intent:** {expected_intent}
**Location Context:** {location_context}

**System A Results:**
{results_a}

**System B Results:**
{results_b}

Compare the two systems and return ONLY valid JSON:
{{
  "winner": "A or B or tie",
  "system_a_score": 0,
  "system_b_score": 0,
  "comparison": {{
    "relevance": {{"winner": "A/B/tie", "reasoning": "..."}},
    "completeness": {{"winner": "A/B/tie", "reasoning": "..."}},
    "local_accuracy": {{"winner": "A/B/tie", "reasoning": "..."}},
    "actionability": {{"winner": "A/B/tie", "reasoning": "..."}}
  }},
  "key_differences": ["difference 1", "difference 2"],
  "recommendations": ["What the losing system should improve"]
}}

IMPORTANT: Return ONLY the JSON object. No markdown, no code fences."""


class SearchEvaluator:
    """
    Evaluates search result quality using Claude as a judge.

    Implements the LLM-as-judge pattern for systematically measuring
    search quality across multiple dimensions. Supports evaluating
    individual queries, running full test suites, and comparing
    two search systems head-to-head.

    Usage:
        evaluator = SearchEvaluator(api_key="your-key")

        # Evaluate a single query's results
        result = evaluator.evaluate_query(
            test_case=TestCase(query="dentist Denver", ...),
            search_results=[{"title": "...", "snippet": "..."}]
        )

        # Run a full test suite
        report = evaluator.run_suite(suite, search_results_map)

        # Compare two search systems
        comparison = evaluator.compare_systems(test_case, results_a, results_b)
    """

    def __init__(self, api_key, model="claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.stats = {
            "evaluations_run": 0,
            "comparisons_run": 0,
            "total_tokens": 0,
            "total_time": 0,
        }

    def evaluate_query(self, test_case, search_results):
        """
        Evaluate search results for a single query.

        Args:
            test_case: TestCase with query, expected results, and context
            search_results: List of result dicts with 'title', 'snippet', 'url' keys

        Returns:
            Dict with scores across 6 dimensions and recommendations
        """
        if isinstance(test_case, dict):
            test_case = TestCase.from_dict(test_case)

        results_text = self._format_results(search_results)

        prompt = EVALUATE_RESULTS_PROMPT.format(
            query=test_case.query,
            expected_intent=test_case.expected_intent or "General search",
            location_context=test_case.location_context or "Not specified",
            expected_results=json.dumps(test_case.expected_results),
            search_results=results_text,
        )

        evaluation = self._call_claude(prompt)

        if evaluation:
            evaluation["query"] = test_case.query
            evaluation["category"] = test_case.category
            evaluation["priority"] = test_case.priority
            self.stats["evaluations_run"] += 1

        return evaluation

    def compare_systems(self, test_case, results_a, results_b):
        """
        Compare results from two search systems for the same query.

        Args:
            test_case: TestCase defining the query and expectations
            results_a: Search results from system A
            results_b: Search results from system B

        Returns:
            Dict with winner, per-dimension comparison, and recommendations
        """
        if isinstance(test_case, dict):
            test_case = TestCase.from_dict(test_case)

        prompt = COMPARE_PROMPT.format(
            query=test_case.query,
            expected_intent=test_case.expected_intent or "General search",
            location_context=test_case.location_context or "Not specified",
            results_a=self._format_results(results_a),
            results_b=self._format_results(results_b),
        )

        comparison = self._call_claude(prompt)

        if comparison:
            comparison["query"] = test_case.query
            self.stats["comparisons_run"] += 1

        return comparison

    def run_suite(self, suite, search_results_map):
        """
        Run evaluation across an entire test suite.

        Args:
            suite: TestSuite containing test cases
            search_results_map: Dict mapping query strings to search result lists
                e.g., {"dentist Denver": [{"title": "...", ...}]}

        Returns:
            Dict with per-query results, category breakdowns, and overall scores
        """
        results = []
        total = len(suite.cases)

        print(f"\n  Running {total} test cases from '{suite.name}'...\n")

        for i, case in enumerate(suite.cases, 1):
            search_results = search_results_map.get(case.query, [])

            if not search_results:
                print(f"  [{i}/{total}] SKIP: No results provided for '{case.query}'")
                results.append({
                    "query": case.query,
                    "category": case.category,
                    "skipped": True,
                    "reason": "No search results provided",
                })
                continue

            print(f"  [{i}/{total}] Evaluating: '{case.query}'...")
            evaluation = self.evaluate_query(case, search_results)
            results.append(evaluation)

            if i < total:
                time.sleep(0.5)

        report = self._build_report(suite, results)
        return report

    def _build_report(self, suite, results):
        """Build a comprehensive evaluation report from individual results."""
        evaluated = [r for r in results if not r.get("skipped")]
        skipped = [r for r in results if r.get("skipped")]

        if not evaluated:
            return {
                "suite": suite.name,
                "total_cases": len(results),
                "evaluated": 0,
                "skipped": len(skipped),
                "message": "No test cases had search results to evaluate",
            }

        all_scores = {}
        dimensions = ["relevance", "completeness", "local_accuracy", "intent_match", "freshness", "actionability"]

        for dim in dimensions:
            scores = []
            for r in evaluated:
                s = r.get("scores", {}).get(dim, {})
                if isinstance(s, dict) and "score" in s:
                    scores.append(s["score"])
            if scores:
                all_scores[dim] = {
                    "avg": round(sum(scores) / len(scores), 1),
                    "min": min(scores),
                    "max": max(scores),
                    "count": len(scores),
                }

        overall_scores = [r.get("overall_score", 0) for r in evaluated if r.get("overall_score")]
        overall_avg = round(sum(overall_scores) / max(len(overall_scores), 1), 1)

        category_scores = {}
        for r in evaluated:
            cat = r.get("category", "general")
            if cat not in category_scores:
                category_scores[cat] = []
            if r.get("overall_score"):
                category_scores[cat].append(r["overall_score"])

        category_summary = {}
        for cat, scores in category_scores.items():
            category_summary[cat] = {
                "avg_score": round(sum(scores) / len(scores), 1),
                "count": len(scores),
                "min": min(scores),
                "max": max(scores),
            }

        all_recommendations = []
        all_missing = []
        for r in evaluated:
            all_recommendations.extend(r.get("recommendations", []))
            all_missing.extend(r.get("missing_results", []))

        return {
            "suite_name": suite.name,
            "summary": {
                "total_cases": len(results),
                "evaluated": len(evaluated),
                "skipped": len(skipped),
                "overall_avg_score": overall_avg,
            },
            "dimension_scores": all_scores,
            "category_breakdown": category_summary,
            "individual_results": results,
            "top_recommendations": list(set(all_recommendations))[:10],
            "commonly_missing": list(set(all_missing))[:10],
            "metadata": {
                "model": self.model,
                "stats": self.get_stats(),
            },
        }

    def _format_results(self, results):
        """Format search results for inclusion in a prompt."""
        if not results:
            return "(No results returned)"

        formatted = []
        for i, r in enumerate(results, 1):
            if isinstance(r, str):
                formatted.append(f"  {i}. {r}")
            elif isinstance(r, dict):
                title = r.get("title", "Untitled")
                snippet = r.get("snippet", r.get("description", ""))
                url = r.get("url", "")
                entry = f"  {i}. {title}"
                if url:
                    entry += f"\n     URL: {url}"
                if snippet:
                    entry += f"\n     {snippet}"
                formatted.append(entry)
        return "\n\n".join(formatted)

    def _call_claude(self, prompt):
        """Make a Claude API call and parse the JSON response."""
        start = time.time()

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=JUDGE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {"error": str(e)}

        elapsed = time.time() - start
        tokens = response.usage.input_tokens + response.usage.output_tokens
        self.stats["total_tokens"] += tokens
        self.stats["total_time"] += elapsed

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {e}")
            return {"error": f"JSON parse error: {e}", "raw": raw}

    def get_stats(self):
        return {
            **self.stats,
            "avg_eval_time": round(
                self.stats["total_time"] / max(self.stats["evaluations_run"] + self.stats["comparisons_run"], 1), 2
            ),
        }
