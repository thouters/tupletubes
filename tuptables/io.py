from tuptables import Table
import unittest
import csv

def ValueToPy(v):
    if len(v) >= 3 and "=" in v:
        d = dict()
        for k,u in map(lambda i: i.split("="),v.strip().split(',')):
            d[k] = u
        return d
    elif len(v) >= 3 and "," in v:
        return v.strip().split(',')
    else:
        return v

def ValuesToPy(row):
    l = dict()
    for c,v in row.items():
        l[c] = ValueToPy(v)
    return l

def ValueToStr(v):
    if type(v) == list:
        return   ",".join(v)
    elif type(v) == dict:
        sl = []
        for (k,u) in v.items():
            sl.append("%s=%s"%(k,u))
        return ','.join(sl)
    else:
        return str(v)

def ValuesToStr(row):
    l = dict()
    for c,v in row.iteritems():
        l[c] = ValueToStr(v)
    return l

def CsvRead(*args,**kwargs):
    t = Table()
    rlist = ["delimiter","dialect"]
    rargs = dict(filter(lambda (k,v): k in rlist,kwargs.items()))
    rows = list(csv.reader(args[0],**rargs))
    cols = rows[0]
    rows = rows[1:]
    for row in rows:
        x = {}
        for i,col in enumerate(cols):
            if row[i] != "":
                x[col] = row[i]
        t.append(x)
    return t

def CsvWrite(*args,**kwargs):
    csvargs = ["delimiter","dialect"]
    csvargs = dict(filter(lambda (k,v): k in csvargs,kwargs.items()))
    dst = csv.writer(args[0], **csvargs)
    table = args[1]

    lines = []
    for row in map(ValuesToStr,table):
        r = map(lambda x: row.get(x,""),table.cols)
        lines.append(r)

    for row in [table.cols]+lines:
        dst.writerow(row)

def DokuRead(*args,**kwargs):
    t = Table()
    lines = [line for line in args[0]]
    cols = []
    while True:
        head = lines.pop(0).strip()
        if len(head) ==0 or head[0] != "^":
            continue
        else:
            cols = head.split("^")[1:-1]
            break
    if cols == []:
        raise Exception
    cols = map(str.strip,cols)
    lines = map(str.strip,lines)
    rows = filter(lambda x: len(x) >2 and x[0] == '|' and x[-1:] == '|',lines)
    rows = map(lambda rstr: map(str.strip,rstr.split("|")[1:-1]),rows)
    for row in rows:
        x = {}
        for i,col in enumerate(cols):
            if row[i] != "":
                x[col] = row[i]
        t.append(x)
    return t

def DokuWrite(dst,table):
    headerrow = dict(zip(table.cols,table.cols))
    rows = [headerrow]+map(ValuesToStr,table)

    widths = []
    for col in table.cols:
        def longest(current,row):
            return max(current,len(row.get(col,"")))
        length = reduce(longest,rows,0)
        widths.append((col,length))

    lines = [(rows[0],'^')]+ map(lambda row: (row,'|'),rows[1:])
    for row,joinchar in lines:
        row = map(lambda (colname,width): " %s " % row.get(colname,"").ljust(width),widths)
        dst.write("%s%s%s\n" % (joinchar,joinchar.join(row),joinchar))

class TestValues(unittest.TestCase):
    stable = {"a":"b,c,d","b":"i=j,k=l","c":"test" }
    ptable = {"a":["b","c","d"],"b":{"i":"j","k":"l"},"c":"test"}
    def TestValuesToPy(self):
        self.assertEqual(ValuesToPy(self.stable), self.ptable)
    def TestValuesToStr(self):
        self.assertEqual(ValuesToStr(self.ptable), self.stable)
class TestPresentable(unittest.TestCase):
    def test_repr(self):
        ababac = Table([{"a":"A","b":"B"},{"a":"A","b":"z"},{"a":"A","c":"C"}])
        ababac.setColumns(["b","c"])
        i = ababac.toText()
        s = "^ b ^ c ^\n"
        s+= "| B |   |\n"
        s+= "| z |   |\n"
        s+= "|   | C |\n"
        self.assertEqual(s, i)

class TestDokuIO(unittest.TestCase):
    def test_dokuwrite(self):
        ababac = Table([{"a":"A","b":"B"},{"a":"A","b":"z"},{"a":"A","c":"C"}])
        import StringIO
        null = open("/dev/null","w")
        DokuWrite(null,ababac)

        ababac.setColumns(["b","c"])
        stream = StringIO.StringIO()
        DokuWrite(stream,ababac)
        s = "^ b ^ c ^\n"
        s+= "| B |   |\n"
        s+= "| z |   |\n"
        s+= "|   | C |\n"
        self.assertEqual(s, stream.getvalue())
    def test_dokuread(self):
        ababac = Table([{"b": "B"}, {"b": "z"}, {"c": "C"}])
        import StringIO
        s = "^ b ^ c ^\n"
        s+= "| B |   |\n"
        s+= "| z |   |\n"
        s+= "|   | C |\n"
        stream = StringIO.StringIO(s)
        r = DokuRead(stream)
        self.assertEqual(r, ababac)

class TestCsvIO(unittest.TestCase):
    def test_csvwrite(self):
        ababac = Table([{"a":"A","b":"B"},{"a":"A","b":"z"},{"a":"A","c":"C"}])
        import StringIO
        null = open("/dev/null","w")
        CsvWrite(null,ababac)

        ababac.setColumns(["b","c"])
        stream = StringIO.StringIO()
        CsvWrite(stream,ababac)
        s = """b,c\r\n"""
        s+= """B,\r\n"""
        s+= """z,\r\n"""
        s+= """,C\r\n"""
        self.assertEqual(s, stream.getvalue())

    def test_csvread(self):
        ababac = Table([{"b": "B"}, {"b": "z"}, {"c": "C"}])
        import StringIO
        s = """b,c\r\n"""
        s+= """B,\r\n"""
        s+= """z,\r\n"""
        s+= """,C\r\n"""
        stream = StringIO.StringIO(s)
        r = CsvRead(stream)
        self.assertEqual(r, ababac)

if __name__ == "__main__":
    unittest.main()
