COUNTRIES = (("countries",),{'type':str,'nargs':'+','help':"countries to route on",'metavar':'COUNTRY'})
GRAPH = (("graph_file",),{'type':str,'help':"use graph file GRAPH",'metavar':'GRAPH'})
HTML = (("html_file",),{'type':str,'help':"use rendered HTML file",'metavar':'HTML'})
RHOST = (("--render-host",),{'type':str,'dest':'r_host','default':'127.0.0.1','help':"render hostname (default: 127.0.0.1)",'metavar':'HOST'})
RPORT = (("--render-port",),{'type':int,'dest':'r_port','default':5000, 'help':"render port number (default: 5000)",'metavar':'PORT'})
RPREFIX = (("--render-prefix",),{'type':str,'dest':'r_prefix','default':'','help':"render URI prefix (default: '')",'metavar':'PREFIX'})
HOST = (("--host",),{'type':str,'dest':'host','default':'0.0.0.0','help':"hostname (default: 0.0.0.0)",'metavar':'HOST'})
PORT = (("--port",),{'type':int,'dest':'port','default':5000, 'help':"port number (default: 5000)",'metavar':'PORT'})
PREFIX = (("--prefix",),{'type':str,'dest':'prefix','default':'','help':"URI prefix (default: '')",'metavar':'PREFIX'})
OSM = (("--osm",),{'action':'store_true','dest':'osm','default':False,'help':"process from OSM file (SLOW)"})
NOBROWSER = (("-n","--no-browser"),{'action':'store_true','dest':'no_browser','default':False,'help':"do not open html in browser (headless)"})
URL = (("-d","--download-url"),{'type':str,'dest':'url','help':"define url for download directory to be URL",'metavar':'URL'})
SHOW = (("-l","--list"),{'action':'store_true','dest':'show','default':False,'help':"list available countries (default: False)"})
CONSERVEMEM = (("-c","--conserve-memory"),{'action':'store_true','dest':'conserve_mem','default':False,'help':"lower memory usage but higher runtime"})

CONFIG = [
    ("auto",{'help':"start HTTP server for given COUNTRY (default: Europe)",'args':[SHOW,URL,CONSERVEMEM,NOBROWSER,HOST,PORT,PREFIX,RHOST,RPORT,RPREFIX,OSM,COUNTRIES]}),
    ("nx",{'help':"start HTTP server for given GRAPH and rendered HTML file",'args':[SHOW,URL,NOBROWSER,HOST,PORT,PREFIX,RHOST,RPORT,RPREFIX,GRAPH,HTML]}),
    ("npz",{'help':"start HTTP server for given GRAPH and rendered HTML file",'args':[SHOW,URL,NOBROWSER,HOST,PORT,PREFIX,RHOST,RPORT,RPREFIX,GRAPH,HTML]})
]

def serve_auto(countries,host="localhost",port=5000,prefix="",osm=False,url=None,show=False,no_browser=False,r_host="localhost",r_port=5000,r_prefix="",conserve_mem=False):
    from limic.download import common, download_graph, download_merged, download_osm
    from limic.init import extract_osm_all, merge_all
    from limic.render import render_nx
    graph_file = None
    if osm:
        countries, url = common(countries=countries,url=url,show=show,osm=osm,join=False)
        download_osm(countries=countries,url=url)
        extract_osm_all(countries=countries,conserve_mem=conserve_mem)
    else:
        countries, url = common(countries=countries,url=url,show=show,osm=osm,join=True)
        download_graph(suffix="npz",countries=countries,url=url,show=show,join=True)
    if len(countries) > 1 :
        merge_all(countries)
    if len(countries) == 1:
        graph_file = "graph."+countries[0]+(".nx" if osm else ".npz")
    html_file = graph_file[:-2]+"html"
    if osm:
        serve_nx(graph_file,html_file,host=host,port=port,prefix=prefix,url=url,show=show,no_browser=no_browser,r_host=r_host,r_port=r_port,r_prefix=r_prefix)
    else:
        serve_npz(graph_file,html_file,host=host,port=port,prefix=prefix,url=url,show=show,no_browser=no_browser,r_host=r_host,r_port=r_port,r_prefix=r_prefix)


def serve_nx(graph_file,html_file,host="localhost",port=5000,prefix="",url=None,show=False,no_browser=False,r_host="localhost",r_port=5000,r_prefix=""):
    from limic.render import render_nx
    from limic.route import astar_nx
    g,nodes = render_nx(graph_file,html_file,host=r_host,port=r_port,prefix=r_prefix)
    serve(g,nodes,astar_nx,html_file,host,port,prefix,url,show,no_browser,r_host,r_port,r_prefix)

