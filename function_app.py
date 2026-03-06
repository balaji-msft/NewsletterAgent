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


@app.timer_trigger(
    schedule="0 0 11 1 * *",      # 11:00 AM UTC on the 1st of each month
    arg_name="timer",
    run_on_startup=False,
)
def sprint_summary_timer(timer: func.TimerRequest) -> None:
    """Monthly timer trigger that invokes the Sprint Summary agent."""
    from sprintsummary.agent import run_sprint_summary_agent

    logging.info("Sprint Summary timer triggered.")
    if timer.past_due:
        logging.warning("Timer is past due – running anyway.")

    try:
        result = run_sprint_summary_agent()
        logging.info("Sprint Summary agent completed. Result preview: %s", result[:200])
    except Exception:
        logging.exception("Sprint Summary agent failed.")
        raise


@app.timer_trigger(
    schedule="0 0 12 1 * *",      # 12:00 PM UTC on the 1st of each month
    arg_name="timer",
    run_on_startup=False,
)
def powerbi_newsletter_timer(timer: func.TimerRequest) -> None:
    """Monthly timer trigger that invokes the Power BI Newsletter agent."""
    from powerbi.agent import run_powerbi_newsletter_agent

    logging.info("Power BI Newsletter timer triggered.")
    if timer.past_due:
        logging.warning("Timer is past due – running anyway.")

    try:
        result = run_powerbi_newsletter_agent()
        logging.info("Power BI Newsletter agent completed. Result preview: %s", result[:200])
    except Exception:
        logging.exception("Power BI Newsletter agent failed.")
        raise


@app.timer_trigger(
    schedule="0 0 13 1 * *",      # 1:00 PM UTC on the 1st of each month
    arg_name="timer",
    run_on_startup=False,
)
def fabricplatform_newsletter_timer(timer: func.TimerRequest) -> None:
    """Monthly timer trigger that invokes the Fabric Platform Newsletter agent."""
    from fabricplatform.agent import run_fabricplatform_newsletter_agent

    logging.info("Fabric Platform Newsletter timer triggered.")
    if timer.past_due:
        logging.warning("Timer is past due – running anyway.")

    try:
        result = run_fabricplatform_newsletter_agent()
        logging.info("Fabric Platform Newsletter agent completed. Result preview: %s", result[:200])
    except Exception:
        logging.exception("Fabric Platform Newsletter agent failed.")
        raise
