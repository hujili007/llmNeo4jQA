# llmNeo4jQA

基于智谱大模型和neo4j图数据库进行问答的样例代码

## Getting Started

### step 1 Clone this repository

```
Clone the repo.
$ git clone https://github.com/hujili007/llmNeo4jQA.git
$ cd llmNeo4jQA
```

### step 2 Installation

Set up conda environment

```
# create a new environment
$ conda create --name llmNeo4jQA python=3.10 -y
$ conda activate llmNeo4jQA
$ pip install zhipuai -U
$ pip install langchain
$ pip install langchain-community
```

### step 3 Run MedcineNeo4jQA.py

```
$ pyhon MedcineNeo4jQA.py
```

### step 4 Use postman to test the api interface

```
http://localhost:8000/answer
```

