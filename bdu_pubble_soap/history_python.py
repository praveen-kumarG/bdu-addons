

from suds.client import Client
client = Client("file:///workspace/SalesWebService [13-9-2017].wsdl")

SalesOrder = client.factory.create('ns1:salesOrder')
transmissionID = 257018651
publisher = "testbdudata"
apiKey = "9tituo3t2qo4zk7emvlb"

SalesOrder.extOrderID = 5890148
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

ad1 = client.factory.create('ns1:adPlacement')

ad1.adSize.adTypeName = "Advertentiepagina"
ad1.adSize.extAdSizeID = 4005
ad1.adSize.height = 200
ad1.adSize.name = "KWARTADVVP"
ad1.adSize.width = 522
ad1.edition.editionDate = "2017-09-27T00:00:00"
ad1.edition.extPublicationID = "AWB"
ad1.extPlacementID = 14890147
ad1.price = 0
ad1.productionDetail.color = "true"
ad1.productionDetail.isClassified = "false"
ad1.productionDetail.dtpComments = "Commentaar voor opmaak"
ad1.productionDetail.placementComments = "Commentaar voor verkoop"
ad1.status = "active"

SalesOrder.orderLine_Ads.adPlacement.append(ad1)

response = client.service.processOrder(SalesOrder, transmissionID, publisher, apiKey)

from suds.plugin import MessagePlugin

client1 = Client("http://ws.pubble.nl/Sales.svc/?wsdl")
client1 = Client("http://pubble.nl/Webservice/ISales/processOrder?wsdl")
client1 = Client("http://pubble.nl/Webservice/ISales/processOrder/?wsdl")