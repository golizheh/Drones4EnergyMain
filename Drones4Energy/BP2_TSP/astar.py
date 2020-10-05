from __future__ import print_function
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import networkx as nx
import pickle
import pyproj
from math import ceil

#takes latitude and longitude from pylons and calls distance function
def dist(t1,t2):
    return distance(t1.latlon,t2.latlon)

geod = pyproj.Geod(ellps="WGS84")
def distance(x,y):
    return geod.line_length((x[1],y[1]),(x[0],y[0]))

class pylon:
    def __init__(self,id,latlon,neighbours=()):
        self.id = id
        self.latlon = latlon
        self.neighbours = neighbours
    def __repr__(self):
        return "pylon(id="+repr(self.id)+",latlon="+repr(self.latlon)+", neighbours="+repr(self.neighbours)+")"
    def __lt__(self,other):
        return self.latlon < other.latlon
    def __eq__(self,other):
        return self.latlon == other.latlon
    def __hash__(self):
        return hash(self.latlon)

#graph file either loaded from limic or astar itself
try:
    globalGraph = pickle.load(open("../BP2_TSP/out.graph","rb"))
except OSError as e:
    try:
        globalGraph = pickle.load(open("out.graph","rb"))
    except OSError as e:
        globalGraph = -1

#finds shortest path between two towers
def route(startPoint, endPoint):
    try:
        path = nx.astar_path(globalGraph, startPoint, endPoint, heuristic=dist)
    except (nx.NetworkXNoPath, nx.exception.NodeNotFound) as e:
        return -1
    return path

#calculates length of route
def routeLength(route):
    length = 0
    for i in range(len(route)-1):
        length += dist(route[i], route[i+1])
    return length

#Creates distance matrix and route matrix
def create_distance_route_matrix(droneAmount, node_list):
    matrix_size = len(node_list)
    distanceMatrix = []
    routeMatrix = []

    #Create empty matrices
    for i in range(matrix_size+1):
        routeRow = []
        distanceRow = []
        for u in range(matrix_size+1):
            routeRow.append([])
            distanceRow.append(0)
        routeMatrix.append(routeRow)
        distanceMatrix.append(distanceRow)

    for i in range(matrix_size):
        for u in range(i, matrix_size):
            path = route(node_list[i], node_list[u])
            if path == -1:
                return []
            routeMatrix[i][u] = path
            routeMatrix[u][i] = path[::-1]
            dist = (int(routeLength(path) * 10**8))
            distanceMatrix[i][u] = dist
            distanceMatrix[u][i] = dist

    #print(concordeDistanceMatrix(distanceMatrix))
    data = {}
    data['distance_matrix'] = distanceMatrix
    data['num_vehicles'] = droneAmount
    data['starts'] = list(range(droneAmount))
    data['ends'] = [matrix_size] * droneAmount
    data['routeMatrix'] = routeMatrix
    return data

#Modifies existing distance and route matrix for improved performance
def modify_distance_route_matrix(data, node_list):
    node1 = node_list[0]
    distanceRow = []
    routeRow = []
    for node2 in node_list:
        path = route(node1, node2)
        if path == -1:
            return []
        routeRow.append(path)
        distanceRow.append(int(routeLength(path) * 10**8))
    distanceRow.append(0)   #connection to dummyRow

    node2 = node_list[0]
    for x in range(len(node_list)):
        path = route(node_list[x], node2)
        if path == -1:
            return []
        data['distance_matrix'][x][0] = int(routeLength(path) * 10**8)
        data['routeMatrix'][x][0] = path

    data['distance_matrix'][0] = distanceRow
    data['routeMatrix'][0] = routeRow
    return data

def concordeDistanceMatrix(distanceMatrix):
    diststr = ""
    for i in range(len(distanceMatrix)-1):
        row1 = ""
        row2 = ""
        for u in range(len(distanceMatrix[i])-1):
            if i == u:
                row1 = row1 + "0 -9999 "
                row2 = row2 + "-9999 0 "
            elif u == 0:
                if i == 0:
                    row1 = row1 + "9999 " + str(0) + " "
                else:
                    row1 = row1 + "9999 " + str(distanceMatrix[u][i]) + " "
                row2 = row2 + str(0) + " 9999 "
            else:
                if i == 0:
                    row1 = row1 + "9999 " + str(0) + " "
                else:
                    row1 = row1 + "9999 " + str(distanceMatrix[u][i]) + " "
                row2 = row2 + str(distanceMatrix[i][u]) + " 9999 "
        row1 = row1 + "\n"
        row2 = row2 + "\n"
        diststr = diststr + row1 + row2
    return diststr


