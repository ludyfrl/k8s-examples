from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("test-spark-job").getOrCreate()

text_file = spark.read.text("/opt/spark/app/words.txt")
word_counts = text_file.selectExpr("explode(split(value, ' ')) as word").groupBy("word").count()

word_counts.show()
spark.stop()