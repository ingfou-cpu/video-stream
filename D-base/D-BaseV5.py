import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from tkinter import *
from tkinter import scrolledtext
from tkinter import ttk, simpledialog, Text, LabelFrame, messagebox
import pyodbc
import pandas as pd
import os
from elevate import elevate

elevate(show_console=False)

fen=Tk()
fen.geometry("820x400")
fen.title('بسم الله الرحمن الرحيم')
from openpyxl import Workbook
db_path = r'E:\Khaibar\Nom.accdb' 
mdp = 'jinbei'
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={db_path};'
    f'PWD={mdp};'
)
try:
    conn = pyodbc.connect(conn_str)
    messagebox.showinfo(title='شكرا على الانتظار', message='تم الإتصال')
    print('تم الإتصال')
except pyodbc.Error as e:
    messagebox.showerror(title='خطأ', message=f'لم يتم الإتصال...تحقق من الملف\n\n{e}')
    fen.destroy()

def make_menu(w):
    global the_menu
    the_menu = Menu(fen, tearoff=0)
    the_menu.add_command(label="Cut")
    the_menu.add_command(label="Copy")
    the_menu.add_command(label="Paste")

def show_menu(e):
    ww = e.widget
    the_menu.entryconfigure("Cut",
    command = lambda: ww.event_generate("<<Cut>>"))
    the_menu.entryconfigure("Copy",
    command = lambda: ww.event_generate("<<Copy>>"))
    the_menu.entryconfigure("Paste",
    command = lambda: ww.event_generate("<<Paste>>"))
    the_menu.tk.call("tk_popup", the_menu, e.x_root, e.y_root)

make_menu(fen)

cur = conn.cursor()
var = StringVar(fen, value=0)
var1 = StringVar(fen, value=0)
txta = Text(fen, font=("Times New Roman", 12),wrap = WORD, height=20, width=100)

lib5 = LabelFrame(fen, text='SECTEUR', font=("Times New Roman", 12, 'bold'))
lib4 = LabelFrame(fen, text='LIBELLE SOUS SECTEUR', font=("Times New Roman", 12, 'bold'))
lib3 = LabelFrame(fen, text='CHAPITRE', font=("Times New Roman", 12, 'bold'))
liba = LabelFrame(fen, text='CHAPITRE+100', font=("Times New Roman", 12, 'bold'))
lib2 = LabelFrame(fen, text='COMMUNE', font=("Times New Roman", 12, 'bold'), width=4)
lib1 = LabelFrame(fen, text='LIBELLE Operation', font=("Times New Roman", 12, 'bold'))
lib = LabelFrame(fen, text='LIBELLE SOUS SECTEUR', font=("Times New Roman", 12, 'bold'))
lib6 = LabelFrame(fen, text='SOUS_SECTEUR txt', font=("Times New Roman", 12, 'bold'))
lib7 = LabelFrame(fen, text='N_OPERATI txt', font=("Times New Roman", 12, 'bold'))
lib8 = LabelFrame(fen, text='CHAPITRE_ nbr', font=("Times New Roman", 12, 'bold'))
#lib9 = LabelFrame(fen, text='CHAPITRE+100 nbr', font=("Times New Roman", 12, 'bold'))
lib10 = LabelFrame(fen, text='LIBELLE_OP txt', font=("Times New Roman", 12, 'bold'), width=4)
lib11 = LabelFrame(fen, text='AP_INITIAL nbr', font=("Times New Roman", 12, 'bold'))
lib12 = LabelFrame(fen, text='COMMUNE txt', font=("Times New Roman", 12, 'bold'))

