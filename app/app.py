import Product
import Orders
import time, threading
from ConfigReader import Configuration

config = Configuration.load_json('./app/config.json')


def runStockCheck():
    threading.Timer(config.intervalsecondsStock, runStockCheck).start()
    Product.CheckAndUpdateStock()

def runProcessOrders():
    threading.Timer(config.intervalsecondsOrders, runProcessOrders).start()

    Orders.ShippingUpdate()

    time.sleep(300)

    Orders.ProcessOrders()


runStockCheck()
runProcessOrders()












    