#prints solution and returns routes for all drones
def print_solution(data, manager, routing, assignment):
    total_route_distance = 0
    droneRoutes = []
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for drone {}:\n'.format(vehicle_id)
        droneRoute = []
        route_distance = 0
        while not routing.IsEnd(index):
            plan_output += ' {} -> '.format(manager.IndexToNode(index))
            droneRoute.append(manager.IndexToNode(index))
            previous_index = index
            index = assignment.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        #route_distance = route_distance / 10 ** 8
        plan_output += '{}\n'.format(manager.IndexToNode(index))
        plan_output += 'Distance of the route: {}\n'.format(route_distance)
        print(plan_output)
        total_route_distance += route_distance
        droneRoutes.append(droneRoute)
    #print('Total route distances: {}\n'.format(total_route_distance))
    print(total_route_distance)
    return total_route_distance, droneRoutes

#converts list of coordinates to formatted lines with latitude and longitude
def visualizer(routesCoordinates):
    latlonString = "latitude,longitude\n"
    for routeCoordinates in routesCoordinates:
        for routeCoordinate in routeCoordinates:
            for u in routeCoordinate:
                latlonString += (str(u) + ', ')
            latlonString += "\n"
        latlonString += "new drone\n"
    return latlonString

def writeToFile(text):
    f = open("output.txt","w+")
    f.write(text)
    f.close()

def localSearch(numberOfTowers):
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.seconds = ceil(0.65 * 2.72 ** (0.064 * numberOfTowers))
    #search_parameters.solution_limit = 10
    #search_parameters.lns_time_limit.seconds = 5
    search_parameters.log_search = False
    return search_parameters

def firstSolution():
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC)
    return search_parameters

def fromNodestoPylons(node_list):
    if isinstance(node_list[0], pylon): #check if conversion to pylon is required
        return node_list

    newNode_list = []
    for node in node_list:  #transform all nodes in list to pylons
        newNode_list.append(pylon(int(node[0]), latlon=(round(float(node[2]), 7), round(float(node[1]), 7)), neighbours=()))
    return newNode_list

def fromDronetoPylon(drone):
    if isinstance(drone, pylon): #check if conversion to pylon is required
        return drone
    else:
        return pylon(int(drone[1]), latlon=(round(float(drone[3]), 7), round(float(drone[2]), 7)), neighbours=())

def solver(droneAmount, node_list, drone_list):
    shortestDistance = float("inf") #infinitely large number
    shortestPath = []

    if globalGraph == -1:
        return "graph file failed to load"

    if len(node_list) < 1 or len(drone_list) < 1:   #check if any towers / drones were picked
        return "Not enough towers/drones selected"

    pylon_list = fromNodestoPylons(node_list)
    data = []
    for drone in drone_list:
        if data == []:
            pylon_list = [fromDronetoPylon(drone)] + pylon_list
            data = create_distance_route_matrix(droneAmount, pylon_list)
        else:
            pylon_list[0] = fromDronetoPylon(drone)
            data = modify_distance_route_matrix(data, pylon_list)
        if data == []:
            pylon_list = fromNodestoPylons(node_list)
            continue

        manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']), data['num_vehicles'], data['starts'], data['ends'])
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

#----------------------SOLVER OPTIONS-------------------------------SOLVER OPTIONS-------------------------SOLVER OPTIONS----------------------------
        search_parameters = localSearch(len(node_list))
        #search_parameters = firstSolution()
#----------------------SOLVER OPTIONS-------------------------------SOLVER OPTIONS-------------------------SOLVER OPTIONS----------------------------

        assignment = routing.SolveWithParameters(search_parameters)

        #Prints result if solution is found
        if assignment:
            totalDistance, droneRoutes = print_solution(data, manager, routing, assignment)
            routesCoordinates = []
            for droneRoute in droneRoutes:
                routeCoordinates = []
                for step in range(len(droneRoute)-1):
                    coordinates = []
                    for tower in data['routeMatrix'][droneRoute[step]][droneRoute[step+1]]:
                        coordinates.append(tower.latlon)
                    if step != (len(droneRoute)-2):
                        routeCoordinates += coordinates[:-1]
                    else:
                        routeCoordinates += coordinates
                routesCoordinates.append(routeCoordinates)
            if not isinstance(drone, pylon):
                routesCoordinates.insert(0, drone[0])
            if totalDistance < shortestDistance:
                shortestDistance = totalDistance
                shortestPath = routesCoordinates
    #returns path with optimal available drone or fails
    if shortestPath == []:
        return "Failed to find route"
    else:
        return shortestPath

def selectAllTowersOnPath(startNode, endNode):
    if globalGraph == -1:
        return "graph file failed to load"

    startPoint = pylon(int(startNode[0]), latlon=(round(float(startNode[2]), 7), round(float(startNode[1]), 7)), neighbours=())
    endPoint = pylon(int(endNode[0]), latlon=(round(float(endNode[2]), 7), round(float(endNode[1]), 7)), neighbours=())
    try:
        path = nx.astar_path(globalGraph, startPoint, endPoint, heuristic=dist)
    except (nx.NetworkXNoPath, nx.exception.NodeNotFound) as e:
        return "Couldn't find route between Towers"
    path = path[1:-1]

    pathLatlon = []
    for node in path:
        pathLatlon.append(node.latlon)

    return pathLatlon

if __name__ == "__main__":
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
