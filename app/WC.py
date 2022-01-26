from woocommerce import API
from ConfigReader import Configuration
import re

config = Configuration.load_json('./app/config.json')


class Product:
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)


### WC api
wcapi = API(
    url=config.woocommerce.url,
    consumer_key=config.woocommerce.c_key,
    consumer_secret=config.woocommerce.c_secret,
    version="wc/v3"
)

### WC functies
def PostStockToWC(product):
    if ((product.voorraadQH == False) and (product.voorraadSH == False)):
        stockstatus = "outofstock"
    else:
        stockstatus = "instock"

    data = {
    "stock_status": stockstatus
    }

    if (product.wctype == "simple"):
        wcapi.put(f"products/{product.wcid}", data).json()
    elif (product.wctype == "variation"):
        wcapi.put(f"products/{product.parentid}/variations/{product.wcid}", data).json()

def GetWCProductInfo(product):
    jsonresponse = wcapi.get(f"products?sku={product.artikelnummer}").json()
    product.wcid = jsonresponse[0]["id"]
    product.wctype = jsonresponse[0]["type"]
    product.parentid = jsonresponse[0]["parent_id"]
    product.huidigeprijs = float(jsonresponse[0]["regular_price"])
    product.wcname = jsonresponse[0]["name"]
    print(f"WC: Gegevens voor {product.artikelnummer} succesvol opgehaald")
    return product

### Returnt alleen picqer_id
def GetPicqerId(order):
#    jsonresponse = wcapi.get(f"orders/{order}").json()

    metadata = order["meta_data"]
    for a in metadata:
        if a['key'] == 'picqer_id':
            return a['value']
    
def GetOrdersWithStatus(status):
    jsonresponse = wcapi.get(f"orders?status={status}&per_page=100").json()
    return jsonresponse

def UpdateShippingInfo(order):
    data = {
"status": "completed",
"meta_data": [
  {
    "key": "tracking_url",
    "value": order.tracking_url
  },
  {
    "key": "tracking_number",
    "value": order.tracking_number  	
  }
]
}

    wcapi.put(f"orders/{order.wcid}", data).json()

def UpdateOrderDetails(order):
    data = {
"status": "wfshipping",
"meta_data": [
  {
    "key": "picqer_id",
    "value": order.picqerid
  }
]
}
    wcapi.put(f"orders/{order.wcid}", data).json()




