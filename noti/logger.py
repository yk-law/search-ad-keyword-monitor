import logging
import logging.config
from logging.handlers import TimedRotatingFileHandler
import time
import os

from config import LOGGING_FILE_PATH
from config import LOGGING_FILE_MAX_BACKUP_COUNT

class MyTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(
        self,
        filename,
        when="midnight",
        interval=1,
        backupCount=0,
        encoding=None,
        delay=False,
        utc=False,
        atTime=None,
    ):
        self.prefix = filename
        super().__init__(
            filename,
            when,
            interval,
            backupCount,
            encoding,
            delay,
            utc,
            atTime,
        )

    def doRollover(self) -> None:
        if self.stream:
            self.stream.close()
            self.stream = None

        # 현재 시간으로 새 파일명 생성
        current_time = time.strftime("%Y%m%d", time.localtime())
        current_time = int(time.time())
        dst_now = time.localtime(current_time)[-1]
        t = self.rolloverAt - self.interval
        # new_log_file_name = self.baseFilename + "." + current_time
        if self.utc:
            time_tuple = time.gmtime(t)
        else:
            time_tuple = time.localtime(t)
            dst_then = time_tuple[-1]
            if dst_now != dst_then:
                if dst_now:
                    addend = 3600
                else:
                    addend = -3600
                time_tuple = time.localtime(t + addend)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, time_tuple)

        if not os.path.exists(dfn) and os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, dfn)
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.mode = "a"
            self.stream = self._open()
        new_rollover_at = self.computeRollover(current_time)
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval
        if (self.when == "MIDNIGHT" or self.when.startswith("W")) and not self.utc:
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if dst_now != dst_at_rollover:
                if not dst_now:
                    addend = -3600
                else:
                    addend = 3600
                new_rollover_at += addend
        self.rolloverAt = new_rollover_at

        # # 기존 파일을 새 파일명으로 변경
        # if os.path.exists(self.baseFilename):
        #     os.rename(self.baseFilename, new_log_file_name)

        # # 새 파일 스트림 열기
        # if not self.delay:
        #     self.stream = self._open()


def setup_logger():
    log_file_path = LOGGING_FILE_PATH + "/noti.log"

    logging_dict_config = {
        "version": 1,
        "formatters": {
            "default": {
                "format": "%(asctime)s.%(msecs)03d %(levelname)s %(thread)d - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "file": {
                "()": MyTimedRotatingFileHandler,
                "formatter": "default",
                "filename": log_file_path,
                "when": "midnight",
                "interval": 1,
                "backupCount": LOGGING_FILE_MAX_BACKUP_COUNT,
            },
        },
        "loggers": {
            "noti": {
                "level": "INFO",
                "handlers": ["default", "file"],
                "propagate": False,
            },
            # Uvicorn 로거 설정
            "uvicorn": {
                "level": "WARNING",
                "handlers": ["default", "file"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["default", "file"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_dict_config)
    return logging_dict_config
