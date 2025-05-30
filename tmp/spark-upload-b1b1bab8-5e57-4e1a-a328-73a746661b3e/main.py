from pyspark.sql import SparkSession
from pyspark import SparkFiles

spark = SparkSession.builder.appName("test-spark-job").getOrCreate()

file_path = SparkFiles.get("words.txt")
print(file_path)
# text_file = spark.read.text(file_path)
# word_counts = text_file.selectExpr("explode(split(value, ' ')) as word").groupBy("word").count()

# word_counts.show()
spark.stop()