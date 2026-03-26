from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv

load_dotenv()

spark = SparkSession.builder \
    .appName('SparkApp') \
    .master('spark://spark:7077') \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262,org.apache.spark:spark-hadoop-cloud_2.12:3.5.3,graphframes:graphframes:0.8.3-spark3.5-s_2.12") \
    .config("spark.hadoop.fs.s3a.committer.name", "staging") \
    .config("spark.hadoop.mapreduce.outputcommitter.factory.scheme.s3a", "org.apache.hadoop.fs.s3a.commit.S3ACommitterFactory") \
    .config("spark.hadoop.fs.s3a.committer.staging.tmp.path", "/tmp/s3a-commit") \
    .config("spark.hadoop.fs.s3a.committer.staging.unique-filenames", "true") \
    .config("spark.hadoop.fs.s3a.committer.staging.conflict-mode", "replace") \
    .getOrCreate()

sc = spark.sparkContext

sc._jsc.hadoopConfiguration().set("fs.s3a.endpoint", f"http://{os.getenv('minio_ip_address')}:3900")
sc._jsc.hadoopConfiguration().set("fs.s3a.access.key", os.getenv('key_id'))
sc._jsc.hadoopConfiguration().set("fs.s3a.endpoint.region", "garage")
sc._jsc.hadoopConfiguration().set("fs.s3a.secret.key", os.getenv('secret_key'))
sc._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")
sc._jsc.hadoopConfiguration().set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
sc._jsc.hadoopConfiguration().set("fs.s3a.connection.ssl.enabled", "false")

# For backward compatibility
sql_context = spark