#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'kun'


# 日志类
import logging


class Logger:
    def __init__(self, log_name, file_name):
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.INFO)

        fh = logging.FileHandler(file_name)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -[line:%(lineno)d]%(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        #ch = logging.StreamHandler()
        #ch.setLevel(logging.INFO)
        #ch.setFormatter(formatter)
        #self.logger.addHandler(ch)

    def get_logger(self):
        return self.logger

log = Logger('sync_dashboard', './sync_dashboard.log').get_logger()