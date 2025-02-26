import logging


class CustomFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.GREY = "\x1b[38;2;192;192;192m"
        self.BLUE = "\x1b[38;2;50;175;255m"
        self.ORANGE = "\x1b[38;2;255;140;0m"
        self.RED = "\x1b[38;2;255;0;0m"
        self.BG_RED = "\x1b[41;37;97m"
        self.RESET = "\x1b[0m"

        self._colors = {
            logging.DEBUG: self.GREY,
            logging.INFO: self.BLUE,
            logging.WARNING: self.ORANGE,
            logging.ERROR: self.RED,
            logging.CRITICAL: self.BG_RED,
        }

    def format(self, record):
        record.msg = self._colors[record.levelno] + record.msg + self.RESET
        return logging.Formatter.format(self, record)


def setup_logging():
    """Set up logging for disnake and rubbergod loggers."""
    output_fmt = "[{asctime}] [{levelname:<8}] {name}: {message}"
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    style = "{"

    disnake_logger = logging.getLogger("disnake")
    disnake_logger.setLevel(logging.INFO)

    prometheus_logger = logging.getLogger("prometheus")
    prometheus_logger.setLevel(logging.INFO)

    rubbergod_logger = logging.getLogger("rubbergod")
    rubbergod_logger.setLevel(logging.INFO)

    # These handlers need to be in this exact order or the log file will contain escape sequences
    file_formatter = logging.Formatter(output_fmt, dt_fmt, style)
    rubbergod_handler = logging.FileHandler(filename="logs/rubbergod.log", encoding="utf-8", mode="w")
    prometheus_handler = logging.FileHandler(filename="logs/prometheus.log", encoding="utf-8", mode="w")

    rubbergod_handler.setFormatter(file_formatter)
    prometheus_handler.setFormatter(file_formatter)

    disnake_logger.addHandler(rubbergod_handler)
    prometheus_logger.addHandler(prometheus_handler)
    rubbergod_logger.addHandler(rubbergod_handler)

    cli_handler = logging.StreamHandler()
    cli_formatter = CustomFormatter(output_fmt, dt_fmt, style)
    cli_handler.setFormatter(cli_formatter)
    disnake_logger.addHandler(cli_handler)
    prometheus_logger.addHandler(cli_handler)
    rubbergod_logger.addHandler(cli_handler)
