import unittest
import copy 

class Table(list):
    """
        Table * {} 
        -> merge dict into rows
        Table * function 
        -> True: keep row
           False: remove row
           Dict: replace row
        Table * [{},fn,...]
        -> for each line: evaluate list contents, merge results

        Table + Table
        -> add lines
        Table + fn: 
    """
    def __getslice__(self, i, j):
        return self.__getitem__(slice(i, j))
    def __setslice__(self, i, j, seq):
        return self.__setitem__(slice(i, j), seq)
    def __delslice__(self, i, j):
        return self.__delitem__(slice(i, j)) 
    def __iadd__(self,other):
        from types import DictType, FunctionType
        if type(other) == DictType:
            o = other.copy()
            for k,v in other.items():
                if type(v) == FunctionType:
                    o[k] = v(self)
                else:
                    o[k] = v
            self.append(o)
        elif callable(other):
            self.append(other(self))
        else:
            self.append(other)
        return self

    def __mod__(self,other):
        if not callable(other):
            raise Exception
        return other(self)

    def __mul__(self, other):
        try:
            iable = iter(other)
            if other.__class__ == dict:
                raise TypeError
        except TypeError:
            other = [other]

        result = []
        for row in self:
            new=row.copy()
            updates =[]
            for mp in other:
                if callable(mp):
                    ret = mp(row.copy())
                    if ret==0:
                        continue
                    if ret.__class__ == dict:
                        updates.append(ret)
                        continue
                    if ret == 1:
                        new=row.copy()
                    elif ret == -1:
                        new=False
                    elif callable(ret):
                        new=ret
                    updates = []
                    break
                elif mp.__class__ == dict:
                    updates.append(mp)
                else:
                    raise Exception(type(mp),mp.__class__.__name__)
            if new:
                if len(updates):
                    for u in updates:
                        new.update(u)
                result.append(new)
        return self.__class__(result)
    def __repr__(self):
        s = ""
        for row in self:
            s+= repr(row)+",\n"
        return "[%s]" % s[:-2]

    def __mod__(self,other):
        return other(self)

    def colrename(self,d):
        for i,row in enumerate(self):
            for old,new in d.items():
                if old in self[i]:
                    self[i][new] = self[i][old]
                    del(self[i][old])

    def __init__(self,cloneobj=False,newlist=False,cols=False):
        if newlist:
            list.__init__(self,newlist)
        elif cloneobj:
            list.__init__(self,cloneobj)
        else:
            list.__init__(self)

        clonecols = getattr(cloneobj,"cols",False)

        if cols:
            self.cols = cols
        elif clonecols !=False:
            self.cols = clonecols
        else:
            self.cols = self.getColumns()
            
    def clone(self):
        return copy.deepcopy(self)

    def getColumns(self):
        def longestrow(a,b):
            if b.__class__ != dict:
                return a
            if len(a)>len(b):
                return a
            else:
                return b
        # row with most columns probably is an original with columns added,
        # and therefore probably maintained original column order
        cols = reduce(lambda l,row: longestrow(l,row),self,{}).keys()
        for row in self:
            if row.__class__ != dict:
                continue
            cols += filter(lambda c: c not in cols,row.keys())
        return cols
    def setColumns(self,cols=False,without=[]):
        if cols ==False:
            self.cols = self.getColumns()
        else:
            self.cols = cols
        self.cols = filter(lambda c: c not in without,self.cols)
    def toText(self):
        widths = []
        headerrow = dict(zip(self.cols,self.cols))
        ctable = [headerrow]+self
        def rowlen(row):
            return len(str(row.get(col,"")))
        for col in self.cols:
            maxlen = reduce(lambda longest,row: max(longest,rowlen(row)),ctable,0)
            widths.append((col,maxlen))

        lines = [(headerrow,'^')]
        lines += map(lambda row: (row,'|'),self)
 
        r = ""
        for row,joinchar in lines:
            row = map(lambda (colname,width): " %s " % str(row.get(colname,"")).ljust(width),widths)
            r += "%s%s%s\n" % (joinchar,joinchar.join(row),joinchar)
        return r

class TestTable(unittest.TestCase):
    def test_muldict(self):
        abcd = Table([{"a":"b"},{"c":"d"}])
        abijcdij = Table([{"a":"b","i":"j"},{"c":"d","i":"j"}])
        i = {"i":"j"}
        self.assertEqual(abcd*i,abijcdij)
    def test_mullambda(self):
        abcd = Table([{"a":"b"},{"c":"d"}])
        abijcdij = Table([{"a":"b","i":"j"},{"c":"d","i":"j"}])
        i = {"i":"j"}
        self.assertEqual(abcd*(lambda x: i),abijcdij)
    def test_iadd(self):
        ababac = Table([{"a":"A","b":"B"},{"a":"A","b":"z"},{"a":"A","c":"C"}])
        ababac += {"tablen":lambda table: len(table),"Foo":"Bar"}
        er = Table([{"a":"A","b":"B"},{"a":"A","b":"z"},{"a":"A","c":"C"},{"tablen":3,"Foo":"Bar"}]) 
        self.assertEqual(ababac, er)

if __name__ == "__main__":
    unittest.main()
