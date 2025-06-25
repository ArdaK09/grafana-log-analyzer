import datetime
import json
import os
from collections import defaultdict
from typing import Optional

from flask import Response
import db_access


def searchByMethodName(methodname: str) -> dict:
    """
    Searches the database for subcalls made by the specified method.

    :param methodname: Name of the method to be searched for (case-insensitive).
    :return: A list of submethod call entries in the format [submethod_name, duration].

    See also:
        insertQueryTrack()
    """
    submethods = []
    name = ""
    details = None

    for doc in db_access.collection.find():
        if methodname.casefold() in doc.get('query').casefold():
            submethods.extend(doc.get('called_methods', []))
            name = doc['query']
            details = doc['details']

    result = {'name': name, 'details': details, 'called_methods': submethods}

    # Writing to file
    if len(submethods) != 0:
        detail = "SearchSubCalls_" + "_" + str(datetime.datetime.now().strftime("%x"))
        produce_output(detail, result)

    return result


def searchByMethodNameRepeating(methodname: str) -> dict:
    """
    :param methodname: Name of the method to be searched for (case-insensitive).
    :return: Dictionary: {"processed": number of documents}

    Searches the database for repeated subcalls made by the specified method. Provides the calls in
    descending number of calls alongside much useful information in out/ folder.
    Produces A JSON file consisting of the list of repeated submethod calls, including the duration and the
    repetition amount.

    See also for non-repeated submethod calls:
        searchByMethodName()
    """
    # Readability can be improved...

    # Extracting relevant info
    doc_found = 0
    for doc in db_access.collection.find():
        total_time = 0
        parent_details = None
        doc_result = {}
        # Find the matching doc
        if methodname.casefold() in doc["query"].casefold():
            # Extract fields form DB and store in relevant var.s
            parent_details = doc.get('details')
            parent_details.update({'name': doc['query']})
            data = doc.get('called_methods')  # List of stats
            parent_method_stats = defaultdict(lambda: [[], ""])
            # stats are stored in the database as follows:
            # {'name':name, 'time (ms)':time, 'url':_url_, 'db.statement': dbstatmnt}
            for stat in data:
                # parent_method_stats format: {'submethod_name1':[[times], db.statement], 'submethod_name2': ... }
                if 'url' in stat.keys():
                    # HTTP request, need to avoid combining different "GET"s etc.
                    parent_method_stats[stat['name'] + " " + stat['url']][0].append(stat['time (ms)'])
                else:
                    if 'db.statement' in stat.keys():
                        # DB request, need to set the second element
                        parent_method_stats[stat['name']][1] = stat['db.statement']

                    parent_method_stats[stat['name']][0].append(stat['time (ms)'])

            for submethod, values in parent_method_stats.items():
                entry = {
                    "call count": len(values[0]),
                    "total time (ms)": round(sum(values[0]), 3),
                    "average time (ms)": round(sum(values[0]) / len(values[0]), 3),
                    "min time (ms)": round(min(values[0]), 3),
                    "max time (ms)": round(max(values[0]), 3)
                }
                # Conditionally add 'db.statement'
                if values[1] != "":
                    # noinspection PyTypeChecker
                    entry["db.statement"] = values[1]
                total_time += sum(values[0])
                doc_result[submethod] = entry

        if len(doc_result) != 0:
            # Ensuring Sorted Response
            sorted_doc_result = dict(sorted(doc_result.items(), key=lambda item: item[1]['total time (ms)'], reverse=True))
            parent_details['total time (ms)'] = round(total_time, 3)
            result = [parent_details, sorted_doc_result]
            doc_found += 1

            # Writing to output file.
            details = "SearchRepeatingSubCalls_" + "_" + str(datetime.datetime.now().strftime("%x")) + "_" + str(doc_found)
            produce_output(details, result)


    return {'processed': doc_found}


