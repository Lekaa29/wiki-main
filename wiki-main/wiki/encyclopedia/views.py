from django.shortcuts import render,redirect
from django import forms
import random
from markdown2 import Markdown

from . import scrapeFOUND

markdowner = Markdown()

def index(request):
    scrapeFOUND.scrape()
    return render(request, "encyclopedia/index.html")