def ajou ():
    mash_hide_tabl_()
    mash_hide_connect()

    lib6.grid(row=1, sticky=W)
    txt6 = Entry(lib6)
    txt6.grid(row=2, columnspan=2, sticky=W)

    lib7.grid(row=3, sticky=W)
    txt7 = Entry(lib7)
    txt7.grid(row=4, columnspan=2, sticky=W)

    lib8.grid(row=5, sticky=W)
    txt8 = Entry(lib8,textvariable=var)
    txt8.grid(row=6, columnspan=2, sticky=W)
    #lib9.grid(row=5, column=2, sticky=W)
    #txt9 = Entry(lib9)
    #txt9.grid(row=6, columnspan=2, sticky=E)
    lib10.grid(row=7, sticky=W)
    txt10 = Entry(lib10)
    txt10.grid(row=8, columnspan=2, sticky=W)

    lib11.grid(row=9, columnspan=1 + 2, sticky=W)
    txt11 = Entry(lib11,textvariable=var1)
    txt11.grid(row=10, sticky=W)

    lib12.grid(row=11, columnspan=2, sticky=W)
    txt12 = Entry(lib12)
    txt12.grid(row=12, sticky=W)
    ''' 
    #ent3 = Entry(fen)
    #ent3.insert(END, 'Secteur')
    #ent3.bind('<Return>', ajou)
    #ent3.grid(row=1)
    #ent4 = Entry(fen)
    #ent4.insert(END, 'N_SS')
    #ent4.bind('<Return>', ajou)
    #ent4.grid(row=2)
    #ent5 = Entry(fen)
    #ent5.insert(END, 'LIBELLE_SOUS_SECTEUR')
    #ent5.bind('<Return>', ajou)
    #ent5.grid(row=3)
    #ent6 = Entry(fen)
    #ent6.insert(END, 'CHAPITRE_')
    #ent6.bind('<Return>', ajou)
    #ent6.grid(row=4)
    #ent7 = Entry(fen)
    #ent7.insert(END, 'N_FIXE_OP')
    #ent7.bind('<Return>', ajou)
    #ent7.grid(row=5)
    '''

    def tem():
        foufou = [(str(txt6.get()),str(txt7.get()), int(txt8.get()),
                   str(txt10.get()),int(txt11.get()), str(txt12.get()))]
        cur.executemany("""INSERT INTO ingfou (SOUS_SECTEUR,N_OPERATI,CHAPITRE_,LIBELLE_OP,AP_INITIAL,COMMUNE) VALUES(?,?,?,?,?,?)""",foufou)
        conn.commit()

    but = Button(fen, text='تم', command=tem)
    but.grid(row=0,column=0, sticky=E)
    conn.commit()
    #cur.close()
    #conn.close()
