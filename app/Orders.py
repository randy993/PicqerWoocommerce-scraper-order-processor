import Picqer
import WC
import mail
from Product import Product
from bs4 import BeautifulSoup as bs
import Gsheets
import requests
from requests import Session
from ConfigReader import Configuration
import re

config = Configuration.load_json('./app/config.json')

class Order:
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)

  def __init__(self, wcid, wcstatus=None, picqerid=None, tracking_url=None, tracking_number=None, deliveryname=None, deliveryaddress=None, deliveryzipcode=None, deliverycity=None, products=None):
    self.wcid = wcid
    self.wcstatus = wcstatus
    self.picqerid = picqerid
    self.tracking_url = tracking_url
    self.tracking_number = tracking_number
    self.deliveryname = deliveryname
    self.deliveryaddress = deliveryaddress
    self.deliveryzipcode = deliveryzipcode
    self.deliverycity = deliverycity
    self.products = products
    
def ProcessOrders():
    orderstoprocess = None
    orderstoprocess = OrdersToProcess()
    subject = None
    tekst = None

    with Session() as s:
        site = s.get(config.picqer.url)
        bs_content = bs(site.content, "html.parser")
        token = bs_content.find("input", {"name":"_token"})["value"]
        cookies = s.cookies
        login_data = {"emailaddress":config.picqer.username,"password":config.picqer.password, "_token":token}
        s.post(f"{config.picqer.url}/login?redirect=%2Fportal",login_data)
        

        for ordertoprocess in orderstoprocess:
            checkcart = s.get("https://quality-heating.picqer.com/portal/cart")
            soup = bs(checkcart.content, 'html.parser').find("p", class_="no-items-found")
            if soup:
                for product in ordertoprocess.products:
                    ### Voeg alle producten van de order toe aan de winkelwagen
                    addtocart = s.get(f"https://quality-heating.picqer.com/portal/cart/add?id={product.urlnummer}&amount={product.hoeveelheid}")
                    print(f"Aan winkelwagen toegevoegd {product.hoeveelheid} x {product.artikelnummer}")
                    
                ### Winkelwagen posten met inhoud
                url = 'https://quality-heating.picqer.com/portal/cart/placeorder'
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                data = f"""_token={token}&deliveryname={ordertoprocess.deliveryname}&deliverycontactname=&deliveryaddress={ordertoprocess.deliveryaddress}&deliveryaddress2=&deliveryzipcode={ordertoprocess.deliveryzipcode}&deliverycity={ordertoprocess.deliverycity}&deliveryregion=&deliverycountry=NL&invoicename=slimmeheater.nl&invoicecontactname=&invoiceaddress=St.+Antonielaan+109&invoiceaddress2=&invoicezipcode=6821GD&invoicecity=Arnhem&invoiceregion=&invoicecountry=NL&reference={ordertoprocess.wcid}&customer_remarks=Dropship&submit=submit"""
                print(data)
                
                ### Posten picqerID en statusupdate naar WC
                #PROD URL
                buy = requests.post(url, data = data, headers = headers, cookies = cookies)
                #TEST URL
                #buy = requests.post(url = "https://ptsv2.com/t/op6qd-1642144621/post", data = data, headers = headers)
                if buy.status_code == 200:
                    url = buy.url
                    ordertoprocess.picqerid = re.sub('[^0-9]','', url)
                    WC.UpdateOrderDetails(ordertoprocess)
                    subject = f"Order {ordertoprocess.wcid} processed"
                    tekst = f"{ordertoprocess}"
                    mail.SendMail(subject, tekst)
                else:
                    print('Fout bij het inschieten van order in Picqer')
                    print(buy.content)
                    subject = f"Fout bij het inschieten van order in Picqer!"
                    tekst = f"{buy.content}"
                    mail.SendMail(subject, tekst)

            else:
                addtocart = "Er zit wat in die winkelwaggie!"
                print(addtocart)
                subject = f"Er it wat in de winkelwaggel!"
                tekst = f"{addtocart}"
                mail.SendMail(subject, tekst)


def OrdersToProcess():
### Returns all orders to be processed including the products ordered
  WCorderstoprocess = WC.GetOrdersWithStatus('processing')
  print(f"{len(WCorderstoprocess)} order(s) met status processing")
  orderstoprocess = []

  gsheetsproduct = Gsheets.GetAllProducts()

  for x in WCorderstoprocess:
      order = Order(x['id'])
      order.wcstatus = x['status']
      order.deliveryname = f"{x['shipping']['first_name']}+{x['shipping']['last_name']}".replace(" ", "+")
      order.deliveryaddress = f"{x['shipping']['address_1']}+{x['shipping']['address_2']}".replace(" ", "+")
      order.deliveryzipcode = x['shipping']['postcode'].replace(" ", "+")
      order.deliverycity = x['shipping']['city'].replace(" ", "+")
      
      products = []
      items = x['line_items']
      for product in items:
        sku = product['sku']
        hoeveelheid = product['quantity']
        for number in gsheetsproduct:
          if product['sku'] == number[0]:
            picqerid = number[1]

        product = Product(artikelnummer = int(sku), hoeveelheid = hoeveelheid, urlnummer = int(picqerid))
        products.append(product) 
      order.products = products
      orderstoprocess.append(order)
  
  return orderstoprocess


### Shippingupdate functie
def ShippingUpdate():
  WCwfshippingorders = WC.GetOrdersWithStatus('wfshipping')
  print(f"{len(WCwfshippingorders)} order(s) met status wfshipping")
  wfshippingorders = []

  session = Picqer.OpenSession()

  for x in WCwfshippingorders:
      order = Order(x['id'])
      order.wcstatus = x['status']
      order.picqerid = WC.GetPicqerId(x)
      order.tracking_number, order.tracking_url = Picqer.GetTrackingInfo(session, order.picqerid)

      wfshippingorders.append(order)

  for p in wfshippingorders:
    if p.tracking_number and p.tracking_url:
      WC.UpdateShippingInfo(p)
      print(f"Shipping info geupdate voor: {p}")
    elif p.picqerid == None:
      print(f"Ontbrekend PicqerID: {p}")
      subject = f"PicqerID niet ingevuld!"
      tekst = f"PicqerID is niet gevonden voor order id: {p.wcid}"
      mail.SendMail(subject, tekst)
    else:
      print(f"Shipping info nog niet available voor {p}")


