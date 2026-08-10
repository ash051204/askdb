from askdb.llm import generate

question = "What are the top 5 best-selling albums by revenue?"

sql = generate(f"Write a SQL query to answer this question: {question}")

print(sql)
