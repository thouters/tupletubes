#!/usr/bin/python
# -*- coding: utf-8 -*-
# calculate modulo 97 for a list of numbers
from csvio import *
from filters import *
from sys import stdin,stdout,exit
from string import Template

if __name__ == "__main__":
    acodes = CsvRead(open("in/acodes.csv")) 
    tpl = Template(open("in/testpr.txt").read())
    o = open("out/test.txt","w")
    for l in acodes:
        l["checksum"] = int(l["barcode"]) % 97
        o.write(tpl.substitute(l))
