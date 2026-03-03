"""
Standalone entry point – run the newsletter agent locally.

Usage:
  python run_local.py                            # full newsletter (all sections)
  python run_local.py --section tsg              # only the TSG section
  python run_local.py --section hot_topics       # only Hot Topics
  python run_local.py --section eeez             # only Fabric Made EEE-z
  python run_local.py --section css_feedback     # only CSS Feedback Items
  python run_local.py --section css_taxonomy     # only CSS Taxonomy Changes
  python run_local.py --section vteam            # only Component V-Team
  python run_local.py "your custom prompt"       # use a custom prompt
  python run_local.py --interactive              # interactive mode (type prompts)
  python run_local.py --send                     # generate & send email
  python run_local.py --section tsg --send       # single section + send email
"""
import argparse
import json
import logging
import os
import sys

# Load settings from local.settings.json into env vars
settings_path = os.path.join(os.path.dirname(__file__), "local.settings.json")
if os.path.exists(settings_path):
    with open(settings_path, "r") as f:
        settings = json.load(f)
    for k, v in settings.get("Values", {}).items():
        if v:
            os.environ.setdefault(k, v)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from agent import run_newsletter_agent

# ── Section-specific prompts ────────────────────────────────────────
# Each key maps to a user prompt that asks the agent to compile ONLY
# that section. The system prompt stays the same so all tool
# definitions remain available.
SECTION_PROMPTS = {
    "hot_topics": (
        "Please compile ONLY the **Hot Topics** section of the newsletter. "
        "Call get_hot_topics_files, summarize the content, and return a "
        "standalone HTML fragment for this section. Do NOT call any other tools."
    ),
    "tsg": (
        "Please compile ONLY the **TSG (Troubleshooting Guides)** section. "
        "Call get_wiki_commits with the configured folder and days_back=30, "
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


def main():
    parser = argparse.ArgumentParser(
        description="Run the Newsletter Agent locally.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Sections: " + ", ".join(VALID_SECTIONS),
    )
    parser.add_argument(
        "--section", "-s",
        choices=VALID_SECTIONS,
        help="Compile only a single section (useful for testing).",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Enter interactive prompt mode.",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send the generated newsletter via email after generation.",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Custom prompt text (ignored when --section or --interactive is used).",
    )
    args = parser.parse_args()

    if args.interactive:
        print("=" * 60)
        print("NEWSLETTER AGENT - INTERACTIVE MODE")
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
            result = run_newsletter_agent(user_prompt=prompt)
            print("=" * 60)
            print("AGENT RESPONSE")
            print("=" * 60)
            print(result)
    else:
        # Determine the prompt
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
        print("=" * 60)
        print("NEWSLETTER AGENT RESULT")
        print("=" * 60)
        print(result)

        # Save HTML output to file
        suffix = f"_{args.section}" if args.section else ""
        out_path = os.path.join(os.path.dirname(__file__), f"newsletter_output{suffix}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\nSaved to: {out_path}")

        # Optionally send email
        if args.send:
            import config
            from tools import send_email

            section_label = args.section or "Full Newsletter"
            subject = f"{config.EMAIL_SUBJECT_PREFIX} - {section_label}"
            recipients = config.EMAIL_RECIPIENTS
            print(f"\nSending email to {recipients}...")
            try:
                send_result = send_email(subject=subject, html_body=result, to_recipients=recipients)
                print(f"Email sent: {send_result}")
            except Exception as exc:
                print(f"Email send failed: {exc}")


if __name__ == "__main__":
    main()
