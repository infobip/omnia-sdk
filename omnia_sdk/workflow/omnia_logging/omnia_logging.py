import logging as log

omnia_logger = log.getLogger("omnia-sdk")
omnia_logger.setLevel(log.INFO)
stream_handler = log.StreamHandler()
formatter = log.Formatter("%(levelname)s: %(asctime)s - %(name)s - %(message)s")
stream_handler.setFormatter(formatter)
omnia_logger.addHandler(stream_handler)