#------------------------------------------------------------------------------------------------------------------------------
def tabl_():
    mash_hide_ajou()
    mash_hide_connect()
    txta.delete(0.0,END)
    db_path = r'E:\Nom.accdb'
    mdp = 'jinbei'
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        f'DBQ={db_path};'
        f'PWD={mdp};'
    )
    try:
        conn = pyodbc.connect(conn_str)
        messagebox.showinfo(title=' شكرا على الانتظار ', message=' قد تم الإتصال')
        print('تم الإتصال')
    except pyodbc.Error as e:
        messagebox.showerror(title='خطأ', message=f'لم يتم الإتصال...تحقق من الملف\n\n{e}')
    style = ttk.Style()
    #theme
    style.theme_use('default')#'clam','default','alt','vista'

    tree_frame = Frame(fen)
    tree_frame.grid(row=0, column=0, padx=10, pady=10)
    tree_scroll = Scrollbar(tree_frame)
    tree_scroll.grid(row=0, column=1, sticky='ns')

    tv = ttk.Treeview(tree_frame,yscrollcommand=tree_scroll.set)
    tree_scroll.config(command=tv.yview)

    answer1 = simpledialog.askstring("بحث", "\t\t\t\t\t\t\t\t\t أدخل الأعمدة", initialvalue='SOUS_SECTEUR,N_OPERATI,CHAPITRE_,LIBELLE_OP,AP_INITIAL,COMMUNE,GEST_')
    #answer2 = simpledialog.askstring("بحث", "\t\t\t\t\t\t\t\t\t  أدخل الشروط" ,  initialvalue='CHAPITRE_ = AND GEST_ = ')# n'est pas egale s'ecrit '<>'
    """answer2 = simpledialog.askstring("بحث", "\t\t\t\t\t\t\t\t\t  أدخل الشروط" ,  initialvalue='CHAPITRE_ = AND GEST_ = ')# n'est pas egale s'ecrit '<>'    
    
    print("ddddddddddddddddddddd" + answer2)
    if answer2 == '' or answer2 == 'CHAPITRE_ = AND GEST_ = ':
        answer3 = 'ALL'
    else:
        answer3 = 'where ' + answer2    """

    fou = 'SELECT ' + answer1 + ' FROM ingfou '# + answer3
    print (fou)
    cur = conn.cursor()
    try:
        cur.execute(fou)
    except pyodbc.Error as e:
        messagebox.showerror(title='خطأ في الاستعلام', message=f'فشل تنفيذ الاستعلام. تحقق من أسماء الأعمدة والقيم.\n\n{e}')
        return
    records = cur.fetchall()
    selected = tv.focus()
    values = tv.item(selected,('values'))

    tv['columns']=('SOUS_SECTEUR','N_OPERATI','CHAPITRE_','LIBELLE_OP','AP_INITIAL','COMMUNE','GEST_')
    tv.column('#0', width=0,minwidth=25,stretch=NO )#
    tv.column('SOUS_SECTEUR', anchor=CENTER,minwidth=80, width=130)
    tv.column('N_OPERATI', anchor=CENTER,minwidth=80, width=100)
    tv.column('CHAPITRE_', anchor=CENTER,minwidth=80, width=100)
    tv.column('LIBELLE_OP', anchor=CENTER,minwidth=80, width=100)#
    tv.column('AP_INITIAL', anchor=CENTER,minwidth=80, width=130)
    tv.column('COMMUNE', anchor=CENTER,minwidth=80, width=100)
    tv.column('GEST_', anchor=CENTER,minwidth=80, width=100)

    tv.heading('#0', text='Label', anchor=CENTER)
    tv.heading('SOUS_SECTEUR', text='SOUS SECTEUR', anchor=CENTER)
    tv.heading('N_OPERATI', text='N_OPERATI', anchor=CENTER)
    tv.heading('CHAPITRE_', text='CHAPITRE', anchor=CENTER)
    tv.heading('LIBELLE_OP', text='LIBELLE_OP', anchor=CENTER)
    tv.heading('AP_INITIAL', text='AP_INITIAL', anchor=CENTER)
    tv.heading('COMMUNE', text='COMMUNE', anchor=CENTER)
    tv.heading('GEST_', text='GEST ', anchor=CENTER)
    def qury_datab ():
        global count
        count = 0
        # tags color lign
        tv.tag_configure('oddrow',background='white')
        tv.tag_configure('evenrow',background='lightblue')
        for record in records:
            if count % 2 == 0:
                v=[r for r in record]
                tv.insert(parent='', index='end', iid=count, text='', values=(v),tags=('evenrow'))
            else :
                v=[r for r in record]
                tv.insert(parent='', index='end', iid=count, text='', values=(v),tags=('oddrow'))
            count += 1

    tv.grid(row=0, column=0, sticky='nsew')
    tree_frame.grid_columnconfigure(0, weight=1)
    tree_frame.grid_rowconfigure(0, weight=1)
    print (len(tv.get_children()))
    #Labels
    string = ' '
    nums = ['SOUS_SECTEUR', 'N_OPERATI', 'CHAPITRE_', 'LIBELLE_OP', 'AP_INITIAL', 'COMMUNE', 'GEST_']
    labels=[] #creates an empty list for your labels
    lib = LabelFrame(fen, text='Record', font=("Times New Roman", 12, 'bold'))
    lib.grid(row=1, column=0, pady=20)

    #Labels
    nl = Label(lib,text = 'SOUS_SECTEUR')
    il = Label(lib,text = 'N_OPERATI')
    tl = Label(lib,text = 'CHAPITRE_')
    nl1 = Label(lib,text = 'LIBELLE_OP')
    il1 = Label(lib,text = 'AP_INITIAL')
    tl1 = Label(lib,text = 'COMMUNE')
    nl2 = Label(lib,text = 'GEST_')

    nl.grid(row=0,column=1)
    il.grid(row=0,column=2)
    tl.grid(row=0,column=3)
    nl1.grid(row=0,column=4)
    il1.grid(row=0,column=5)
    tl1.grid(row=0,column=6)
    nl2.grid(row=0,column=7)

    #Entry box
    nam_box =Entry (lib)
    id_box =Entry (lib)
    top_box =Entry (lib,width=10,justify='center')
    nam_box1 =Entry (lib,width=40)
    id_box1 =Entry (lib,width=10)#,jstify='center'
    top_box1 =Entry (lib)
    nam_box2 =Entry (lib)
    count1 =Entry (lib)

    nam_box.grid(row=1,column=1)
    id_box.grid(row=1,column=2)
    top_box.grid(row=1,column=3)
    nam_box1.grid(row=1,column=4)
    id_box1.grid(row=1,column=5)
    top_box1.grid(row=1,column=6)
    nam_box2.grid(row=1,column=7)
    count1.grid(row=2,column=4)
    # add_rec fonction
    def add_rec ():
        global count
        if count % 2 == 0:
            tv.insert(parent='', index='end', iid=count, text='', values=(id_box.get(),nam_box.get(),top_box.get()),tags=('evenrow'))
        else:
            tv.insert(parent='', index='end', iid=count, text='', values=(id_box.get(),nam_box.get(),top_box.get()),tags=('oddrow'))
        count +=1
        #clear the box after add
        nam_box.delete(0,END)
        id_box.delete(0,END)
        top_box.delete(0,END)
    def remove_all ():
        for record in tv.get_children():
            tv.delete(record)
    def remove_one ():
        x = tv.selection()[0]
        tv.delete(x)
    def remove_many ():
        x = tv.selection()
        for record in x:
            tv.delete(record)
    def select_record ():
        #clear the box after add
        nam_box.delete(0,END)
        id_box.delete(0,END)
        top_box.delete(0,END)
        nam_box1.delete(0,END)
        id_box1.delete(0,END)
        top_box1.delete(0,END)
        nam_box2.delete(0,END)
        selected = tv.focus()
        values = tv.item(selected,('values'))
        nam_box.insert(0,values[0])
        id_box.insert(0,values[1])
        top_box.insert(0,values[2])
        nam_box1.insert(0,values[3])
        id_box1.insert(0,values[4])
        top_box1.insert(0,values[5])
        nam_box2.insert(0,values[6])

    def clicker (e):
        select_record()
    def up ():
        rows = tv.selection()
        for row in rows :
            tv.move(row,tv.parent(row),tv.index(row)-1)
    def down ():
        rows = tv.selection()
        for row in reversed(rows)  :
            tv.move(row,tv.parent(row),tv.index(row)+1)
    def update_record ():
        selected = tv.focus()
        values = tv.item(selected,text='',values=(nam_box.get(),id_box.get(),top_box.get()))
        nam_box.delete(0,END)
        id_box.delete(0,END)
        top_box.delete(0,END)

    def on_get_count_clicked():
        """
        The 'Get count' button has been clicked.
        """
        total_count = get_count()
        print(total_count)
        count1.delete(0,END)
        count1.insert(0,total_count)
    def get_count(item_iid="") -> int:
        """
        Count and return the number of items and sub-items in the treeview widget.
        """
        count = 0
        
        # Enumerate over the given iid's sub-items.
        # If no item iid has been provided, it will enumerate over the parent items.
        for item in tv.get_children(item_iid):
            
            # Count the parent item that we're currently on.
            count += 1
            
            # Count all the sub-items of the current parent that we're on.
            count += get_count(item)
            
        return count
        
    #add button 
    lib1 = LabelFrame(fen, text='Button', font=("Times New Roman", 12, 'bold'))
    lib1.grid(row=2, column=0)
    move_down  = Button(lib1, text = 'Move Down', command = down )
    move_down.grid(row=0,column=0)
    move_up  = Button(lib1, text = 'Move Up', command = up )
    move_up.grid(row=0,column=1)
    # add_record
    add_reco = Button(lib1, text = 'add rec', command = add_rec )
    add_reco.grid(row=0,column=2)
    #update rec
    update_rec = Button(lib1, text = 'update rec', command = update_record )
    update_rec.grid(row=0,column=3)
    #remove all
    remov_all = Button(lib1, text = 'remove all rec', command = remove_all )
    remov_all.grid(row=0,column=4)
    #remove one selected
    remov_one = Button(lib1, text = 'remove one selected', command = remove_one )
    remov_one.grid(row=0,column=5)
    #remove many selection
    remov_many_s = Button(lib1, text = 'remove many selection', command = remove_many )
    remov_many_s.grid(row=0,column=6)
    #select record
    select_records = Button(lib1, text = 'select_record', command = select_record )
    select_records.grid(row=0,column=7)
    #count record
    select_records = Button(lib1, text = 'count record', command = on_get_count_clicked )
    select_records.grid(row=1,column=4)
    #bind
    tv.bind('<ButtonRelease-1>', clicker)
    qury_datab ()