def serve_npz(graph_file,html_file,host="localhost",port=5000,prefix="",url=None,show=False,no_browser=False,r_host="localhost",r_port=5000,r_prefix=""):
    from limic.render import render_npz
    from limic.route import astar_npz
    g,nodes = render_npz(graph_file,html_file,host=r_host,port=r_port,prefix=r_prefix)
    serve(g,nodes,astar_npz,html_file,host,port,prefix,url,show,no_browser,r_host,r_port,r_prefix)

def serve(g,nodes,astar,html_file,host="localhost",port=5000,prefix="",url=None,show=False,no_browser=False,r_host="localhost",r_port=5000,r_prefix=""):
    from flask import Flask, jsonify, request
    from limic.util import load_pickled, start, end, status
    from threading import Thread
    from time import sleep
    from webbrowser import open as wopen
    from scipy.spatial import cKDTree as KDTree
    from pyproj import CRS, Transformer

    start("Initializing KD-Tree")
    crs_4326 = CRS("WGS 84")
    crs_proj = CRS("EPSG:28992")
    transformer = Transformer.from_crs(crs_4326, crs_proj)
    tree = KDTree(list(map(lambda x:transformer.transform(x[1],x[2]),nodes)))
    end()

    start("Setting up the app")
    app = Flask("LiMiC")

    @app.route(prefix+"/")
    def hello():
        return open(html_file).read()

    @app.route(prefix+"/tower")
    def tower():
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
        start("Finding tower",lat,lng)
        tower = nodes[tree.query(transformer.transform(lat,lng))[1]]
        end('')
        res = jsonify(tower=tower)
        end()
        return res

    @app.route(prefix+"/route")
    def route():
        source_lat = float(request.args.get('source[lat]'))
        source_lng = float(request.args.get('source[lng]'))
        target_lat = float(request.args.get('target[lat]'))
        target_lng = float(request.args.get('target[lng]'))
        print("SOURCE COMING UP")
        print(source_lat)
        start("Routing",source_lat,source_lng,target_lat,target_lng)
        source_index = tree.query(transformer.transform(source_lat,source_lng))[1]
        source = nodes[source_index]
        end('')
        target_index = tree.query(transformer.transform(target_lat,target_lng))[1]
        target = nodes[target_index]
        end('')
        path = astar(g,(source,source_index),(target,target_index))
        end('')
        if path[1][-1][0] == float('inf'):
            path[1][-1] = (path[1][-1][1],)+path[1][-1][1:]
        res = jsonify(path=path)
        end()
        return res
    end()

    @app.route(prefix+"/tsp")
    def tsp():
        import sys
        sys.path.append("..")
        from BP2_TSP.astar import solver, pylon  #sys path append added to use tsp solver from parent directory
        allDrones = []
        i = 0
        newDrone = list(request.args.getlist('drones[' + str(i) + '][]'))
        while(newDrone != []):
            i+=1
            allDrones.append(newDrone)
            newDrone = list(request.args.getlist('drones[' + str(i) + '][]'))

        allTowers = []
        i = 0
        newTower = list(request.args.getlist('towers[' + str(i) + '][]'))
        while(newTower != []):
            i+=1
            allTowers.append(newTower)
            newTower = list(request.args.getlist('towers[' + str(i) + '][]'))

        towers = list(request.args.getlist('towers'))
        drones = list(request.args.getlist('drones[0][]'))

        path = solver(1, allTowers, allDrones)
        res = jsonify(path=path)
        return res

    @app.route(prefix+"/selectAll")
    def selectAll():
        import sys
        sys.path.append("..")
        from BP2_TSP.astar import selectAllTowersOnPath, pylon  #sys path append added to use tsp solver from parent directory

        first = list(request.args.getlist('first[]'))
        second = list(request.args.getlist('second[]'))

        path = selectAllTowersOnPath(first, second)
        res = jsonify(path=path)
        return res



    @app.route(prefix+"/graph")
    def graph():
        file = open("../BP3_Webinterface/bachelorProject/openlayers/data/export1.geojson","r")
        return file.read()

    @app.route(prefix+"/no_zone")
    def no_zone():
        file = open("../BP3_Webinterface/bachelorProject/openlayers/data/no_zone.geojson","r")
        return file.read()

    @app.route(prefix+"/marker")
    def marker():
        from flask import send_file
        return send_file("../BP3_Webinterface/bachelorProject/openlayers/data/marker.png")

    class OpenThread(Thread):
        def run(self):
            delay = 0.5
            sleep(delay)
            url = "http://%s:%d%s/" % (r_host,r_port,r_prefix)
            start("Open",url,"in browser")
            wopen(url,new=2)
            status("DONE")
    if not no_browser:
        OpenThread().start()
    app.run(host=host,port=port)
