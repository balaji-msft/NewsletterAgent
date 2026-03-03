"""
Standalone entry point – run the Fabric BI MoR Callout Agent locally.

Usage:
  python fabricbimor_run.py                     # generate MoR callouts (default)
  python fabricbimor_run.py --send               # generate & send email
  python fabricbimor_run.py "custom prompt"      # use a custom prompt
  python fabricbimor_run.py --interactive        # interactive mode
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

from fabricbimor_agent import run_mor_agent


def main():
    parser = argparse.ArgumentParser(
        description="Run the Fabric BI MoR Callout Agent locally.",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Enter interactive prompt mode.",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send the generated MoR callouts via email after generation.",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Custom prompt text (ignored when --interactive is used).",
    )
    args = parser.parse_args()

    if args.interactive:
        print("=" * 60)
        print("FABRIC BI MoR CALLOUT AGENT - INTERACTIVE MODE")
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
            print("\nRunning MoR agent...\n")
            result = run_mor_agent(user_prompt=prompt)
            print("=" * 60)
            print("MoR AGENT RESPONSE")
            print("=" * 60)
            print(result)
    else:
        if args.prompt:
            prompt = " ".join(args.prompt)
            print(f"Custom prompt: {prompt}\n")
        else:
            prompt = None
            print("Using default MoR callout prompt.\n")

        result = run_mor_agent(user_prompt=prompt)
        print("=" * 60)
        print("MoR CALLOUT AGENT RESULT")
        print("=" * 60)
        print(result)

        # Save output to file
        out_path = os.path.join(os.path.dirname(__file__), "fabricbimor_output.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\nSaved to: {out_path}")

        # Optionally send email
        if args.send:
            import fabricbimor_config as mor_cfg
            from fabricbimor_tools import send_email

            subject = mor_cfg.EMAIL_SUBJECT_PREFIX
            recipients = mor_cfg.EMAIL_RECIPIENTS
            print(f"\nSending email to {recipients}...")
            try:
                send_result = send_email(subject=subject, html_body=result, to_recipients=recipients)
                print(f"Email sent: {send_result}")
            except Exception as exc:
                print(f"Email send failed: {exc}")


if __name__ == "__main__":
    main()
