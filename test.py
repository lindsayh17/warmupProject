import firebase as f

if __name__ == "__main__":
    print("Start!")
    print(f.getInfo("Population", "Japan"))
    print(f.getDetailedInfo("Area", "Peru"))
    print(f.getCompare("Population", ">", 1000000000))
    print(f.getDetailedCompare("Coastline", ">=", 20))