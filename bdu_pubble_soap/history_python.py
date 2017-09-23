

from suds.client import Client
client = Client("file:///workspace/SalesWebService [13-9-2017].wsdl")

SalesOrder = client.factory.create('ns1:salesOrder')
transmissionID = 257018651 # hoe komen we aan dit ID?
publisher = "testbdudata" #Is dit altijd dezelfde?
apiKey = "9tituo3t2qo4zk7emvlb" # Endeze?

SalesOrder.extOrderID = 5890148 #Kan dit ook alfanumeriek zijn?
SalesOrder.reference = "Advertentie Kwart Voorpagina Alkmaars en Schager Weekblad"
SalesOrder.createdBy = "Barry"
SalesOrder.debtor.extAccountingID = 3406
SalesOrder.debtor.extDebtorID = 3406
SalesOrder.debtor.addedDate = "2017-09-14T18:06:51.8015518+02:00"
SalesOrder.debtor.city = "Baarn"
SalesOrder.debtor.emailadres = "info@inproba.nl"
SalesOrder.debtor.lastModified = "2017-09-04T18:06:51.8015518+02:00"
SalesOrder.debtor.name = "Inproba B.V."
SalesOrder.debtor.postalcode = "3741GP"
SalesOrder.agency = None
                    ##Hoe verhoudt de Adverteerder zich tot het Mediabureau? Als er een mediabureau is, wordt dit toch de debtor?
ad1 = client.factory.create('ns1:adPlacement')

ad1.adSize.adTypeName = "Advertentiepagina" #Dit zou de naam van de Advertising Class moeten zijn, klopt dat?
ad1.adSize.extAdSizeID = 4005 #Wat betekent dit?
ad1.adSize.height = 200 #in mm?
ad1.adSize.name = "KWARTADVVP" #?
ad1.adSize.width = 522 #?
ad1.edition.editionDate = "2017-09-27T00:00:00" # Odoo heeft dezelfde datumformaat, maar zonder de T tussen datum en tijd.
ad1.edition.extPublicationID = "AWB"
ad1.extPlacementID = 14890147 #Wat is dit?
ad1.price = 0
ad1.productionDetail.color = "true" #?
ad1.productionDetail.isClassified = "false" #?
ad1.productionDetail.dtpComments = "Commentaar voor opmaak"
ad1.productionDetail.placementComments = "Commentaar voor verkoop"
ad1.status = "active"

SalesOrder.orderLine_Ads.adPlacement.append(ad1)

response = client.service.processOrder(SalesOrder, transmissionID, publisher, apiKey)

from suds.plugin import MessagePlugin

client1 = Client("http://ws.pubble.nl/Sales.svc/?wsdl")
client1 = Client("http://pubble.nl/Webservice/ISales/processOrder?wsdl")
client1 = Client("http://pubble.nl/Webservice/ISales/processOrder/?wsdl")