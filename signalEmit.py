#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Date: 2019/11/12
# @Author: Tigerots


from PyQt5 import QtCore


class SignalEmit(object):
    # 信号槽机制：设置信号与槽，用于涉及界面的模块间通信
    signal_write_msg = QtCore.pyqtSignal(str)# 接收消息
    signal_list_ip = QtCore.pyqtSignal(str)# 客户端IP列表


















# ======================================================