def insertQueryTrace(filepath: str):
    """
    Inserts a query tracking document into the MongoDB database. Skips already existing files in the database.

    :param filepath: Path to the JSON file containing the query and submethod data.

    The function extracts the HTTP query from the first span in `batches[0]` and the
    submethods it calls from `batches[1]`. Each submethod is stored with its duration and other useful info.

    See also:
        insertQueryTrackFromPath()
    """
    with open(db_access.PATH + "/" + filepath, "r") as f:
        data = json.load(f)

    refQuery = data["batches"][0]["instrumentationLibrarySpans"][0]["spans"][0]
    name = refQuery["name"]
    traceId = refQuery["traceId"]
    urlPath, networkAddress, serverAddress, httpResponseCode = None, None, None, None

    for a in refQuery['attributes']:
        if a.get('key') == "url.path":
            urlPath = a
            continue
        elif a.get('key') == "network.peer.address":
            networkAddress = a
            continue
        elif a.get('key') == "server.address":
            serverAddress = a
            continue
        elif a.get('key') == "http.response.status_code":
            httpResponseCode = a
    details = {'traceId': traceId, 'attributes': [urlPath, networkAddress, serverAddress, httpResponseCode]}

    # Check the database if the document already exists
    for doc in db_access.collection.find():
        if (doc.get('query') == name) and (doc.get('details') == details):
            return {name: "Already in database", "details": details}

    span_list = []
    # Grabbing the related fields of batches[1] elements (submethods)
    for span in data["batches"][1]["instrumentationLibrarySpans"][0]["spans"]:
        cur_span_dic = {'name': span['name']}
        cur_span_dic.update({'time (ms)': (span["endTimeUnixNano"] - span["startTimeUnixNano"]) / 1000000})
        for atr in span["attributes"]:
            if atr.get('key') == "url.full":
                url = atr.get('value').get('stringValue')
                cur_span_dic.update({'url': url})
            if atr.get('key') == "db.statement":
                dbs = atr.get('value').get('stringValue')
                cur_span_dic.update({'db.statement': dbs})
        span_list.append(cur_span_dic)

    result = {"query": name, "details": details, "called_methods": span_list}
    insertResult = db_access.collection.insert_one(result)

    print("Inserted document ID:", insertResult.inserted_id)
    return {name: "Inserted to Database"}


def insertQueryTraceFromPath():
    """
    Calls insertQueryTrack() for every file in the configured PATH.

    Iterates through all files in the specified directory and inserts
    their contents as tracking documents.

    Note: insertQueryTrack does not insert duplicate files to the database.

    See also:
        insertQueryTrack()
    """

    insert_result = []
    for file in os.listdir(db_access.PATH):
        if not file.startswith('.'):  # skips hidden files on Unix/Mac
            print("File:", file)
            insert_result.append(insertQueryTrace(file))
            print("------------------------------------")

    return insert_result


def printQueryTrack(filepath: str):
    """
    :param filepath: Path to the JSON file containing the query and submethod data.

    The function extracts the HTTP query from the first span in `batches[0]` and the
    submethods it calls from `batches[1]`. Each submethod is stored with its duration.

    Unlike `insertQueryTrack`, it does not insert into the
    database specified in the configuration file. Used for testing puposes.

    See also:
        insertQueryTrack()
    """
    with open(db_access.PATH + "/" + filepath, "r") as f:
        data = json.load(f)

    refQuery = data["batches"][0]["instrumentationLibrarySpans"][0]["spans"][0]
    name = refQuery["name"]
    traceId = refQuery["traceId"]
    urlPath, networkAddress, serverAddress, httpResponseCode = None, None, None, None

    for a in refQuery['attributes']:
        if a.get('key') == "url.path":
            urlPath = a
            continue
        elif a.get('key') == "network.peer.address":
            networkAddress = a
            continue
        elif a.get('key') == "server.address":
            serverAddress = a
            continue
        elif a.get('key') == "http.response.status_code":
            httpResponseCode = a
    details = {'traceId': traceId, 'attributes': [urlPath, networkAddress, serverAddress, httpResponseCode]}

    span_list = []
    # Grabbing the related fields of batches[1] elements (submethods)
    for span in data["batches"][1]["instrumentationLibrarySpans"][0]["spans"]:
        cur_span_dic = {'name': span['name']}
        cur_span_dic.update({'time (ms)': (span["endTimeUnixNano"] - span["startTimeUnixNano"]) / 1000000})
        for atr in span["attributes"]:
            if atr.get('key') == "url.full":
                url = atr.get('value').get('stringValue')
                cur_span_dic.update({'url': url})
            if atr.get('key') == "db.statement":
                dbs = atr.get('value').get('stringValue')
                cur_span_dic.update({'db.statement': dbs})
        span_list.append(cur_span_dic)

    result = {"query": name, "details": details, "called_methods": span_list}

    print(json.dumps(result, indent=2))


def searchForParentMethods(methodname: str) -> list:
    """
    Finds all queries (parent methods) that invoked the specified submethod.

    :param methodname: The submethod name to search for (case-insensitive).
    :return: A list of parent method names that include the specified submethod.

    See also:
        searchByMethodName()
    """
    casefoldMethod = methodname.casefold()
    methods = []

    for doc in db_access.collection.find():
        for element in doc.get("called_methods", []):
            curQuery = doc.get("query")
            if element['name'].casefold() in casefoldMethod and (curQuery not in methods):
                methods.append(curQuery)

    if len(methods) != 0:
        details = "SearchParents_" + "_" + str(datetime.datetime.now().strftime("%x"))
        produce_output(details, methods)
    return methods


# Helper for output files
def produce_output(details: str, content):
    details = details.replace("/", "-")
    output_path = f"out/{details}.json"
    with open(output_path, 'w') as out:
        json.dump(content, out, indent=4)
