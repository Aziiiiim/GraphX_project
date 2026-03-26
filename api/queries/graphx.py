from utils.conf_spark import sql_context

def request():
    test()
    return "<p>Graph</p>"

def test():
    subway_routes_df = sql_context.sql(
    """
        SELECT DISTINCT * FROM routes r
        WHERE agency_id = "IDFM:Operator_100"  
            AND route_type = 1
    """)

    subway_routes_df.show()

    subway_routes_df.createOrReplaceTempView("subway_routes")