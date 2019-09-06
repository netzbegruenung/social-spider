import json
from copy import copy
from pprint import pprint
from spider import dir_entries
import difflib

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

MAPPING = {"Neustadt a.d. Aisch-Bad Windsheim": "Neustadt-Aisch",
           "Märkischer Kreis": "Mark",
           "Osterode am Harz": "Göttingen",
           "Göttingen": "Göttingen",
           "Straubing": "Straubing-Bogen",
           "Straubing-Bogen": "Straubing-Bogen",
           "Kaufbeuren": "Ostallgäu",
           "Ostallgäu": "Ostallgäu"}

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
            if entry["level"] == "DE:REGIONALVERBAND":
                entry["district"] = entry["region"]
                green_data.append(entry)

    print(len(map_data))
    print(len(green_data))
    return map_data, green_data

def generateMapping(map_data_local, green_data_local):
    # print("-----------------------------")
    # for d in green_data_local:
    #     print(d["district"])
    # print("----")
    # for d in map_data_local:
    #     name = d["properties"]["GEN"]
    #     if d["properties"]["NBD"] == "ja":
    #         fullname = d["properties"]["BEZ"] +" " + d["properties"]["GEN"]
    #     else:
    #         fullname = d["properties"]["GEN"]
    #     print(fullname)
    # print("-----------------------------")

    mapping = [-1] * len(map_data_local)
    mapCount = [0] * len(green_data_local)

    # ------------------------------------------
    # match predefined
    # ------------------------------------------

    for i, d in enumerate(map_data_local):
        name = d["properties"]["GEN"]
        if MAPPING.get(name):
            mapName = MAPPING[name]
            for j, entry in enumerate(green_data_local):
                if mapName == entry["district"]:
                    mapping[i] = j
                    mapCount[j] += 1

    # ------------------------------------------
    # match full name
    # ------------------------------------------

    mapCount_copy = copy(mapCount)
    for i, d in enumerate(map_data_local):
        if d["properties"]["NBD"] == "ja":
            fullname = d["properties"]["BEZ"] +" " + d["properties"]["GEN"]
        else:
            fullname = d["properties"]["GEN"]
        for j, entry in enumerate(green_data_local):
            if mapCount_copy[j] == 0:
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

    mapCount_copy = copy(mapCount)
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

    # ------------------------------------------
    # match with string similarity
    # ------------------------------------------

    mapCount_copy = copy(mapCount)
    for i, d in enumerate(map_data_local):
        if mapping[i] == -1:
            name = d["properties"]["GEN"]
            for j, entry in enumerate(green_data_local):
                if mapCount_copy[j] == 0:
                    similarity = difflib.SequenceMatcher(a=entry["district"].lower(), b=name.lower()).ratio()
                    if similarity > 0.6:
                        mapping[i] = j
                        mapCount[j] += 1

    remaining = len([e for e in mapping if e == -1])
    print("Remaining:", remaining)
    if remaining == 0:
        return mapping

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

            print(fullname, "--", d["properties"]["GEN"], "--")

    return mapping

def preprocess():
    map_data, green_data = initialize()

    all_mapping_data = {}
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
        mapping = generateMapping(map_data_local, green_data_local)
        all_mapping_data[countrycode] = {"map_data_local": map_data_local,
                                         "green_data_local": green_data_local,
                                         "mapping": mapping}

    return all_mapping_data


def createMap(all_mapping_data):
    result_features = []
    for countrycode in all_mapping_data.keys():
        for i, feature in enumerate(all_mapping_data[countrycode]["map_data_local"]):
            entry_idx = all_mapping_data[countrycode]["mapping"][i]
            if entry_idx != -1:
                entry = all_mapping_data[countrycode]["green_data_local"][entry_idx]
                feature["properties"]["fill"] = "#00ff00"
            else:
                feature["properties"]["fill"] = "#ff0000"
            feature["properties"]["fill-opacity"] = 1
            feature["properties"].update(entry)
            result_features.append(feature)
    result_map = {"type": "FeatureCollection",
                  "features": result_features}
    with open("maps/test.geojson", "w") as output_f:
        json.dump(result_map, output_f)

if __name__ == "__main__":
    all_mapping_data = preprocess()
    createMap(all_mapping_data)
