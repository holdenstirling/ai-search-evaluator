#!/usr/bin/env python3
"""
AI Search Evaluator - Demo
Author: Holden Ottolini (holdenstirling)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluator import SearchEvaluator
from src.test_suite import TestSuite, TestCase


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  AI SEARCH EVALUATOR - DEMO")
    print("=" * 60)

    evaluator = SearchEvaluator(api_key=api_key)

    print(f"\n{'=' * 60}")
    print("  Demo 1: Single Query Evaluation")
    print(f"{'=' * 60}")

    test_case = TestCase(
        query="physical therapy near downtown Denver",
        expected_results=["Nearby PT clinics with addresses", "Ratings and reviews", "Insurance information", "Specialties like sports rehab"],
        expected_intent="Find a physical therapy provider close to downtown Denver",
        category="local_discovery",
        location_context="Denver, CO",
        priority=5,
    )

    sample_results = [
        {"title": "Summit Physical Therapy - Denver", "url": "https://summitpt.com/denver", "snippet": "Expert physical therapy in downtown Denver. Sports rehab, post-surgical recovery, chronic pain. Same-day appointments. In-network with most insurers. (303) 555-0142"},
        {"title": "Denver Physical Therapy & Wellness", "url": "https://denverptwell.com", "snippet": "Comprehensive PT services in the heart of Denver. Specializing in manual therapy and dry needling. Accepting new patients. Call (303) 555-0199."},
        {"title": "Colorado Sports Rehab Center", "url": "https://cosportsrehab.com", "snippet": "Located in Aurora, CO. Premier sports rehabilitation facility serving the Denver metro area. Free injury screenings available."},
        {"title": "What Is Physical Therapy? - WebMD", "url": "https://webmd.com/physical-therapy", "snippet": "Physical therapy is a treatment method that focuses on the science of movement. Learn about types, conditions treated, and what to expect."},
        {"title": "Rocky Mountain Physical Therapy - Boulder", "url": "https://rockymtnpt.com/boulder", "snippet": "Boulder's top-rated physical therapy clinic. Serving Boulder County since 2005. Specializing in hiking and climbing injuries."},
    ]

    print(f"\n  Query: '{test_case.query}'")
    print(f"  Results to evaluate: {len(sample_results)}")
    print(f"  Evaluating...\n")

    result = evaluator.evaluate_query(test_case, sample_results)

    if "error" in result:
        print(f"  Error: {result['error']}")
    else:
        scores = result.get("scores", {})
        print(f"  Quality Scores:")
        for dim, data in scores.items():
            if isinstance(data, dict):
                score = data.get("score", 0)
                if isinstance(score, float):
                    score = int(round(score))
                feedback = data.get("feedback", "")[:70]
                bar = "=" * score + "-" * (10 - score)
                print(f"     {dim.replace('_', ' ').title():.<22} [{bar}] {score}/10")
                print(f"       {feedback}...")

        overall = result.get("overall_score", 0)
        if isinstance(overall, float):
            overall = int(round(overall))
        print(f"\n     {'Overall':.<22} [{'=' * overall}{'-' * (10 - overall)}] {overall}/10")

        recs = result.get("recommendations", [])
        if recs:
            print(f"\n  Recommendations:")
            for r in recs:
                print(f"     -> {r}")

    print(f"\n{'=' * 60}")
    print("  Demo 2: Head-to-Head System Comparison")
    print(f"{'=' * 60}")

    compare_case = TestCase(
        query="emergency dentist Denver open now",
        expected_results=["24/7 dental clinics", "Emergency contact numbers", "Current availability"],
        expected_intent="Find a dentist available for an emergency visit right now",
        category="urgent_local",
        location_context="Denver, CO",
    )

    system_a = [
        {"title": "Emergency Dental Care Denver - Open 24/7", "url": "https://denveremergencydental.com", "snippet": "Immediate emergency dental care. Walk-ins welcome. Open 24 hours. Call now: (303) 555-0911."},
        {"title": "Bright Smile Dental - Denver", "url": "https://brightsmile.com/denver", "snippet": "General and cosmetic dentistry. Open Monday-Friday 8am-5pm."},
        {"title": "What To Do In A Dental Emergency - Healthline", "url": "https://healthline.com/dental-emergency", "snippet": "A dental emergency can be scary. Here is what to do."},
    ]

    system_b = [
        {"title": "Denver Emergency Dentists - Open Tonight", "url": "https://emergencydentistsdenver.com", "snippet": "Find emergency dentists in Denver open right now. Same-day appointments. (303) 555-0333."},
        {"title": "Urgent Dental Care of Colorado - Downtown", "url": "https://urgentdentalco.com", "snippet": "Downtown Denver emergency dental. Open until 10pm weekdays, 8pm weekends. No appointment needed."},
        {"title": "Mile High Emergency Dental", "url": "https://milehighemergencydental.com", "snippet": "Emergency extractions, pain relief, broken tooth repair. Open 7am-11pm daily. (303) 555-0777."},
    ]

    print(f"\n  Query: '{compare_case.query}'")
    print(f"  Comparing System A vs System B...")
    print(f"  Evaluating...\n")

    comparison = evaluator.compare_systems(compare_case, system_a, system_b)

    if "error" in comparison:
        print(f"  Error: {comparison['error']}")
    else:
        winner = comparison.get("winner", "?")
        score_a = comparison.get("system_a_score", 0)
        score_b = comparison.get("system_b_score", 0)
        print(f"  Winner: System {winner}")
        print(f"  System A Score: {score_a}/10")
        print(f"  System B Score: {score_b}/10")

        diffs = comparison.get("key_differences", [])
        if diffs:
            print(f"\n  Key Differences:")
            for d in diffs:
                print(f"     -> {d}")

    print(f"\n{'=' * 60}")
    print("  Demo 3: Pre-Built Test Suite")
    print(f"{'=' * 60}")

    suite = TestSuite.create_local_search_suite()
    summary = suite.summary()
    print(f"\n  Suite: {summary['name']}")
    print(f"  Total test cases: {summary['total_cases']}")
    print(f"\n  Categories:")
    for cat, count in summary["categories"].items():
        print(f"     {cat:.<30} {count} cases")
    print(f"\n  Sample queries:")
    for case in suite.cases[:5]:
        print(f"     [{case.category}] '{case.query}'")

    os.makedirs("results", exist_ok=True)
    suite.to_json("results/local_search_suite.json")
    if result and "error" not in result:
        with open("results/demo_evaluation.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
    if comparison and "error" not in comparison:
        with open("results/demo_comparison.json", "w") as f:
            json.dump(comparison, f, indent=2, default=str)

    stats = evaluator.get_stats()
    print(f"\n{'=' * 60}")
    print(f"  Session Stats")
    print(f"{'=' * 60}")
    print(f"  Evaluations run:  {stats['evaluations_run']}")
    print(f"  Comparisons run:  {stats['comparisons_run']}")
    print(f"  Total tokens:     {stats['total_tokens']:,}")
    print(f"  Avg eval time:    {stats['avg_eval_time']}s")
    print(f"\n  Results saved to: results/\n")


if __name__ == "__main__":
    main()
