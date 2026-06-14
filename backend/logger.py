import os
import logging
from pythonjsonlogger import jsonlogger

def setup_logger():
    # Make sure logs directory exists in the project root
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("biometrics")
    logger.setLevel(logging.INFO)
    
    # Prevent handler duplication
    if logger.handlers:
        return logger
        
    log_file = os.path.join(log_dir, "app.log")
    
    # File handler with JSON formatter
    file_handler = logging.FileHandler(log_file)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s %(filename)s %(lineno)d'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    # Console handler with standard formatter or json formatter (let's use json formatter for standard logs requested)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # Disable propagation to root logger to avoid duplicate console outputs
    logger.propagate = False
    
    return logger

logger = setup_logger()
