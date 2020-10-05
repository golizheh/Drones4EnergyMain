## Dataset:
  https://overpass-turbo.eu/

    (area[name="Danmark"];)->.a;(way(area.a)["power"="line"];node(w););out;way["power"="line"]({{bbox}});>;out;

## Requirements:
  OR-Tools  https://developers.google.com/optimization/install/python/windows

    pip install ortools

      only works with 64 bit python, guaranteed with python 3.7.x  64 bit

  networkx

    pip install networkx

  pyproj

    pip install pyproj

## Using program:
  Run astar.py
  The function solver(droneAmountToUse, towers, drones) takes the amount of drones to be used, a list of towers and a list of available drones. Output can be exported to output.txt and can be visualized at https://www.gpsvisualizer.com/map_input?form=data

## Example:
Place in main:

    d0 = pylon(2278912432, latlon=(55.2358393, 10.4952056), neighbours=())
    d1 = pylon(831393245, latlon=(55.3212158, 10.6231185), neighbours=())
    d2 = pylon(831803315, latlon=(55.3316506, 10.2775602), neighbours=())
    d3 = pylon(1855024080, latlon=(55.5170376, 10.0643745), neighbours=())
    d4 = pylon(2374155687, latlon=(55.2774965, 9.941915), neighbours=())
    d5 = pylon(2251290513, latlon=(55.1129137, 10.1833763), neighbours=())
    d6 = pylon(2251253841, latlon=(55.0646142, 10.4405162), neighbours=())
    d7 = pylon(2276136436, latlon=(55.5001219, 10.6421767), neighbours=())
    d8 = pylon(2374285438, latlon=(55.4886889, 9.7882277), neighbours=())
    d9 = pylon(1854971946, latlon=(55.5406875, 10.2649967), neighbours=())
    
    droneAmount = 1
    tower_list = [d1, d2, d3, d4, d5, d6, d7, d8, d9]
    drone_list = [d0]
    value = solver(droneAmount, tower_list, drone_list)
    writeToFile(visualizer(value))
