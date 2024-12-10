import logging

class _Logging:
    """Custom logging class"""
    def __init__(self):
        pass

    def logging_setup():
        """Setup logging"""
        logger = logging.getLogger(__name__)
        logging.basicConfig(
            format="[%(asctime)s] %(levelname)s %(message)s",
            encoding="utf-8",
            level=logging.INFO,
        )
        return logging
