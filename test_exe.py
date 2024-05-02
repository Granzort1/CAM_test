from distutils.core import setup
import py2exe

setup (windows = ['viewResultsOnMapWindow_v3.pyw'],
       options = { 'py2exe' : {'packages':['Tkinter']}})