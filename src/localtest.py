from time import sleep

from QueryTracking import *

insertQueryTrace("Trace-750bc4-2025-06-19 08_30_03.json")
insertQueryTrace("Trace-0780b3-2025-06-18 08_00_16.json")
# printQueryTrack("Trace-0780b3-2025-06-18 08_00_16.json")
searchByMethodNameRepeating("/marvel/mainOrder/{shoppingCartId}")
sleep(1)
searchByMethodNameRepeating("marvel/mainOrder/updateUpcCodeAndConditionChar")
# searchForParentMethods("getDefaultSiteEntityByUser")
# json.dumps(searchByMethodName("marvel"))
print("--------------------------------------------")
print("Cleanup")
print(db_access.collection.delete_many({}))
print("Remaining", db_access.collection.count_documents({}))
