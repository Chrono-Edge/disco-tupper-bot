class BaseBotException(Exception):
    """
    Base OCImporter Exception.
    """


class ConfigurationError(BaseBotException):
    """
    The ConfigurationError exception is raised when the configuration of the Bot is invalid.
    """
