#!/usr/bin/python
# -*- coding: utf-8 -*-
from csvio import *
from sys import stdin,stdout

if __name__ == "__main__":
    DokuWrite(stdout,Presentable(DokuRead(stdin)))
