"""
Unified entry point – run any agent locally.

Usage:
  python run_local.py                                # full newsletter (all sections)
  python run_local.py --agent newsletter             # explicit: newsletter agent
  python run_local.py --agent powerbi                # Power BI newsletter agent
  python run_local.py --agent fabricplatform         # Fabric Platform newsletter agent
  python run_local.py --agent mor                    # Fabric BI MoR callout agent
  python run_local.py --agent dnai                    # Fabric BI MoR callout agent
  python run_local.py --agent sprint                 # Sprint Summary agent
  python run_local.py --section tsg                  # only the TSG section
  python run_local.py --section tsg -p "Fabric Experiences/Data Engineering"  # TSG with folder path
  python run_local.py --section hot_topics           # only Hot Topics
  python run_local.py --section eeez                 # only Fabric Made EEE-z
  python run_local.py --section eeez                 # only Fabric Made EEE-z
  python run_local.py --section css_feedback         # only CSS Feedback Items
  python run_local.py --section css_taxonomy         # only CSS Taxonomy Changes
  python run_local.py --section vteam                # only Component V-Team
  python run_local.py "your custom prompt"           # use a custom prompt
  python run_local.py --interactive                  # interactive mode (type prompts)
  python run_local.py --send                         # generate & send email
  python run_local.py --section tsg --send           # single section + send email
  python run_local.py --agent mor --send             # MoR callouts + send email
  python run_local.py --agent sprint --send          # Sprint Summary + send email
  python run_local.py --agent powerbi --send         # Power BI newsletter + send email
  python run_local.py --agent fabricplatform --send   # Fabric Platform newsletter + send email
"""
import argparse
import json
import logging
import os
import sys

# ── Load local.settings.json into env vars ──────────────────────────
settings_path = os.path.join(os.path.dirname(__file__), "local.settings.json")
if os.path.exists(settings_path):
    with open(settings_path, "r") as f:
        settings = json.load(f)
    for k, v in settings.get("Values", {}).items():
        if v:
            os.environ.setdefault(k, v)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s  %(message)s",
)

# ── Section-specific prompts (newsletter only) ──────────────────────
SECTION_PROMPTS = {
    "hot_topics": (
        "Please compile ONLY the **Hot Topics** section of the newsletter. "
        "Call get_hot_topics_files, summarize the content, and return a "
        "standalone HTML fragment for this section. Do NOT call any other tools."
    ),
    "tsg": (
        "Please compile ONLY the **TSG (Troubleshooting Guides)** section. "
        "Call get_wiki_commits with the configured folder and year/month for "
        "the previous calendar month (e.g. year=2026, month=2 for February), "
        "then render the Component | Page table as an HTML fragment. "
        "Do NOT call any other tools."
    ),
    "eeez": (
        "Please compile ONLY the **Fabric Made EEE-z** section. "
        "Call get_eeez_features, render the features table as an HTML fragment. "
        "Do NOT call any other tools."
    ),
    "css_feedback": (
        "Please compile ONLY the **CSS Feedback Items** section. "
        "Call get_ado_query_results with the CSS Feedback query_id, org_url, "
        "and project, then render the results as an HTML table fragment. "
        "Do NOT call any other tools."
    ),
    "css_taxonomy": (
        "Please compile ONLY the **CSS Taxonomy Changes** section. "
        "Call get_ado_query_results with the CSS Taxonomy query_id, org_url, "
        "and project, then summarize the changes as an HTML fragment. "
        "Do NOT call any other tools."
    ),
    "vteam": (
        "Please compile ONLY the **Component V-Team** section. "
        "Call get_static_content with section_name 'vteam', convert the "
        "markdown to a well-formatted HTML fragment with the ownership table "
        "and thank-you list. Do NOT call any other tools."
    ),
}

VALID_SECTIONS = list(SECTION_PROMPTS.keys())


# ── Runner helpers ──────────────────────────────────────────────────

def _run_newsletter(args):
    from newsletter.agent import run_newsletter_agent

    if args.interactive:
        _interactive_loop("NEWSLETTER AGENT", run_newsletter_agent)
        return

    if args.section:
        prompt = SECTION_PROMPTS[args.section]
        print(f"Running section: {args.section}\n")
    elif args.prompt:
        prompt = " ".join(args.prompt)
        print(f"Custom prompt: {prompt}\n")
    else:
        prompt = None
        print("Using default newsletter prompt.\n")

    result = run_newsletter_agent(user_prompt=prompt)
    _show_result("NEWSLETTER AGENT RESULT", result)

    suffix = f"_{args.section}" if args.section else ""
    out_path = os.path.join(os.path.dirname(__file__), "output", f"newsletter_output{suffix}.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\nSaved to: {out_path}")

    if args.send:
        from newsletter import config as nl_cfg
        from newsletter.tools import send_email

        section_label = args.section or "Full Newsletter"
        subject = f"{nl_cfg.EMAIL_SUBJECT_PREFIX} - {section_label}"
        _send(send_email, subject, result, nl_cfg.EMAIL_RECIPIENTS)


