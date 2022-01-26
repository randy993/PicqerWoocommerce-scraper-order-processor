import Picqer
import WC
import mail
import Gsheets
import time, threading
from ConfigReader import Configuration

config = Configuration.load_json('./app/config.json')

producten = []

class Product:
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)

  def __init__(self, artikelnummer, urlnummer=None, hoeveelheid=None, prijs=None, voorraadQH=None, voorraadSH=None, wcid=None, wctype=None, parentid=None, stekker=None, huidigeprijs=None, prijszondermarge=None, wcname=None):
    self.artikelnummer = artikelnummer
    self.hoeveelheid = hoeveelheid
    self.urlnummer = urlnummer
    self.prijs = prijs
    self.wcid = wcid
    self.wctype = wctype
    self.voorraadQH = voorraadQH
    self.voorraadSH = voorraadSH
    self.parentid = parentid
    self.stekker = stekker
    self.huidigeprijs = huidigeprijs
    self.prijszondermarge = prijszondermarge
    self.wcname = wcname

### Product lijst maken 
def CreateProductenList():
    allproducts = Gsheets.GetAllProducts()
    for x in allproducts:
        product = Product(x[0])
        product.urlnummer = x[1]
        producten.append(product)
    return producten

### Check stekker
def CheckStekker(product):
    checkfor = "-"
    if checkfor in product.artikelnummer:
        product.stekker = True
    else:
        product.stekker = False
### Prijscheck
def CalculateZeroMarginPrice(product):
    product.prijszondermarge = product.prijs

    if product.stekker:
        product.prijs = product.prijs+config.stekkerprijs
        product.prijszondermarge = product.prijszondermarge+config.stekkerprijs

    product.prijszondermarge = product.prijszondermarge*1.21+13

### Stock vanuit Gsheets ophalen
def CheckSHStock(stocklist, product):
        if product.artikelnummer in stocklist:
            product.voorraadSH = True
        else:
            product.voorraadSH = False
        return product

def CheckAndUpdateStock():
    producten = CreateProductenList()
    SHstock = Gsheets.GetSHStockList()
    productennietopvoorraadstring = "Artikelnummer Artikel \n"
    productennietopvoorraadteller = 0
    productenzondermargestring = "Artikelnummer Artikel Onze prijs QH prijs \n"
    productenzondermargeteller = 0

    session = Picqer.OpenSession()
    ### Bewerkingen
    for product in producten:
        Picqer.GetPriceAndStock(session, product)
        WC.GetWCProductInfo(product)
        CheckSHStock(SHstock, product)
        WC.PostStockToWC(product)
        CheckStekker(product)
        CalculateZeroMarginPrice(product)
        print(f"{time.ctime()} {product}")

        ### Mail berekeningen
        if ((product.voorraadQH == False) and (product.voorraadSH == False)):
            productennietopvoorraadstring = productennietopvoorraadstring.__add__(f"{product.artikelnummer} {product.wcname} \n ")
            productennietopvoorraadteller +=1
        if product.huidigeprijs < product.prijszondermarge:
            productenzondermargestring = productenzondermargestring.__add__(f"{product.artikelnummer} {product.wcname} {product.prijs} {product.prijszondermarge} \n ")
            productenzondermargeteller +=1

    ### Stuur mail
    subject = f"Voorraad/prijs rapport {time.ctime()}"
    tekst = f"Niet op voorraad: {str(productennietopvoorraadteller)} \n Zonder marge: {str(productenzondermargeteller)} \n\nNiet op voorraad: \n{productennietopvoorraadstring} \nNegatieve marges: \n{productenzondermargestring}".replace(u"\u2013", "-")
    mail.SendMail(subject, tekst)

    ### Clear variables
    producten.clear()

    return "OK"

