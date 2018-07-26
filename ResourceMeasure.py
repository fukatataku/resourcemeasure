#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function

import os
from datetime import datetime
import time
from contextlib import contextmanager
from subprocess import Popen
import functools
from cProfile import Profile

HERE = os.path.dirname(__file__)


class ResourceMeasure(object):
    """
    リソースの使用状況を出力する
    """

    CMD_BASH = "/bin/bash"
    CMD_MEASURE = os.path.join(HERE, "resource_measure")

    _instance = None
    _interval = 5
    _profiling = False
    _outdir = os.path.join(HERE, "measure_result/{}".format(datetime.now().strftime("%Y%m%d.%H%M%S")))

    @classmethod
    def get_instance(cls):
        """ シングルトンインスタンスを取得する """
        if cls._instance is None:
            cls._instance = ResourceMeasure(cls._interval, cls._outdir, cls._profiling)
        return cls._instance

    @classmethod
    def config(cls, interval=None, profiling=None, outdir=None):
        """ 各種設定値を設定する """
        if interval is not None:
            cls._interval = interval

        if outdir is not None:
            cls._outdir = outdir

        if profiling is not None:
            cls._profiling = profiling

    @classmethod
    @contextmanager
    def cls_measure(cls, title):
        """ 測定を実行する(コンテキストマネージャ) """
        raise NotImplementedError()

    @classmethod
    def cls_measured(cls, title=None):
        raise NotImplementedError()

    def __init__(self, interval, outdir, profiling):
        self.interval = interval
        self.outdir = outdir
        self.profiling = profiling
        self.profile = Profile() if self.profiling else None
        # self.iostat_filepath = os.path.join(self.outdir, "iostat.txt")
        # self.vmstat_filepath = os.path.join(self.outdir, "vmstat.txt")
        # self.ndstat_filepath = os.path.join(self.outdir, "ndstat.txt")
        # self.free_filepath = os.path.join(self.outdir, "free.txt")
        # self.ps_filepath = os.path.join(self.outdir, "ps.txt")
        self.section_filepath = os.path.join(self.outdir, "section.tsv")
        self.profile_filepath = os.path.join(self.outdir, "profile.prof")
        self.sections = []                  # 測定区間ごとに(タイトル, 開始時刻, 終了時刻)を入れる
        self.measure_start = time.time()    # 測定開始時間

        # 測定スクリプト起動
        self.proc = Popen([self.CMD_BASH, self.CMD_MEASURE, str(os.getpid()), str(self.interval), self.outdir])
        time.sleep(1)

        # プロファイリング開始
        if self.profiling:
            self.profile.enable()

    @contextmanager
    def measure(self, title):
        """ 測定を実行する(コンテキストマネージャ) """
        start = datetime.now()
        yield
        end = datetime.now()
        seconds = (end - start).total_seconds()
        self.sections.append((title, start, end, seconds))

    def measured(self, title=None):
        """ 測定を実行する(デコレータ) """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = datetime.now()
                ret = func(*args, **kwargs)
                end = datetime.now()
                seconds = (end - start).total_seconds()
                self.sections.append((func.func_name if title is None else title, start, end, seconds))
                return ret
            return wrapper
        return decorator

    def finish(self):
        """ 終了する """
        self.output_section_file()

        # プロファイリング終了
        if self.profiling:
            self.profile.create_stats()
            self.profile.dump_stats(self.profile_filepath)

        # 測定スクリプト停止
        self.proc.terminate()
        self.proc.wait()

    def __del__(self):
        self.finish()

    def output_section_file(self):
        """ 区間ごとの処理時間集計ファイルを出力する """
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

    ResourceMeasure.config(interval=1, profiling=True, outdir="./measure_result")
    resm = ResourceMeasure.get_instance()

    with resm.measure("do something"):
        do_something(5)

    with resm.measure("create process list"):
        proc_list = [mp.Process(target=do_something, args=(5, )) for _ in range(2)]

    with resm.measure("execute processes"):
        for proc in proc_list:
            proc.start()

        for proc in proc_list:
            proc.join()

    @resm.measured()
    def do_something2(t):
        start = time.time()
        while True:
            li = list(range(1014 * 1024))
            total = 0
            for v in li:
                total += v

            # 指定秒数が経過したら終了
            if (time.time() - start) >= t:
                break

    do_something2(1)
    do_something2(2)
    do_something2(3)

    resm.finish()