def _run_mor(args):
    from fabricbimor.agent import run_mor_agent

    if args.interactive:
        _interactive_loop("FABRIC BI MoR CALLOUT AGENT", run_mor_agent)
        return

    if args.prompt:
        prompt = " ".join(args.prompt)
        print(f"Custom prompt: {prompt}\n")
    else:
        prompt = None
        print("Using default MoR callout prompt.\n")

    result = run_mor_agent(user_prompt=prompt)
    _show_result("MoR CALLOUT AGENT RESULT", result)

    out_path = os.path.join(os.path.dirname(__file__), "output", "fabricbimor_output.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\nSaved to: {out_path}")

    if args.send:
        from fabricbimor import config as mor_cfg
        from fabricbimor.tools import send_email

        subject = mor_cfg.EMAIL_SUBJECT_PREFIX
        _send(send_email, subject, result, mor_cfg.EMAIL_RECIPIENTS)


def _run_sprint(args):
    from sprintsummary.agent import run_sprint_summary_agent

    if args.interactive:
        _interactive_loop("SPRINT SUMMARY AGENT", run_sprint_summary_agent)
        return

    if args.prompt:
        prompt = " ".join(args.prompt)
        print(f"Custom prompt: {prompt}\n")
    else:
        prompt = None
        print("Using default Sprint Summary prompt.\n")

    result = run_sprint_summary_agent(user_prompt=prompt)
    _show_result("SPRINT SUMMARY AGENT RESULT", result)

    out_path = os.path.join(os.path.dirname(__file__), "output", "sprintsummary_output.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\nSaved to: {out_path}")

    if args.send:
        from sprintsummary import config as sprint_cfg
        from sprintsummary.tools import send_email

        subject = sprint_cfg.EMAIL_SUBJECT_PREFIX
        _send(send_email, subject, result, sprint_cfg.EMAIL_RECIPIENTS)


def _run_powerbi(args):
    from powerbi.agent import run_powerbi_newsletter_agent

    if args.interactive:
        _interactive_loop("POWER BI NEWSLETTER AGENT", run_powerbi_newsletter_agent)
        return

    if args.section:
        prompt = SECTION_PROMPTS[args.section]
        print(f"Running section: {args.section}\n")
    elif args.prompt:
        prompt = " ".join(args.prompt)
        print(f"Custom prompt: {prompt}\n")
    else:
        prompt = None
        print("Using default Power BI newsletter prompt.\n")

    result = run_powerbi_newsletter_agent(user_prompt=prompt)
    _show_result("POWER BI NEWSLETTER AGENT RESULT", result)

    suffix = f"_{args.section}" if args.section else ""
    out_path = os.path.join(os.path.dirname(__file__), "output", f"powerbi_output{suffix}.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\nSaved to: {out_path}")

    if args.send:
        from powerbi import config as pbi_cfg
        from powerbi.tools import send_email

        section_label = args.section or "Full Newsletter"
        subject = f"{pbi_cfg.EMAIL_SUBJECT_PREFIX} - {section_label}"
        _send(send_email, subject, result, pbi_cfg.EMAIL_RECIPIENTS)


def _run_fabricplatform(args):
    from fabricplatform.agent import run_fabricplatform_newsletter_agent

    if args.interactive:
        _interactive_loop("FABRIC PLATFORM NEWSLETTER AGENT", run_fabricplatform_newsletter_agent)
        return

    if args.section:
        prompt = SECTION_PROMPTS[args.section]
        print(f"Running section: {args.section}\n")
    elif args.prompt:
        prompt = " ".join(args.prompt)
        print(f"Custom prompt: {prompt}\n")
    else:
        prompt = None
        print("Using default Fabric Platform newsletter prompt.\n")

    result = run_fabricplatform_newsletter_agent(user_prompt=prompt)
    _show_result("FABRIC PLATFORM NEWSLETTER AGENT RESULT", result)

    suffix = f"_{args.section}" if args.section else ""
    out_path = os.path.join(os.path.dirname(__file__), "output", f"fabricplatform_output{suffix}.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\nSaved to: {out_path}")

    if args.send:
        from fabricplatform import config as fp_cfg
        from fabricplatform.tools import send_email

        section_label = args.section or "Full Newsletter"
        subject = f"{fp_cfg.EMAIL_SUBJECT_PREFIX} - {section_label}"
        _send(send_email, subject, result, fp_cfg.EMAIL_RECIPIENTS)


