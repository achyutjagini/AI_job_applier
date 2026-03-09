from __future__ import annotations

import logging

from agents.auto_apply_agent import AutoApplyAgent

logger = logging.getLogger(__name__)


def run_auto_apply(test_mode: bool = True) -> dict[str, int]:
    """Run the minimal auto-apply stage over generated application folders."""

    agent = AutoApplyAgent(test_mode=test_mode)
    summary = agent.run()
    logger.info("Auto apply summary: %s", summary)
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_auto_apply()
