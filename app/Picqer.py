from requests import Session
from bs4 import BeautifulSoup as bs
from ConfigReader import Configuration
import re

config = Configuration.load_json('./app/config.json')

### Sessie openen
def OpenSession():
    with Session() as s:
        site = s.get(config.picqer.url)
        bs_content = bs(site.content, "html.parser")
        token = bs_content.find("input", {"name":"_token"})["value"]
        login_data = {"emailaddress":config.picqer.username,"password":config.picqer.password, "_token":token}
        s.post(f"{config.picqer.url}/login?redirect=%2Fportal",login_data)
    return s

### Prijs en voorraad ophalen van Picqer
def GetPriceAndStock(s, product):

    home_page = s.get(f"{config.picqer.url}/products/{product.urlnummer}")
    soup = bs(home_page.content, 'html.parser')
    rows = soup.findAll('tr')
    
    resultdict = {}

    for row in rows:
        th = row.find_all('th')
        td = row.find_all('td')
        resultTh = th[0].get_text()
        resultTd = td[0].get_text()

        resultdict[resultTh]=resultTd

    prijs = resultdict["Prijs"].strip("€ ")
    prijs = float(prijs.replace(",","."))
   
    voorraad1 = resultdict["Voorraad Alkmaar pallet plaatsen"].strip()
    voorraad2 = resultdict["Voorraad Alkmaar magazijn b Stelling F"].strip()

    def VoorraadCheck(voorraad1, voorraad2):
        if ((voorraad1 == "Niet op voorraad") and (voorraad2 == "Niet op voorraad")):
            return False
        else:
            return True

    voorraad = VoorraadCheck(voorraad1, voorraad2)

    product.prijs = prijs
    product.voorraadQH = voorraad

    print(f"Picqer: Gegevens voor {product.artikelnummer} succesvol opgehaald")

    return product

### Tracking nummer ophalen
def GetTrackingInfo(s, oid):
    home_page = s.get(f"{config.picqer.url}/orders/{oid}")
    soup = bs(home_page.content, 'html.parser')
    tracking_number = None
    tracking_url = None

    if soup.find("td", class_="order-shipments-table-code"):
        shipment = soup.find("td", class_="order-shipments-table-code")
        tracking_number = shipment.get_text().split()[0]
        tracking_url = shipment.find('a', href = re.compile(r'[/]([a-z]|[A-Z])\w+')).attrs['href']
    return tracking_number, tracking_url

