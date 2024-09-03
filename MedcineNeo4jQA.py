from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from zhipuai import ZhipuAI
from langchain_community.graphs import Neo4jGraph
import ast
import re

app = FastAPI()

client = ZhipuAI(
    api_key=""
)

# 连接Neo4j数据库
uri = "" # example bolt://10.125.59.11:7687
userName = "neo4j"
password = ""
graph = Neo4jGraph(url=uri, username=userName, password=password, sanitize=True, refresh_schema=True)

class Question(BaseModel):
    content: str

async def get_entities(text):
    print(f"Received text for entity recognition: {text}")
    try:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": "你是一个命名实体识别专家。请从给定的文本中识别出所有的命名实体，并以Python列表的形式返回。"},
                {"role": "user", "content": f"请识别以下文本中的命名实体：\n\n{text}"}
            ],
            stream=False,
        )
        content = response.choices[0].message.content
        # Replace curly quotes with straight quotes
        content = content.replace('"', '"').replace('"', '"')
        # Extract the list from the content
        match = re.search(r'\[.*?\]', content, re.DOTALL)
        if match:
            entities_str = match.group(0)
            entities = ast.literal_eval(entities_str)
            print(f"识别到的实体: {entities}")
            return entities
        else:
            print("No list found in the response")
            return []
    except Exception as e:
        print(f"实体识别出错: {str(e)}")
        return []

async def query_neo4j(entities):
    try:
        # 构建Cypher查询
        cypher_query = f"""
        MATCH (n)
        WHERE n.name IN {entities}
        WITH n
        OPTIONAL MATCH (n)-[r]-(m)
        WHERE type(r) IN ['目录', '包括', '条文', '症状', '方剂', '组成', '服用方法', '别名', '集注', '按', '注']
        RETURN n.name AS source, type(r) AS relation, m.name AS target, 
               labels(n)[0] AS source_type, labels(m)[0] AS target_type
        LIMIT 20
        """

        # 执行Neo4j查询
        results = graph.query(cypher_query)
        print(results)
        # 构建上下文
        context = []
        for row in results:
            source = row['source']
            relation = row['relation']
            target = row['target']
            source_type = row['source_type']
            target_type = row['target_type']
            if relation:
                context.append(f"{source_type} '{source}' {relation} {target_type} '{target}'")
            else:
                context.append(f"{source_type} '{source}' 被提及")
        print(context)
        return "\n".join(context)
    except Exception as e:
        print(f"Neo4j查询出错: {str(e)}")
        return ""

@app.post("/answer")
async def answer(question: Question):
    try:
        # 使用大模型进行命名实体识别
        entities = await get_entities(question.content)

        # 查询Neo4j获取实体和关系信息
        context = await query_neo4j(entities)
        print("context:",context)
        # 构建带有上下文的提示
        prompt = f"""基于以下信息回答问题：

上下文信息：
{context}

问题：{question.content}

请根据上下文信息回答问题。如果上下文中没有足够的信息，请说明无法回答或需要更多信息。"""

        # 调用AI模型回答问题
        print("prompt:",prompt)
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": "你是一个专门回答中医相关问题的智能助手。请根据提供的上下文信息回答问题。上下文中包含了实体之间的关系，请利用这些信息来回答问题。如果信息不足，请诚实地说明。"},
                {"role": "user", "content": prompt}
            ],
            stream=False,
        )
        
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ... 保留原有的代码 ...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
