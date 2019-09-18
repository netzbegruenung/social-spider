import json
import math

def updateMaps(level="lv"):
    data = {}
    map_data = {}
    with open("docs/result.json") as f:
        data = json.load(f)
    with open("maps/" + level + "_basemap.geojson") as f:
        map_data = json.load(f)
    fb_max = 0
    tw_max = 0
    in_max = 0
    for feature in map_data["features"]:
        p = feature["properties"]
        key = "//".join([p["type"], p["level"], p["state"], p.get("district", ""), p.get("city", "")])
        result = data.get(key)

        social_data = {}
        if result:
            _, _, _ , _, _, fb_name, fb_count, tw_name, tw_count, in_name, in_count = result
            if fb_count > fb_max:
                fb_max = fb_count
            if tw_count > tw_max:
                tw_max = tw_count
            if in_count > in_max:
                in_max = in_count
            social_data["fb_name"] = fb_name
            social_data["fb_count"] = fb_count
            social_data["tw_name"] = tw_name
            social_data["tw_count"] = tw_count
            social_data["in_name"] = in_name
            social_data["in_count"] = in_count
        feature["properties"].update(social_data)

    print(fb_max, tw_max, in_max)
    for plattform, maxval, col in zip(["fb", "tw", "in"], [fb_max, tw_max, in_max], ["#3664a2", "#55acee", "#d02e92"]):
        for feature in map_data["features"]:
            count = feature["properties"].get(plattform + "_count", 0)
            if level == "lv":
                # linear for LV
                feature["properties"]["fill-opacity"] = count/maxval
            elif level == "kv":
                # logarithmic for KV
                feature["properties"]["fill-opacity"] = getLogValue(count, maxval)
            feature["properties"]["fill"] = col
            feature["properties"]["stroke-width"] = 0
        with open("maps/" + level + "_" + plattform + ".geojson", "w") as f:
            json.dump(map_data, f, indent=4)

def getLogValue(count, maxval):
    multiplier = 0.1
    if count * multiplier < 1:
        return 0
    return math.log(count*multiplier) / math.log(maxval*multiplier)

if __name__ == "__main__":
    updateMaps(level="kv")
    updateMaps(level="lv")