#---------------------------------------------------------------------------------------------------------------------    
def connectt ():
    mash_hide_tabl_()
    mash_hide_ajou()
    
    answer = simpledialog.askstring("بحث", "أدخل رقم العملية\t\t", initialvalue='NK5.623.7.262.132.12.01')
    #answer.bind_class(fen,"<Button-3><ButtonRelease-3>", show_menu)

    cur.execute("SELECT * FROM ingfou Where N_OPERATI = ?", (answer,))
    rows = cur.fetchone()

    lib5.grid(row=1, sticky=W)
    txt5 = Text(lib5, font=("Times New Roman", 12), height=1, width=30)
    txt5.insert(END, rows.SECTEUR)

    lib4.grid(row=3, sticky=W)
    txt4 = Text(lib4, font=("Times New Roman", 12), height=1, width=30)
    txt4.insert(END, rows.LIBELLE_SOUS_SECTEUR)

    lib3.grid(row=5, sticky=W)
    txt3 = Text(lib3, font=("Times New Roman", 12), height=1, width=30)
    txt3.insert(END, rows.CHAPITRE_)

    liba.grid(row=5, column=2, sticky=W)
    txta = Text(liba, font=("Times New Roman", 12), height=1, width=30)
    chapitre_val = rows.CHAPITRE_
    txta.insert(END, (int(chapitre_val) if chapitre_val is not None else 0) + 100)

    lib2.grid(row=7, sticky=W)
    txt2 = Text(lib2, font=("Times New Roman", 12), height=1, width=30)
    txt2.insert(END, rows.COMMUNE)

    lib1.grid(row=9, columnspan=1 + 2, sticky=W)
    txt1 = scrolledtext.ScrolledText(lib1, font=("Times New Roman", 12), height=3, width=60, wrap = WORD)
    txt1.insert(1.0, rows.LIBELLE_OP)

    txt = Text(lib, font=("Times New Roman", 12), height=1, width=30)
    txt.insert(END, rows.LIBELLE_SOUS_SECTEUR)
    lib.grid(row=11, columnspan=2, sticky=W)

    def tem():
        txt5.grid(row=2,columnspan=2,sticky=W)
        txt4.grid(row=4,columnspan=2,sticky=W)
        txt3.grid(row=6,columnspan=2,sticky=W)
        txta.grid(row=6, columnspan=2, sticky=E)
        txt2.grid(row=8,columnspan=2,sticky=W)
        txt1.grid(row=10, sticky=W)
        #txt1.config(state=DISABLED)
        txt.grid(row=12,sticky=W)
    if answer:
        tem()
    labr = Label (fen,text='                           ',height=2)
    labr.grid(row=0, column=1, sticky=W)

