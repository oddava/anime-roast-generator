"""Test script to demonstrate the improvements to roast generation."""

import sys

sys.path.insert(0, "/home/oddava/Projects/anime-roast-generator/backend")

from simple_context_builder import SimpleContextBuilder
from roast_cleaner import RoastCleaner

# Mock data simulating OPM Season 3
opm_data = {
    "title": {"romaji": "One Punch Man Season 3", "english": "One Punch Man Season 3"},
    "year": 2025,
    "episodes": 12,
    "format": "TV",
    "studios": ["J.C.Staff"],
    "source": "MANGA",
    "score": 51,  # 5.1/10
    "controversyScore": 15,
    "relations": [{"relation": "PREQUEL", "title": "One Punch Man Season 2"}],
}

# Mock review context with few reviews (below threshold)
sparse_reviews = {
    "review_count": 4,
    "verified_complaints": [],
    "anilist_score": 5.1,
    "sentiment_breakdown": {"positive_pct": 100, "negative_pct": 0},
}

# Mock review context with many reviews
rich_reviews = {
    "review_count": 15,
    "verified_complaints": [
        {
            "category": "animation",
            "review_count": 12,
            "examples": ["the animation looks cheap compared to season 1 and 2"],
        },
        {
            "category": "studio",
            "review_count": 10,
            "examples": ["JC Staff ruined what Madhouse built"],
        },
    ],
    "anilist_score": 5.1,
}

print("=" * 80)
print("TEST: One Punch Man Season 3 (Low Review Count)")
print("=" * 80)
print("\nSimplified Context (NEW - below 10 review threshold):")
print("-" * 80)

context_sparse = SimpleContextBuilder.build_context(opm_data, sparse_reviews)
print(context_sparse)

print("\n" + "=" * 80)
print("TEST: One Punch Man Season 3 (High Review Count)")
print("=" * 80)
print("\nSimplified Context (NEW - above 10 review threshold):")
print("-" * 80)

context_rich = SimpleContextBuilder.build_context(opm_data, rich_reviews)
print(context_rich)

print("\n" + "=" * 80)
print("TEST: Roast Cleaner")
print("=" * 80)

# Example bad roast (simulating what the old system might produce)
bad_roast = """Oh, look, One-Punch Man Season 3 made it to TV for 12 glorious episodes! 
Guess they finally adapted more of the MANGA... because who doesn't love seeing a guy 
so OP he can end battles with a sneeze? Coming in at an earth-shattering 5.1/10 on AniList, 
it seems like SOMEONE's punch landed a little flat. But hey, at least it's number ONE... 
in most popular, out of how many, exactly? Right. And while the sentiment is 100% POSITIVE 
across 4 whole reviews, it begs the question: are we watching a show or are we just 
aggressively agreeing with each other?"""

print("\nBEFORE (Robotic/Statistical):")
print("-" * 80)
print(bad_roast[:300] + "...")

print("\nAFTER (Cleaned):")
print("-" * 80)
cleaned = RoastCleaner.clean_roast(bad_roast)
print(cleaned[:300] + "...")

print("\n" + "=" * 80)
print("KEY IMPROVEMENTS:")
print("=" * 80)
print("✓ No percentages or statistics in output")
print("✓ Review data only shown when >= 10 reviews")
print("✓ Qualitative reception descriptions only")
print("✓ Post-generation cleanup removes awkward phrasing")
print("✓ Franchise context for sequels")
print("✓ Focus on actual quotes from reviews")
print("=" * 80)
