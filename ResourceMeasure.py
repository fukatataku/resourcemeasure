#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function

import os
from datetime import datetime
import time
from contextlib import contextmanager
from subprocess import Popen
import functools

HERE = os.path.dirname(__file__)


class ResourceMeasure(object):
    """
    リソースの使用状況を出力する
    """

    CMD_BASH = "/bin/bash"
    CMD_MEASURE = os.path.join(HERE, "resource_measure")

    _instance = None
    _interval = 5
    _outdir = os.path.join(HERE, "measure_result/{}".format(datetime.now().strftime("%Y%m%d.%H%M%S")))

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ResourceMeasure(cls._interval, cls._outdir)
        return cls._instance

    @classmethod
    def config(cls, interval=None, outdir=None):
        if interval is not None:
            cls._interval = interval

        if outdir is not None:
            cls._outdir = outdir

    def __init__(self, interval, outdir):
        self.interval = interval
        self.outdir = outdir
        self.iostat_filepath = os.path.join(self.outdir, "iostat.txt")
        self.vmstat_filepath = os.path.join(self.outdir, "vmstat.txt")
        self.ndstat_filepath = os.path.join(self.outdir, "ndstat.txt")
        self.free_filepath = os.path.join(self.outdir, "free.txt")
        self.ps_filepath = os.path.join(self.outdir, "ps.txt")
        self.section_filepath = os.path.join(self.outdir, "section.tsv")
        self.sections = []                  # 測定区間ごとに(タイトル, 開始時刻, 終了時刻)を入れる
        self.measure_start = time.time()    # 測定開始時間

        # resource_measure起動
        self.proc = Popen([self.CMD_BASH, self.CMD_MEASURE, str(os.getpid()), str(self.interval), self.outdir])
        time.sleep(1)

    @contextmanager
    def rec(self, title):
        start = datetime.now()
        yield
        end = datetime.now()
        seconds = (end - start).total_seconds()
        self.sections.append((title, start, end, seconds))

    def recmethod(self):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = datetime.now()
                ret = func(*args, **kwargs)
                end = datetime.now()
                seconds = (end - start).total_seconds()
                self.sections.append((title, start, end, seconds))
                return ret
            return wrapper
        return decorator

    def finish(self):
        self.proc.terminate()
        self.output_section_file()
        self.proc.wait()

    def __del__(self):
        self.finish()

    def output_section_file(self):
        tform = "%Y/%m/%d %H:%M:%S"
        with open(self.section_filepath, "w") as fout:
            for title, start, end, seconds in self.sections:
                print("\t".join([title, start.strftime(tform), end.strftime(tform), str(seconds)]), file=fout)


if __name__ == "__main__":

    import multiprocessing as mp

    def do_something(t):
        start = time.time()
        while True:
            li = list(range(1014 * 1024))
            total = 0
            for v in li:
                total += v

            # 指定秒数が経過したら終了
            if (time.time() - start) >= t:
                break

    ResourceMeasure.config(interval=1, outdir="./measure_result")
    resm = ResourceMeasure.get_instance()

    with resm.rec("do something"):
        do_something(15)

    with resm.rec("create process list"):
        proc_list = [mp.Process(target=do_something, args=(10, )) for _ in range(2)]

    with resm.rec("execute processes"):
        for proc in proc_list:
            proc.start()

        for proc in proc_list:
            proc.join()

    resm.finish()
