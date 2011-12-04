
import BeautifulSoup
import urllib, re
import pickle

class PriceInQtys:
    """ Determine individual component cost when component is bought in given BOARD quantitys"""
    def __init__(self,quantities=[],vendormap=[]):
        self.quantities = quantities
        self.vendormap = vendormap
    def __call__(self,table):
        for i,row in enumerate(table):
            if not "Farnell" in row:
                continue
            usableVendor = filter(lambda x: x.handles(row),self.vendormap)
            if usableVendor == []:
                continue
            usableVendor = usableVendor[0]
            price = usableVendor.lookup(row)
            row["Vendor"] = usableVendor.name
            row["VendorCode"] = row["Farnell"][2:]
            for q in self.quantities:
                row["price%s"%q] = price.resolve(row.get("Qty",1)*q)
            table[i] = row
        return table

class Price:
    # list of tuple(min,max,price)
    # where (x,CEIL,price) == (x,0,price)

    def __init__(self,x=[]):
        self.ranges = [] 

    def __repr__(self):
        x= "Price range resolver\n"
        for p in self.ranges:
            x += "%s - %s  --> %s\n" %(p[0],p[1],p[2])
        return x

    def resolve(self,qty):
        min = 0
        max = 1
        price = 2
        ranges = sorted(self.ranges,lambda x,y: cmp(x[min], y[min]))
        for r in ranges:
            if r[max] == 0:
                return r[price]
            if qty > r[max]:
                continue
            else:
                return r[price]

    def addrange(self,min,max,price):
        self.ranges.append((min,max,price))

class Vendor:
    name = "UVendor"
    key = "Farnell" #data[key] is used to match against
    def handles(self,x):
        return True

    def lookup(self,row):
        x = Price()
        x.addrange(1,0,0)
        return x

class VendorCache:
    # Adaptor, save partid,prices in pickle
    def __init__(self,klass):
        self.c = klass()
        self.dbfile = "cache/%s.pickle" % klass.__name__
        try:
            f = open(self.dbfile,'r')
            self.cache = pickle.load(f)
            f.close()
        except:
            self.cache = {}

    def lookup(self,data):
        partid = data[self.c.key]
        if not partid in self.cache.keys():
            p = self.c.lookup(data)
            self.cache[partid] = p
            f = open(self.dbfile,'w')
            pickle.dump(self.cache,f)
            f.close()
        else:
            p = self.cache[partid]
        return p

    def __getattr__(self,name):
        return getattr(self.c,name)

class Farnell(Vendor):
    listurl = "http://be.farnell.com/jsp/search/productdetail.jsp?sku=%s"
    name = "Farnell"
    idcode = "F#"

    def __init__(self):
        pass
    def handles(self,x):
        if len(x) > 2 and self.key in x and x[self.key][0:2] == self.idcode:
            return True
        else:
            return False
    def lookup(self,x):
        partid = x[self.key][2:]
        remotefile = urllib.urlopen(self.listurl % partid)
        contents = remotefile.read().decode('latin-1')
        remotefile.close()
        soup = BeautifulSoup.BeautifulSoup(contents)
        # debug -- save to disk
        #x = open("".join(map(lambda x: x.name,tables)),'w')
        #x.write(soup.prettify())
        #x.close()
        x = Price()
        div = soup.html.body.findAll("div", {"id":"price"})[0]
        for tr in div.findAll('tr'):
            tds = tr.findAll('td')
            if len(tds):
                q = tds[0].contents[0].strip()
                if q.find('+') !=  -1:
                    q = q.split("+")[0]
                    q = [int(q),0]
                else:
                    q = map(int,q.split("&nbsp;-&nbsp;"))
                p = tds[1].contents[0].strip()[:-7].replace(',','.')
                x.addrange(q[0],q[1],float(p))
        return x

