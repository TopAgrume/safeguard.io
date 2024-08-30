import os

class Config:
    """
    Configuration class for retrieving and validating environment variables required
    for the Telegram bot.

    Attributes:
        TELEGRAM_API_TOKEN (str): The API token for the Telegram bot, retrieved from the
                                  environment variables.
        TELEGRAM_BOT_USERNAME (str): The username of the Telegram bot, retrieved from the
                                     environment variables.
    """
    TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
    TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME')

    @classmethod
    def validate(cls):
        """
        Validates that the necessary Telegram environment variables are set. If any of
        the required variables are missing, it raises a ValueError.

        Raises:
            ValueError: If TELEGRAM_API_TOKEN or TELEGRAM_BOT_USERNAME is not set.
        """
        if not cls.TELEGRAM_API_TOKEN or not cls.TELEGRAM_BOT_USERNAME:
            raise ValueError("One or more required Telegram environment variables are missing.")