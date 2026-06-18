"""Interactive post-launch check-in.

Walks the user through the week 2 / 4 / 8 / 12 post-launch checkpoints from
playbooks/post-launch-checks.md. Asks the right questions, pulls them through
the kill-or-double-down decision matrix, and saves the result to disk so the
user can't fool themselves with vibes.

Usage:
    python -m scripts.checkin                     # interactive walk-through
    python -m scripts.checkin --niche shopify     # tag the entries to a niche

The script writes results to:
    briefs/<niche>/post-launch/week-<N>.md

The output is your written artifact for that checkpoint. Required for advancing
through the post-launch phase per the coach's no-vibes rule.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import click

REPO_ROOT = Path(__file__).resolve().parent.parent
BRIEFS_DIR = REPO_ROOT / "briefs"


# ---------------------------------------------------------------------------
# week-by-week question packs
# ---------------------------------------------------------------------------


WEEK_2 = {
    "title": "Week 2 — Install signal check",
    "purpose": "Does anyone want this?",
    "questions": [
        ("installs_total", "Total installs since launch (publisher dashboard)", int),
        ("listing_visitors", "Total listing visitors (publisher dashboard)", int),
        ("reviews_count", "Reviews left so far", int),
        ("reviews_avg_rating", "Average star rating (skip if 0 reviews)", float),
        ("refunds_initiated", "Refunds initiated", int),
        ("dm_replies", "DMs / emails / questions received from real users", int),
    ],
}

WEEK_4 = {
    "title": "Week 4 — Engagement check",
    "purpose": "Do people who installed it actually use it?",
    "questions": [
        ("installs_total", "Total cumulative installs", int),
        ("installs_this_week", "Installs in just the last 7 days", int),
        ("reviews_count", "Total reviews so far", int),
        ("reviews_avg_rating", "Average star rating", float),
        ("refunds_total", "Total refunds since launch", int),
        ("support_hours_per_week", "Hours/week on support so far", float),
        ("negative_reviews_about_known_bugs", "Negative reviews about issues you already know exist", int),
    ],
}

WEEK_8 = {
    "title": "Week 8 — Velocity check",
    "purpose": "Is this growing or stagnating?",
    "questions": [
        ("installs_total", "Total cumulative installs", int),
        ("installs_weeks_1_2", "Installs during weeks 1-2 (look back at week-2 entry)", int),
        ("installs_weeks_7_8", "Installs during weeks 7-8 (most recent two weeks)", int),
        ("reviews_count", "Total reviews", int),
        ("reviews_recent_30d_rating", "Average rating across reviews from last 30 days", float),
        ("search_rank_top_keyword", "Where do you rank in apps.odoo.com search for your top keyword? (1=top, 0=not visible)", int),
    ],
}

WEEK_12 = {
    "title": "Week 12 — Kill or double-down",
    "purpose": "The big one. Pre-committed kill rules apply.",
    "questions": [
        ("installs_total", "Total cumulative installs", int),
        ("revenue_total_usd", "Total revenue since launch (publisher dashboard, in USD)", float),
        ("revenue_run_rate_monthly", "Current monthly revenue run-rate (last 30 days)", float),
        ("revenue_growing_flat_declining", "Revenue trend (growing / flat / declining) — type one word", str),
        ("hours_per_week", "Average hours/week you've been working on this app over last 4 weeks", float),
        ("support_hours_per_week", "Of those, how many on support specifically", float),
        ("motivation_1_to_10", "Honest motivation level for continuing (1-10)", int),
    ],
}

CHECKIN_PACKS = {2: WEEK_2, 4: WEEK_4, 8: WEEK_8, 12: WEEK_12}


# ---------------------------------------------------------------------------
# decision logic
# ---------------------------------------------------------------------------


def _verdict_week_2(answers: dict) -> tuple[str, list[str]]:
    notes: list[str] = []
    installs = answers["installs_total"]
    visitors = answers["listing_visitors"]

    if installs == 0 and visitors >= 200:
        return "LISTING CRISIS", [
            "Listing copy is the bottleneck. Rewrite headline + first paragraph + screenshots THIS week.",
            "Show 3 of your Day-3 interviewees the listing, ask: 'would you click install?' Their feedback drives the rewrite.",
            "Re-install the app yourself in fresh Odoo to confirm it actually works.",
        ]

    if installs == 0 and visitors < 50:
        return "DISTRIBUTION CRISIS", [
            "You're not getting in front of buyers. Increase posting frequency.",
            "Email your full waitlist again with subject 'a few weeks in — would love your honest take'.",
            "Post in 2 more channels you haven't yet (LinkedIn, Indie Hackers, OCA Telegram).",
        ]

    if 1 <= installs <= 2:
        return "SLOW START (within range of normal)", [
            "Don't panic. Apps.odoo.com search rankings take weeks.",
            "Continue distribution: weekly r/Odoo update, partner outreach.",
            "Email each installer for feedback within 24h.",
        ]

    if 3 <= installs <= 7:
        return "HEALTHY START", [
            "Continue plan. Email each installer for feedback.",
            "Start drafting v1.1 based on first installer feedback.",
        ]

    if installs >= 8:
        notes.append("Strong launch — note this; it tells you the niche has real demand.")
        notes.append("Plan v1.1 around early reviews; consider raising prices in week 4.")
        return "STRONG LAUNCH", notes

    return "REVIEW MANUALLY", ["Numbers don't fit the matrix — re-read playbooks/post-launch-checks.md"]


def _verdict_week_4(answers: dict) -> tuple[str, list[str]]:
    installs = answers["installs_total"]
    refunds = answers["refunds_total"]
    reviews = answers["reviews_count"]
    bug_reviews = answers["negative_reviews_about_known_bugs"]

    refund_rate = (refunds / installs) if installs else 0
    review_ratio = (reviews / installs) if installs else 0

    if refund_rate > 0.20:
        return "QUALITY CRISIS — STOP NEW INSTALLS", [
            "Refund rate above 20%. Pause your distribution efforts.",
            "Watch a refunder install (record their screen if possible).",
            "Identify the failure point. Fix it. Re-launch with a v1.1.",
            "Apps.odoo.com will rate-limit your visibility if you stay above 25%.",
        ]

    if reviews == 0 and installs >= 5:
        return "ENGAGEMENT CRISIS", [
            "No reviews after 4 weeks of installs. Email every installer personally.",
            "Use the template: 'what worked, what didn't, would you give me 1 line as a review?'",
            "Conversion from this email to a review is typically 10-20%.",
        ]

    if bug_reviews >= 2:
        return "UNDER-SPECCED V1", [
            "Multiple negative reviews about known bugs. Ship v1.1 with fixes within 14 days.",
            "Reply to negative reviews acknowledging fixes are on the way.",
            "After v1.1 ships, ask the negative reviewers to re-evaluate — most will update.",
        ]

    if refund_rate > 0 and review_ratio < 0.05:
        return "SILENT QUITTERS", [
            "Customers are refunding without reviewing — they're not telling you what's wrong.",
            "Email each refunder for feedback. Most won't reply, but the few who do are gold.",
        ]

    return "STABLE — CONTINUE PLAN", [
        f"Refund rate {refund_rate*100:.1f}%, review ratio {review_ratio*100:.1f}%. Healthy range.",
        "Continue weekly posts. Consider drafting v1.1 with top 2 user-requested features.",
    ]


def _verdict_week_8(answers: dict) -> tuple[str, list[str]]:
    weeks_1_2 = answers["installs_weeks_1_2"] or 1
    weeks_7_8 = answers["installs_weeks_7_8"]
    velocity_ratio = weeks_7_8 / weeks_1_2

    if velocity_ratio >= 1.5:
        return "GROWING — STAY THE COURSE", [
            f"Velocity is {velocity_ratio:.2f}x — app is finding its audience.",
            "Plan v1.2 based on accumulated review feedback.",
            "Consider raising prices 30%. New buyers won't notice; existing buyers aren't affected.",
        ]

    if 0.8 <= velocity_ratio <= 1.5:
        return "FLAT — NORMAL, KEEP GOING", [
            f"Velocity is {velocity_ratio:.2f}x — stable but not yet compounding.",
            "This is normal. Continue marketing motions for 4 more weeks.",
            "Don't panic, don't stop. Search rankings still maturing.",
        ]

    if velocity_ratio < 0.8 and weeks_7_8 > 0:
        return "DECLINING — DIAGNOSE", [
            f"Velocity is {velocity_ratio:.2f}x — declining. Either novelty wore off, or quality is hurting word-of-mouth.",
            "Read your reviews carefully. Identify the top complaint. Ship a fix.",
            "Engage publicly with reviewers showing the fix coming.",
        ]

    if weeks_7_8 == 0:
        return "STALL — POSSIBLE WRONG-NICHE SIGNAL", [
            "0 installs in weeks 7-8. Test ONE big change in week 9 (listing rewrite, price drop, new differentiator).",
            "Re-read your Day-3 interviews. Is there a different audience you missed?",
            "If still 0 installs at week 12, kill or pivot.",
        ]

    return "REVIEW MANUALLY", ["Re-read playbooks/post-launch-checks.md week 8 section"]


def _verdict_week_12(answers: dict) -> tuple[str, list[str]]:
    rev = answers["revenue_run_rate_monthly"]
    trend = (answers["revenue_growing_flat_declining"] or "").lower()
    hours = answers["hours_per_week"]
    motivation = answers["motivation_1_to_10"]

    sustainable = hours <= 12 and motivation >= 5
    heavy = hours > 20 or motivation <= 4

    if rev > 300 and trend == "growing" and sustainable:
        return "CONTINUE", [
            f"${rev:.0f}/mo and growing on sustainable hours. You're on the path to $1k/mo by month 6-9.",
            "Stay focused. Don't start app #2 yet.",
        ]

    if 100 <= rev <= 300 and trend == "growing" and sustainable:
        return "CONTINUE + PLAN APP #2 IN PARALLEL (just ideation)", [
            f"${rev:.0f}/mo and growing — slow-burn winner. Knowing app #2 is coming reduces pressure on #1.",
            "Start sketching app #2 ideas in spare moments. Don't write code yet.",
        ]

    if 100 <= rev <= 300 and trend == "flat" and sustainable:
        return "MAINTAIN MODE — MOVE ENERGY TO APP #2", [
            f"${rev:.0f}/mo flat is fine. Don't kill, don't push hard.",
            "Quarterly updates only. Move primary energy to validating + building app #2.",
        ]

    if rev < 100 and trend == "growing" and sustainable:
        return "ONE MORE MONTH, THEN DECIDE", [
            f"${rev:.0f}/mo growing slowly. Give it 4 more weeks.",
            "If still <$200/mo at week 16, kill.",
        ]

    if rev < 100 and (trend == "flat" or heavy):
        return "KILL — WRITE THE POSTMORTEM", [
            f"${rev:.0f}/mo flat with {hours:.1f}h/week effort. You're working harder than the revenue justifies.",
            "Write briefs/<niche>/postmortem.md per the playbook.",
            "Capture lessons. Move on. Start app #2 with calibrated knowledge.",
        ]

    if trend == "declining":
        return "KILL OR PIVOT", [
            "Pivot only if you have a specific hypothesis (e.g. wrong audience identified).",
            "Otherwise, kill. Don't grind a declining trajectory.",
        ]

    return "REVIEW MANUALLY", ["Numbers don't cleanly fit the matrix — re-read playbooks/post-launch-checks.md week 12 section"]


VERDICT_FNS = {
    2: _verdict_week_2,
    4: _verdict_week_4,
    8: _verdict_week_8,
    12: _verdict_week_12,
}


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _ask_questions(pack: dict) -> dict:
    answers: dict = {}
    print(f"\n=== {pack['title']} ===")
    print(f"Purpose: {pack['purpose']}")
    print()
    for key, prompt, cast in pack["questions"]:
        while True:
            raw = input(f"  {prompt}: ").strip()
            if raw == "" or raw.lower() in {"skip", "s", "n/a", "-"}:
                answers[key] = 0 if cast in (int, float) else ""
                break
            try:
                answers[key] = cast(raw)
                break
            except ValueError:
                print(f"  (couldn't parse as {cast.__name__}; type 'skip' to skip)")
    return answers


def _save_artifact(week: int, niche: str, answers: dict, verdict: str, actions: list[str]) -> Path:
    out_dir = BRIEFS_DIR / niche / "post-launch"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"week-{week:02d}.md"

    lines = [
        f"# Post-launch check-in — week {week}",
        f"*Niche: {niche}*  ·  *Recorded: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Numbers",
    ]
    for k, v in answers.items():
        lines.append(f"- {k}: **{v}**")
    lines.append("")
    lines.append(f"## Verdict: **{verdict}**")
    lines.append("")
    lines.append("## Recommended actions")
    for a in actions:
        lines.append(f"- {a}")
    lines.append("")
    lines.append("## My honest reflection")
    lines.append("")
    lines.append("> [write 2-3 sentences here in your editor before closing this file]")
    lines.append("")

    out_file.write_text("\n".join(lines), encoding="utf-8")
    return out_file


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.command()
@click.option("--week", type=click.Choice(["2", "4", "8", "12"]), help="Which checkpoint")
@click.option("--niche", default=None, help="Niche name (used for output path)")
def main(week: str | None, niche: str | None) -> None:
    """Walk through a post-launch checkpoint and record the verdict."""
    print()
    print("=" * 60)
    print("  OdooStack Coach — post-launch check-in")
    print("=" * 60)

    if not niche:
        niche = input("Niche name (e.g. 'shopify-bridge'): ").strip() or "untitled"

    if not week:
        week_raw = input("Which week are you checking? [2 / 4 / 8 / 12]: ").strip()
        if week_raw not in {"2", "4", "8", "12"}:
            print("Invalid week. Run again with --week 2/4/8/12.")
            sys.exit(1)
        week = week_raw

    week_int = int(week)
    pack = CHECKIN_PACKS[week_int]
    verdict_fn = VERDICT_FNS[week_int]

    answers = _ask_questions(pack)
    verdict, actions = verdict_fn(answers)

    print()
    print("─" * 60)
    print(f"  VERDICT: {verdict}")
    print("─" * 60)
    print()
    print("Recommended actions:")
    for a in actions:
        print(f"  • {a}")
    print()

    out_file = _save_artifact(week_int, niche, answers, verdict, actions)
    print(f"Saved: {out_file}")
    print()
    print("Open the file and add your honest reflection (2-3 sentences) at the bottom.")
    print("Without that reflection, the checkpoint is incomplete.")
    print()


if __name__ == "__main__":
    main()
