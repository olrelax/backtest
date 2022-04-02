#!/usr/bin/python
# -*- coding: utf-8 -*-
from tkinter import *
import os
import sys
import tkinter.filedialog as fd

def die(event):
    sys.exit(0)

root = Tk()
w = root.winfo_screenwidth()//2 - 400
h = root.winfo_screenheight()//2 - 300
root.geometry("800x600+{}+{}".format(w, h))
root.title("Подписать документ")

flName = fd.askopenfilename(title="Что подписываем?")

if flName:
    os.system("gpg -ba " + flName)
    button = Button(text="ЭЦП создана")
    button.bind("<Button-1>", die)
    button.pack(expand=YES, anchor=CENTER)
else:
    die(1)

root.mainloop()
