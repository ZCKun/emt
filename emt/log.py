import os
import logging
from datetime import datetime

log_level = logging.DEBUG
log_save_path = "emt_logs"
if not os.path.exists(log_save_path):
    os.mkdir(log_save_path)

today_dt = datetime.today().strftime("%Y%m%d")
logger = logging.getLogger('emttrade_logger')
logger.setLevel(log_level)

file_handler = logging.FileHandler(os.path.join(log_save_path, f'emttrade_{today_dt}.log'))
file_handler.setLevel(log_level)

fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s')
file_handler.setFormatter(fmt)

logger.addHandler(file_handler)

logger.debug('logger init')
logger.info('logger init')
logger.warning('logger init')
logger.error('logger init')
