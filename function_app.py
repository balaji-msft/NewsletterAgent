"""
Azure Function – Timer Triggers for Newsletter and MoR agents.
"""
import logging
import azure.functions as func

app = func.FunctionApp()


@app.timer_trigger(
    schedule="0 0 9 1 * *",       # 9:00 AM UTC on the 1st of each month
    arg_name="timer",
    run_on_startup=False,
)
def newsletter_timer(timer: func.TimerRequest) -> None:
    """Monthly timer trigger that invokes the newsletter agent."""
    from newsletter.agent import run_newsletter_agent

    logging.info("Newsletter timer triggered.")
    if timer.past_due:
        logging.warning("Timer is past due – running anyway.")

    try:
        result = run_newsletter_agent()
        logging.info("Newsletter agent completed. Result preview: %s", result[:200])
    except Exception:
        logging.exception("Newsletter agent failed.")
        raise


@app.timer_trigger(
    schedule="0 0 10 1 * *",      # 10:00 AM UTC on the 1st of each month
    arg_name="timer",
    run_on_startup=False,
)
def mor_timer(timer: func.TimerRequest) -> None:
    """Monthly timer trigger that invokes the MoR callout agent."""
    from fabricbimor.agent import run_mor_agent

    logging.info("MoR timer triggered.")
    if timer.past_due:
        logging.warning("Timer is past due – running anyway.")

    try:
        result = run_mor_agent()
        logging.info("MoR agent completed. Result preview: %s", result[:200])
    except Exception:
        logging.exception("MoR agent failed.")
        raise
