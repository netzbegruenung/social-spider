import json
import os
from copy import copy
from pprint import pprint
from spider import dir_entries
import difflib
from osmxtract import overpass, location
import urllib

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

REMOVE_BW = ["08215", "08226", "08136", "08436"]

def createLVBasemap():
    green_data = []
    for entry in dir_entries():
        if entry["type"] == "REGIONAL_CHAPTER":
            if entry["level"] == "DE:LANDESVERBAND":
                green_data.append(entry)

    with open("maps/bundeslaender_simplify200.geojson", encoding='utf-8') as map_f:
        maps = json.load(map_f)
        result_map = copy(maps)
        result_map["features"] = []
        for feature in maps["features"]:
            name = feature["properties"]["GEN"]
            for d in green_data:
                if d["state"] == name:
                    feature["properties"] = {}
                    feature["properties"]["type"] = d["type"]
                    feature["properties"]["level"] = d["level"]
                    feature["properties"]["state"] = d["state"]
                    result_map["features"].append(feature)
    with open("maps/lv_basemap.geojson", "w", encoding='utf-8') as output_f:
        json.dump(result_map, output_f, indent=4)

def initialize():
    map_data = []
    green_data = []
    with open("maps/landkreise_simplify200.geojson") as map_f:
        map_data = json.load(map_f)["features"]

    # add additional bw data:
    map_data_copy = []
    for feature in map_data:
        if feature["properties"]["SN_L"] == "08" and feature["properties"]["RS"] in REMOVE_BW:
            pass # don't add it
        else:
            map_data_copy.append(feature)
    map_data = map_data_copy
    with open("maps/additional_bw.geojson") as map_f:
        map_data2 = json.load(map_f)["features"]
        for feature in map_data2:
            feature["properties"]["GEN"] = feature["properties"]["kvname"]
            feature["properties"]["NBD"] = ""
            feature["properties"]["BEZ"] = ""
            feature["properties"]["SN_L"] = "08"
        map_data += map_data2

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


def createKVBasemap():
    all_mapping_data = preprocess()
    result_features = []
    for countrycode in all_mapping_data.keys():
        for i, feature in enumerate(all_mapping_data[countrycode]["map_data_local"]):
            entry_idx = all_mapping_data[countrycode]["mapping"][i]
            if entry_idx != -1:
                entry = all_mapping_data[countrycode]["green_data_local"][entry_idx]
            else:
                # skip not-matched map parts
                continue
            feature["properties"] = {}
            feature["properties"]["type"] = entry["type"]
            feature["properties"]["level"] = entry["level"]
            feature["properties"]["state"] = entry["state"]
            feature["properties"]["district"] = entry["district"]
            result_features.append(feature)
    result_features += getHamburgMap()
    result_features += getBerlinMap()
    result_features += getBremenMap()
    result_map = {"type": "FeatureCollection",
                  "features": result_features}
    with open("maps/kv_basemap.geojson", "w") as output_f:
        json.dump(result_map, output_f, indent=4)


def getBerlinMap():
    lat, lon = location.geocode('Berlin, Germany')
    bounds = location.from_buffer(lat, lon, buffer_size=10000)
    print(bounds)
    # Build an overpass QL query and get the JSON response
    query = f'[out:json][timeout:25];(relation["type"="boundary"]["boundary"="administrative"]["admin_level"="9"]{bounds}; ); out geom qt;'
    response = overpass.request(query)
    ids = []
    names = []
    for elem in response["elements"]:
        print(elem["id"])
        ids.append(elem["id"])
        names.append(elem["tags"]["name"])

    mapdata = []
    for id_, name in zip(ids, names):
        if name == "Lindenberg":
            continue
        url = "http://polygons.openstreetmap.fr/get_geojson.py?id=" + str(id_) + "&params=0"
        urllib.request.urlretrieve(url, './tmp.geojson')
        print(name)
        with open('./tmp.geojson') as f:
            data = json.load(f)
            print(len(data["geometries"]))
            c = {"type": "Feature",
                "properties": {
                    "type": "REGIONAL_CHAPTER",
                    "level": "DE:KREISVERBAND",
                    "state": "Berlin",
                    "district": name
                },
                "geometry": data["geometries"][0]}
            mapdata.append(c)
    os.remove('./tmp.geojson')
    return mapdata


def getHamburgMap():
    lat, lon = location.geocode('Hamburg, Germany')
    bounds = location.from_buffer(lat, lon, buffer_size=10000)
    print(bounds)
    # Build an overpass QL query and get the JSON response
    query = f'[out:json][timeout:25];(relation["type"="boundary"]["boundary"="administrative"]["admin_level"="9"]{bounds}; ); out geom qt;'
    response = overpass.request(query)
    ids = []
    names = []
    for elem in response["elements"]:
        print(elem["id"])
        ids.append(elem["id"])
        names.append(elem["tags"]["name"])

    mapdata = []
    for id_, name in zip(ids, names):
        url = "http://polygons.openstreetmap.fr/get_geojson.py?id=" + str(id_) + "&params=0"
        urllib.request.urlretrieve(url, './tmp.geojson')
        print(name)
        if name.startswith("Hamburg-"):
            name = name.replace("Hamburg-", "")
        with open('./tmp.geojson') as f:
            data = json.load(f)
            print(len(data["geometries"]))
            c = {"type": "Feature",
                "properties": {
                    "type": "REGIONAL_CHAPTER",
                    "level": "DE:KREISVERBAND",
                    "state": "Hamburg",
                    "district": name
                },
                "geometry": data["geometries"][0]}
            mapdata.append(c)
    os.remove('./tmp.geojson')
    return mapdata

def getBremenMap():
    with open('./maps/additional_hb.geojson') as f:
        data = json.load(f)
        return data["features"]

if __name__ == "__main__":
    createKVBasemap()
    createLVBasemap()