def _run_dnai(args):
    from dnai.agent import run_dnai_newsletter_agent

    if args.interactive:
        _interactive_loop("DNAI NEWSLETTER AGENT", run_dnai_newsletter_agent)
        return

    if args.section:
        prompt = SECTION_PROMPTS[args.section]
        if args.section == "eeez" and args.filter:
            prompt += f' Use title_filter="{args.filter}" when calling get_eeez_features.'
            print(f"Running section: {args.section} (filter={args.filter})\n")
        elif args.section == "tsg" and args.path:
            prompt += f' Use folder_filter="{args.path}" when calling get_wiki_commits.'
            print(f"Running section: {args.section} (path={args.path})\n")
        else:
            print(f"Running section: {args.section}\n")
    elif args.prompt:
        prompt = " ".join(args.prompt)
        print(f"Custom prompt: {prompt}\n")
    else:
        prompt = None
        print("Using default DnAI newsletter prompt.\n")

    result = run_dnai_newsletter_agent(user_prompt=prompt)
    _show_result("DNAI NEWSLETTER AGENT RESULT", result)

    suffix = f"_{args.section}" if args.section else ""
    out_path = os.path.join(os.path.dirname(__file__), "output", f"dnai_output{suffix}.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\nSaved to: {out_path}")

    if args.send:
        from dnai import config as dnai_cfg
        from dnai.tools import send_email

        section_label = args.section or "Full Newsletter"
        subject = f"{dnai_cfg.EMAIL_SUBJECT_PREFIX} - {section_label}"
        _send(send_email, subject, result, dnai_cfg.EMAIL_RECIPIENTS)


def _interactive_loop(banner: str, run_fn):
    print("=" * 60)
    print(f"{banner} - INTERACTIVE MODE")
    print("Type your prompt, or 'quit' to exit.")
    print("=" * 60)
    while True:
        try:
            prompt = input("\nYour prompt> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not prompt or prompt.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break
        print("\nRunning agent...\n")
        result = run_fn(user_prompt=prompt)
        _show_result("AGENT RESPONSE", result)


def _show_result(header: str, result: str):
    print("=" * 60)
    print(header)
    print("=" * 60)
    print(result)


def _send(send_fn, subject, html, recipients):
    print(f"\nSending email to {recipients}...")
    try:
        res = send_fn(subject=subject, html_body=html, to_recipients=recipients)
        print(f"Email sent: {res}")
    except Exception as exc:
        print(f"Email send failed: {exc}")


# ── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run Newsletter, MoR, Sprint Summary, Power BI, Fabric Platform, or DnAI agent locally.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Agents: newsletter (default), powerbi, fabricplatform, dnai, mor, sprint\n"
            "Newsletter sections: " + ", ".join(VALID_SECTIONS)
        ),
    )
    parser.add_argument(
        "--agent", "-a",
        choices=["newsletter", "powerbi", "fabricplatform", "dnai", "mor", "sprint"],
        default="newsletter",
        help="Which agent to run (default: newsletter).",
    )
    parser.add_argument(
        "--section", "-s",
        choices=VALID_SECTIONS,
        help="Newsletter only: compile a single section.",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Enter interactive prompt mode.",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send the generated output via email after generation.",
    )
    parser.add_argument(
        "--filter", "-f",
        help="EEE-z title filter override (e.g. NF-PBI, NF-PLAT). Used with --section eeez.",
    )
    parser.add_argument(
        "--path", "-p",
        help='TSG wiki folder path override (e.g. "Fabric Experiences/Data Engineering"). Used with --section tsg.',
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Custom prompt text (ignored when --section or --interactive is used).",
    )
    args = parser.parse_args()

    if args.agent == "mor":
        _run_mor(args)
    elif args.agent == "sprint":
        _run_sprint(args)
    elif args.agent == "powerbi":
        _run_powerbi(args)
    elif args.agent == "fabricplatform":
        _run_fabricplatform(args)
    elif args.agent == "dnai":
        _run_dnai(args)
    else:
        _run_newsletter(args)


if __name__ == "__main__":
    main()
