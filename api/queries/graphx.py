from utils.conf_spark import sql_context, spark
from graphframes import GraphFrame

def request():
    routes_df = sql_context.read.csv("s3a://graphx/data/gtfs/routes.txt", header=True, inferSchema=True)
    routes_df.createOrReplaceTempView("routes")
    stops_df = sql_context.read.csv("s3a://graphx/data/gtfs/stops.txt", header=True, inferSchema=True)
    stops_df.createOrReplaceTempView("stops")
    stops_times_df = sql_context.read.csv("s3a://graphx/data/gtfs/stop_times.txt", header=True, inferSchema=True)
    stops_times_df.createOrReplaceTempView("stop_times")
    trips_df = sql_context.read.csv("s3a://graphx/data/gtfs/trips.txt", header=True, inferSchema=True)
    trips_df.createOrReplaceTempView("trips")
    
    subway_routes_df = sql_context.sql(
    """
        SELECT DISTINCT * FROM routes r
        WHERE agency_id = "IDFM:Operator_100"  
            AND route_type = 1
    """)

    subway_routes_df.createOrReplaceTempView("subway_routes")
        
    subway_trips_df = sql_context.sql(
        """SELECT DISTINCT
            t.trip_id,
            r.route_id,
            r.route_long_name,
            st.stop_sequence,
            s.stop_name,
            s.stop_id,
            s.stop_lon,
            s.stop_lat,
            parent_station,
            t.direction_id
        FROM trips t
        JOIN subway_routes r ON t.route_id = r.route_id
        JOIN stop_times st ON t.trip_id = st.trip_id
        JOIN stops s ON st.stop_id = s.stop_id
        ORDER BY t.trip_id, st.stop_sequence"""
    )

    subway_trips_df.createOrReplaceTempView("subway_trips")

    subway_stops_df = sql_context.sql("""
        SELECT DISTINCT 
            stop_id, 
            parent_station,
            stop_name
        FROM subway_trips
        ORDER BY stop_name
    """)
    subway_stops_df.createOrReplaceTempView("subway_stops")

    mapping_df = sql_context.sql("""
        SELECT 
            stop_id, 
            COALESCE(parent_station, stop_id) as unique_stop_id,
            stop_name
        FROM subway_stops
    """)
    mapping_df.createOrReplaceTempView("stop_mapping")

    vertices_df = sql_context.sql("""
        SELECT DISTINCT 
            m.unique_stop_id AS id, 
            m.stop_name
        FROM subway_trips t
        JOIN stop_mapping m ON t.stop_id = m.stop_id
        ORDER BY stop_name
    """)

    edges_unclean_df = sql_context.sql("""
        SELECT DISTINCT
            stop_id AS src,
            next_stop_id AS dst,
            route_id,
            direction_id
        FROM (
            SELECT 
                stop_id,
                LEAD(stop_id) OVER (PARTITION BY trip_id ORDER BY stop_sequence) AS next_stop_id,
                route_id,
                direction_id
            FROM subway_trips
        )
        WHERE next_stop_id IS NOT NULL
    """)

    edges_unclean_df.createOrReplaceTempView("edges_unclean")

    edges_df = sql_context.sql("""
        SELECT
            sm.unique_stop_id as src,
            sm.stop_name as src_stop_name,
            dm.unique_stop_id as dst,
            dm.stop_name as dst_stop_name,
            e.route_id,
            e.direction_id
        FROM edges_unclean e
        JOIN stop_mapping sm ON e.src = sm.stop_id          
        JOIN stop_mapping dm ON e.dst = dm.stop_id 
        ORDER BY e.route_id         
    """)

    local_vertices = vertices_df.select("id", "stop_name").distinct().collect()
    local_edges = edges_df.select("src", "dst").distinct().collect()

    v_final = spark.createDataFrame(local_vertices, ["id", "stop_name"])
    e_final = spark.createDataFrame(local_edges, ["src", "dst"])

    g = GraphFrame(v_final, e_final)

    g.pageRank(resetProbability=0.15, maxIter=5).vertices.show()

    return "<p>Graph</p>"

def test():
    pass