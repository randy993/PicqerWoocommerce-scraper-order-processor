from oauth2client.service_account import ServiceAccountCredentials
import gspread
from ConfigReader import Configuration

config = Configuration.load_json('./app/config.json')

scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('./app/gsheets-api.json', scope)
client = gspread.authorize(creds)

def GetAllProducts():
    products = client.open(config.gsheets.filename).worksheet(config.gsheets.PicqerTab).get_all_values()
    print("Producten opgehaald")
    return products

def GetSHStockList():
    products = client.open(config.gsheets.filename).worksheet(config.gsheets.StockTab).col_values(config.gsheets.Voorraadkolom)
    return products

    



