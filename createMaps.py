import json
from copy import copy
from pprint import pprint
from spider import dir_entries

COUNTRY_MAP =  {"01": "Schleswig-Holstein",
                "02": "Hamburg",
                "03": "Niedersachsen",
                "04": "Bremen",
                "05": "Nordrhein-Westfalen",
                "06": "Hessen",
                "07": "Rheinland-Pfalz",
                "08": "Baden-Württemberg",
                "09": "Bayern",
                "10": "Saarland",
                "11": "Berlin",
                "12": "Brandenburg",
                "13": "Mecklenburg-Vorpommern",
                "14": "Sachsen",
                "15": "Sachsen-Anhalt",
                "16": "Thüringen"}


def createBundeslaenderMap(filename, column):
    with open("maps/bundeslaender_simplify200.geojson") as map_f:
        maps = json.load(map_f)
        with open("docs/result.json") as result_f:
            result = json.load(result_f)
            minimum = 1000000
            maximum = -1
            for _, elem in result.items():
                if elem[0] != "LV":
                    continue
                if elem[column] < minimum:
                    minimum = elem[column]
                if elem[column] > maximum:
                    maximum = elem[column]
            print(maximum)
            for feature in maps["features"]:
                name = feature["properties"]["GEN"]
                for _, elem in result.items():
                    if elem[0] != "LV":
                        continue
                    if elem[1] != name:
                        continue
                    feature["properties"]["fill-opacity"] = elem[column] / maximum
                    feature["properties"]["fill"] = "#00ff00"
    with open("maps/bundeslaender_" + filename + ".geojson", "w") as output_f:
        json.dump(maps, output_f)

def initialize():
    map_data = []
    green_data = []
    with open("maps/landkreise_simplify200.geojson") as map_f:
        map_data = json.load(map_f)["features"]

    for entry in dir_entries():
        if entry["type"] == "REGIONAL_CHAPTER":
            if entry["level"] == "DE:KREISVERBAND":
                green_data.append(entry)

    print(len(map_data))
    print(len(green_data))
    return map_data, green_data


def getEntryFromFeature(feature, map_data, green_data):
    countrycode = feature["properties"]["SN_L"]
    countryname = COUNTRY_MAP[countrycode]
    print(countryname)
    green_data_local = []
    for d in green_data:
        if d["state"] == countryname:
            green_data_local.append(d)
    map_data_local = []
    for d in map_data:
        if d["properties"]["SN_L"] == countrycode:
            map_data_local.append(d)
    print()
    generateMapping(map_data_local, green_data_local)


def generateMapping(map_data_local, green_data_local):
    print("-----------------------------")
    for d in green_data_local:
        print(d["district"])
    print("----")
    for d in map_data_local:
        name = d["properties"]["GEN"]
        if d["properties"]["NBD"] == "ja":
            fullname = d["properties"]["BEZ"] +" " + d["properties"]["GEN"]
        else:
            fullname = d["properties"]["GEN"]
        print(fullname)
    print("-----------------------------")

    mapping = [-1] * len(map_data_local)
    mapCount = [0] * len(green_data_local)

    # ------------------------------------------
    # match full name
    # ------------------------------------------

    for i, d in enumerate(map_data_local):
        if d["properties"]["NBD"] == "ja":
            fullname = d["properties"]["BEZ"] +" " + d["properties"]["GEN"]
        else:
            fullname = d["properties"]["GEN"]
        for j, entry in enumerate(green_data_local):
            if fullname == entry["district"]:
                mapping[i] = j
                mapCount[j] += 1

    # ------------------------------------------
    # match -Land and -Stadt entries
    # ------------------------------------------

    mapCount_copy = copy(mapCount)
    for i, d in enumerate(map_data_local):
        if mapping[i] == -1:
            name = d["properties"]["GEN"]
            for j, entry in enumerate(green_data_local):
                if mapCount_copy[j] == 0:
                    district_name = entry["district"]
                    if district_name.endswith("-Stadt") and "stadt" in d["properties"]["BEZ"].lower():
                        if name == district_name[:-6]:
                            mapping[i] = j
                            mapCount[j] += 1
                    if district_name.endswith("-Land") and "land" in d["properties"]["BEZ"].lower():
                        if name == district_name[:-5]:
                            mapping[i] = j
                            mapCount[j] += 1

    # ------------------------------------------
    # match short name
    # ------------------------------------------

    for i, d in enumerate(map_data_local):
        if mapping[i] == -1:
            name = d["properties"]["GEN"]
            for j, entry in enumerate(green_data_local):
                if mapCount_copy[j] == 0:
                    if name == entry["district"]:
                        mapping[i] = j
                        mapCount[j] += 1

    # ------------------------------------------
    # match entries ending with "kreis"
    # ------------------------------------------

    mapCount_copy = copy(mapCount)
    for i, d in enumerate(map_data_local):
        if mapping[i] == -1:
            name = d["properties"]["GEN"]
            if name.endswith("-Kreis"):
                name = name[:-6]
            if name.lower().endswith("kreis"):
                name = name[:-5]
            for j, entry in enumerate(green_data_local):
                if mapCount_copy[j] == 0:
                    if name == entry["district"]:
                        mapping[i] = j
                        mapCount[j] += 1

    # ------------------------------------------
    # match containing substrings
    # ------------------------------------------

    mapCount_copy = copy(mapCount)
    for i, d in enumerate(map_data_local):
        if mapping[i] == -1:
            name = d["properties"]["GEN"]
            for j, entry in enumerate(green_data_local):
                if mapCount_copy[j] == 0:
                    name2 = entry["district"]
                    if name in name2 or name2 in name:
                        mapping[i] = j
                        mapCount[j] += 1

    print("------------------------")

    remaining = len([e for e in mapping if e == -1])
    print("Remaining:", remaining)
    if remaining == 0:
        return 0

    for j, entry in enumerate(green_data_local):
        if mapCount[j] == 0:
            print(entry["district"])
    print("---")
    for i, d in enumerate(map_data_local):
        if mapping[i] == -1:
            if d["properties"]["NBD"] == "ja":
                fullname = d["properties"]["BEZ"] +" " + d["properties"]["GEN"]
            else:
                fullname = d["properties"]["GEN"]
            print(fullname, "--", d["properties"]["GEN"])


    return remaining


if __name__ == '__main__':
    #createBundeslaenderMap("facebookLikes", 5)
    #createBundeslaenderMap("twitterFollower", 7)
    #createBundeslaenderMap("instaFollower", 9)
    map_data, green_data = initialize()
    #print(getEntryFromFeature(map_data[0], map_data, green_data))
    #print(getEntryFromFeature(map_data[1], map_data, green_data))
    remaining = 0
    for countrycode in COUNTRY_MAP.keys():
        countryname = COUNTRY_MAP[countrycode]
        if countryname in ["Berlin", "Bremen", "Hamburg"]:
            continue
        green_data_local = []
        for d in green_data:
            if d["state"] == countryname:
                green_data_local.append(d)
        map_data_local = []
        for d in map_data:
            if d["properties"]["SN_L"] == countrycode:
                map_data_local.append(d)
        print("===================================")
        print(countryname)
        print("===================================")
        remaining += generateMapping(map_data_local, green_data_local)
    print("REMAINING:", remaining)
