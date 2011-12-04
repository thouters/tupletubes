import gtk
class TableInspector:
    def __init__(self,title="TupTables GUI"):
        try:
            from quidgets.widgets.dictionary_grid import DictionaryGrid 
            self.tblwidget = DictionaryGrid
        except:
            def plaingrid(table,tablecols):
                b = gtk.TextBuffer()
                b.set_text(table.toText())
                x = gtk.TextView(b)
                import pango
                x.modify_font(pango.FontDescription("monospace"))
                x.show()
                return x
            self.tblwidget = plaingrid
        self.wnd = gtk.Window()
        self.wnd.set_title(title)
        self.nbook = gtk.Notebook()
        self.nbook.show()
        self.wnd.add(self.nbook)
        self.wnd.connect('destroy',self.__destroy)
        self.wnd.set_default_size(800,600)
    def show(self):
        self.wnd.show()
        gtk.main()
        
    def __destroy(self,x):
        gtk.main_quit()

    def add(self,a,title=""):
        s = gtk.ScrolledWindow()
        d = self.tblwidget(a,a.cols) 
        s.add(d)
        self.nbook.append_page(s, gtk.Label(title))
        s.show()
        d.show()

