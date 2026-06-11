import logging
import signal
import sys
import time
from typing import List

from config import Config
from email_client import EmailClient
from filters import EmailFilter
from formatter import MessageFormatter
from logger import setup_logging
from telegram_client import TelegramClient


class EmailMonitor:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._shutdown_requested = False
        self._folders = ["inbox", "Spam", "Notification"]

        self.email_client = EmailClient(config)
        self.telegram_client = TelegramClient(
            bot_token=config.telegram_bot_token.get_secret_value(),
            chat_id=config.telegram_chat_id,
        )
        self.filter = EmailFilter(
            subject_substring=config.filter_subject,
            body_substring=config.filter_body,
        )
        self.formatter = MessageFormatter()

    def _handle_signal(self, signum: int, frame) -> None:
        self._shutdown_requested = True

    def run(self) -> None:
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        setup_logging(self.config.log_level)
        logging.info("Starting Email to Telegram monitor...")

        try:
            self.email_client.connect()
        except Exception as exc:
            logging.error("Could not connect to email server: %s", exc)
            sys.exit(1)

        try:
            while not self._shutdown_requested:
                self._check_once()
                if not self._shutdown_requested:
                    logging.info("Waiting %s seconds before next check...", self.config.check_interval_seconds)
                    time.sleep(self.config.check_interval_seconds)
        finally:
            self.email_client.close()
            logging.info("Shutdown complete.")

    def _check_once(self) -> None:
        try:
            emails = self.email_client.fetch_unread(self._folders)
        except Exception as exc:
            logging.error("Error fetching emails: %s", exc)
            return

        for email in emails:
            try:
                logging.info("Checking email from %s | Subject: %s", email.sender, email.subject)

                if self.filter.matches(email):
                    logging.info("Email matches filter! Forwarding to Telegram...")
                    message = self.formatter.format(email)
                    self.telegram_client.send(message)
                    self.email_client.mark_seen(email.email_id, email.folder)
                else:
                    logging.info("Email does not meet filter criteria. Skipping.")
            except Exception as exc:
                logging.error("Error processing email from %s: %s", email.sender, exc)


def main() -> None:
    config = Config()
    monitor = EmailMonitor(config)
    monitor.run()


if __name__ == "__main__":
    main()
