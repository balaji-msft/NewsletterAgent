"""
Azure Function – Timer Trigger (monthly) to run the Newsletter Agent.
Runs on the 1st of every month at 9:00 AM UTC.
"""
import logging
import azure.functions as func
from agent import run_newsletter_agent

app = func.FunctionApp()

@app.timer_trigger(
    schedule="0 0 9 1 * *",       # 9:00 AM UTC on the 1st of each month
    arg_name="timer",
    run_on_startup=False,
)
def newsletter_timer(timer: func.TimerRequest) -> None:
    """Monthly timer trigger that invokes the newsletter agent."""
    logging.info("Newsletter timer triggered.")

    if timer.past_due:
        logging.warning("Timer is past due – running anyway.")

    try:
        result = run_newsletter_agent()
        logging.info("Newsletter agent completed. Result preview: %s", result[:200])
    except Exception:
        logging.exception("Newsletter agent failed.")
        raise
