import json


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


if __name__ == '__main__':
    createBundeslaenderMap("facebookLikes", 5)
    createBundeslaenderMap("twitterFollower", 7)
    createBundeslaenderMap("instaFollower", 9)