def mash_hide_connect():
    lib5.grid_forget()
    lib4.grid_forget()
    lib3.grid_forget()
    liba.grid_forget()
    lib2.grid_forget()
    lib1.grid_forget()
    lib.grid_forget()
def mash_hide_tabl_():
    txta.grid_forget()
    labr = Label (fen,text='                                 ',height=2)
    labr.grid(row=0, column=1, sticky=W)
def mash_hide_ajou():
    lib6.grid_forget()
    lib7.grid_forget()
    lib8.grid_forget()
    #lib9.grid_forget()
    lib10.grid_forget()
    lib11.grid_forget()
    lib12.grid_forget()
    labrE = Label (fen,text='                       ',height=2)
    labrE.grid(row=0, column=0, sticky=E)
#   connectt().grid_forget()

menuBar = Menu(fen)
fen['menu'] = menuBar
sousMenu = Menu(menuBar,tearoff=0) # tearoff=0 menu ne peut ce detache
menuBar.add_cascade(label='Menu', menu=sousMenu)#,state=DISABLED
sousMenu.add_command(label='فتح ملف',command=connectt)
sousMenu.add_command(label='أضف قيم',command=ajou)
sousMenu.add_command(label='جدول',command=tabl_)
sousMenu.add_command(label='خروج',command=fen.destroy)

fen.mainloop()

"""from tkinter import *
fen= Tk()

frm= Label (fen, text='mlihmfdldf')
frm2= Label (fen, text='fofofofofofo')
def aktob2 ():
    hide()
    frm.pack()
def aktob ():
    hide()
    frm2.pack()

def hide():
    frm.pack_forget()
    frm2.pack_forget()

but = Button(fen , text= 'بوطونة', command = aktob).pack()
but1= Button(fen , text= 'بوطونة', command = aktob2).pack()

fen.mainloop()"""