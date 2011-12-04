from tuptables import Table
import unittest

class ExpandField:
    """ Merge contents of dict in Attributes into main dict"""
    def __init__(self,colname,newcols=[]):
        self.colname = colname
        self.newcols = newcols
    def __call__(self,row):
        import types
        d = row.get(self.colname,None)
        if d == None:
           return True
        if type(d) != types.DictType:
            return False
        r = dict()
        for (k,v) in d.items():
            if k in self.newcols:
                r[k] = v
        return r

class DictMatchAll:
    def __init__(self,cols):
        self.cols = cols
    def __call__(self,row,rule):
        a = filter(lambda a:a[0] in self.cols,row.items())
        b = filter(lambda a:a[0] in self.cols,rule.items())
        if a==b:
            return True
        else:
            return False
    def __repr__(self):
        return "<%s matching %s >" % (self.__class__.__name__,repr(self.cols))

class DictMatchAny:
    def __init__(self,cols):
        self.cols = cols
    def __call__(self,row,rule):
        for k,v in rule.items():
            if k not in self.cols:
                continue
            if k in row and row[k] == v:
                return True
        return False
    def __repr__(self):
        return "<%s matching %s >" % (self.__class__.__name__,repr(self.cols))

class ActThisRow:
    def __call__(*args):
        return 1
    def __repr__(self):
        return "<%s>" % self.__class__.__name__

class ActKeepRow:
    def __call__(*args):
        return 0
    def __repr__(self):
        return "<%s>" % self.__class__.__name__

class ActDiscardRow:
    def __call__(*args):
        return -1
    def __repr__(self):
        return "<%s>" % self.__class__.__name__

class ActMergeRow:
    def __init__(self,cols):
        self.cols = cols
    def __call__(self,row,rule):
        b = filter(lambda a:a[0] in self.cols,rule.items())
        return dict(b)
    def __repr__(self):
        return "<DictMerge merging keys %s>" % (repr(self.cols))

class With:
    def __init__(self,factory,rule):
        self.factory = factory
        self.rule = rule
    def __call__(self,row):
        if self.factory.evaluator(row,self.rule):
            return self.factory.actiontrue(row,self.rule)
        else:
            return self.factory.actionfalse(row,self.rule)
    def __repr__(self):
        r = repr(self.rule)
        f = repr(self.factory)
        s = "\nrule:%s\nFactory:%s" % ( r.replace("\n","\n    "),
                                        f.replace("\n","\n    "))
        return "%s:%s" % (self.__class__.__name__,s.replace("\n","\n    "))

class WithWhen:
    """ Combine When() instance with a rule"""
    def __init__(self,when):
        self.when = when
    def __call__(self,rule):
        return With(self.when,rule)
    def __repr__(self):
        s = "\n" + repr(self.when)
        return "%s:%s" % (self.__class__.__name__,s.replace("\n","\n    "))

class When:
    def __init__(self,evaluator,actiontrue,actionfalse):
        self.evaluator = evaluator
        self.actiontrue = actiontrue
        self.actionfalse = actionfalse
    def __call__(self,row):
        if self.evaluator(row,{}):
            return self.actiontrue(row,{})
        else:
            return self.actionfalse(row,{})
    def __repr__(self):
        e = "\n" + repr(self.evaluator)
        t = "\n" + repr(self.actiontrue)
        f = "\n" + repr(self.actionfalse)
        s = "\nEvaluator:%s\nTrue:%s\nFalse:%s" % ( e.replace("\n","\n    "),
                                                        t.replace("\n","\n    "),
                                                        f.replace("\n","\n    "))
        return "%s:%s" % (self.__class__.__name__,s.replace("\n","\n    "))

class Group:
    def __init__(self, cols, update):
        self.cols = cols
        self.cmp = DictMatchAll(cols)
        self.update = update
    def __call__(self,table):
        left = list(table)
        out = []
        while len(left) >0:
            item = left.pop(0)
            matches = [item.copy()] + filter(lambda z: self.cmp(z,item),left)
            left = filter(lambda z: not self.cmp(z,item),left)
            keys = []
            if len(matches) > 0:
                for match in matches:
                    for key in match.keys():
                        if len([r for r in matches if key in r]) == len(matches):
                            if key not in keys:
                                keys.append(key)
            else:
                keys = item.keys()
            new = {}
            for col in keys:
                new[col] = item[col]
            for key,fn in self.update.items():
                new[key] = fn(matches)
            out.append(new)
        return table.__class__(out)

class TestGroup(unittest.TestCase):
    def test_group(self):
        t = [{"a":"A","b":"B","c":"d"},
             {"a":"A","b":"B","c":"d"},
             {"a":"A","b":"q","c":"C"}]
        ex= [{"a":"A","b":"B","c":"d", "group":[
             {"a":"A","b":"B","c":"d"},
             {"a":"A","b":"B","c":"d"}] 
             },
             {"a":"A","b":"q","c":"C", "group":[
             {"a":"A","b":"q","c":"C"}] 
             }
            ]
        r = Group(["a","b"],{"group":lambda rows:rows})(t)
        self.assertEqual(r, ex)

class TestWithWhen(unittest.TestCase):
    def test_with(self):
        a={"Value":20}
        b={"Value":10}

        w1 = With(  When(   DictMatchAll(["Value"]),
                            ActMergeRow(["test"]),
                            ActKeepRow()),
                    {"Value":10,"test":20})
        
        self.assertEqual(w1(a), 0)
        self.assertEqual(w1(b), {"test":20})

        w2 = With(  When(   DictMatchAll(["Value"]),
                            ActDiscardRow(),
                            ActKeepRow()),
                    {"Value":10,"test":20})

        self.assertEqual(w2(a), 0)
        self.assertEqual(w2(b), -1)

    def test_withwhen(self):
        t= Table([{"Value":20,"name":"twintig"},{"Key":5,"Value":10,"name":"tien"}])
        r= Table([{"Value":20,"Device":"D20","Key":"2"},  {"Key":5,"Value":10,"Device":"D10"}])
        w = WithWhen(When(DictMatchAny(["Value","Key"]),ActMergeRow(["Device"]),ActKeepRow()))

        e= Table([{"Value":20,"name":"twintig","Device":"D20"},
                  {"Key":5,"Value":10,"name":"tien",   "Device":"D10"}])
        self.assertEqual(t*(r*w), e)

    def test_withwhenfilter(self):
        t= Table([{"Value":20,"name":"twintig"},{"Value":10,"name":"tien"}])
        r= Table([{"Value":20,"Device":"D20","Key":"2"}])
        w = WithWhen(When(DictMatchAny(["Value"]),ActDiscardRow(),ActKeepRow()))
        e= Table([{"Value":10,"name":"tien"}])
        self.assertEqual(t*(r*w), e)

if __name__ == "__main__":
    unittest.main()

