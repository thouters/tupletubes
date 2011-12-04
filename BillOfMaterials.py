#!/usr/bin/python
# -*- coding: utf-8 -*-

# process a flat Bill of materials list
# filter out do-not-mount list
# include prototype component cost calculation.

from copy import deepcopy
from tuptables.io import *
from tuptables.filters import *
from tuptables.visual import *
from tuptables import Table
import vendors

from sys import stdin,stdout,exit

if __name__ == "__main__":

    gui = TableInspector()

    excludes = CsvRead(open("in/Excludes.csv")) * ValuesToPy
    gui.add(excludes,"Excludes")

    discretes = CsvRead(open("in/DiscretesFromFarnell.csv")) * ValuesToPy
    gui.add(discretes,"discretes")

    vendorprod = CsvRead(open("in/VendorProduct.csv")) * ValuesToPy
    gui.add(vendorprod,"VendorProduct")

    bom = CsvRead(open("in/gate4v2.csv")) * ValuesToPy
    bom *= (discretes * WithWhen(When(DictMatchAll(["Value","Device"]),ActMergeRow(["Farnell"]),ActKeepRow())))
    bom *= (excludes * WithWhen(When(DictMatchAny(["Part","Value","Device"]),ActDiscardRow(),ActKeepRow())))
    gui.add(bom,"BOM")

    cost = deepcopy(bom) 
    cost %= Group(["Value","Device"],{"Parts": lambda rows:[row["Part"] for row in rows], "Qty":lambda rows:len(rows)})
    cost %= vendors.PriceInQtys([1,10,20],[vendors.VendorCache(vendors.Farnell)])
    cost *= (vendorprod * WithWhen(When(DictMatchAny(["Farnell"]),ActMergeRow(["Vendor","price1"]),ActKeepRow())))

    cost += {"Parts":   "All",
             "price1":  lambda rows: sum([row.get("Qty",0)*float(row.get("price1",0)) for row in rows]),
             "price10": lambda rows: float(sum([row.get("Qty",0)*row.get("price10",float(row.get("price1",0))) for row in rows])),
             "price20": lambda rows: sum([row.get("Qty",0)*row.get("price20",float(row.get("price1",0))) for row in rows])
             }

    cost.setColumns(without=["Description","Attributes","Part"])
    CsvWrite(open("out/cost.csv",'w'),cost)
    DokuWrite(open("out/cost.dok",'w'),cost)
    gui.add(cost,"Kostprijs")

    currents = ["I3V","I5V","I24V"]
    cur = deepcopy(bom) 
    cur *= ExpandField("Attributes",currents)

    def nrofcurrents(row):
        return len([k for k in row.keys() if k in currents])

    cur *= When(lambda row,rule: nrofcurrents(row)>0, ActKeepRow(), ActDiscardRow())

    def SumOfColumn(key):
        return lambda rows: sum([float(row.get(key,0)) for row in rows])

    cur += {"Description":"Sum",
            "I5V": SumOfColumn("I5V"),
            "I3V": SumOfColumn("I3V"),
            "I24V": SumOfColumn("I24V")
            }

    cur.setColumns(["Part","Value","Description","I5V","I3V","I24V"])
    CsvWrite(open("out/CurrentCalc.csv",'w'),cur)
    gui.add(cur,"Currents")

    order = deepcopy(bom)
    order %= Group(["Value","Device"],{"Parts": lambda rows:[row["Part"] for row in rows], "Qty":lambda rows:len(rows)})
    order %= vendors.PriceInQtys([1,10,20],[vendors.VendorCache(vendors.Farnell)])
    order *= lambda row: {"Qty10":row["Qty"]*10}
    order *= When(lambda row,rule: lambda row: "Vendor" in row and row["Vendor"]=="Farnell", ActKeepRow(), ActDiscardRow())
    order *= When(lambda row,rule: lambda row: "Value" in row and row["price1"]<1, ActKeepRow(), ActDiscardRow())
    order.setColumns(["VendorCode","Qty10","Parts"])
    CsvWrite(open("out/Order.csv",'w'),order)
    gui.add(order,"Order")

    prod = deepcopy(bom) 
    prod %= Group(["Value","Device"],{"Parts": lambda rows:[row["Part"] for row in rows], "Qty":lambda rows:len(rows)})
    prod %= Group(["Value","Device"],{"Parts": lambda rows:[row["Part"] for row in rows], "Qty":lambda rows:len(rows)})
    prod *= (CsvRead(open("in/ListSmds.csv")) * WithWhen(When(DictMatchAny(["Part","Value"]),ActMergeRow(["Smd"]),ActKeepRow())))
    prod *= (CsvRead(open("in/ListBottom.csv")) * WithWhen(When(DictMatchAll(["Part"]),ActMergeRow(["Bottom"]),ActKeepRow())))
    prod.sort(lambda x,y: cmp(x.get("VendorCode",0),y.get("VendorCode",0)))
    prod.sort(lambda x,y: cmp(x.get("Smd",0),y.get("Smd",0)))
    prod.sort(lambda x,y: cmp(x.get("Bottom",0),y.get("Bottom",0)))
    prod.setColumns(["Value","Farnell","Part","Smd","Bottom"])
    CsvWrite(open("out/Production.csv",'w'),prod)
    DokuWrite(open("out/Production.dok",'w'),prod)
    gui.add(prod,"Productie")

    gui.show()
