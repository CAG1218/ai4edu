"""
Neo4j 知识图谱种子数据脚本（独立版 v2）
修复：subject 字段使用英文 id（与 graph_service.SUBJECT_CATEGORIES 一致）
用法: python seed_knowledge_graph_standalone.py
"""
import json
import sys

try:
    from neo4j import GraphDatabase
except ImportError:
    print("Please install neo4j first: python -m pip install neo4j")
    sys.exit(1)

# ============ 配置 ============
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "neo4j_password"
# =================================


NODES = [
    # 数学 (subject="math")
    {"id": "math_function_basic", "name": "函数基础", "subject": "math",
     "description": "函数的概念、定义域、值域、图像等基本知识",
     "cognitive_level": json.dumps({"memory": 0.8, "understanding": 0.7, "application": 0.5, "analysis": 0.3, "evaluation": 0.2, "creation": 0.1})},
    {"id": "math_quadratic_function", "name": "二次函数", "subject": "math",
     "description": "二次函数的图像、性质、解析式求解及应用",
     "cognitive_level": json.dumps({"memory": 0.6, "understanding": 0.8, "application": 0.9, "analysis": 0.6, "evaluation": 0.3, "creation": 0.2})},
    {"id": "math_triangle_function", "name": "三角函数", "subject": "math",
     "description": "正弦、余弦、正切函数的定义、图像与性质",
     "cognitive_level": json.dumps({"memory": 0.5, "understanding": 0.7, "application": 0.8, "analysis": 0.6, "evaluation": 0.3, "creation": 0.2})},
    {"id": "math_derivative", "name": "导数", "subject": "math",
     "description": "导数的概念、计算法则、几何意义及实际应用",
     "cognitive_level": json.dumps({"memory": 0.4, "understanding": 0.7, "application": 0.9, "analysis": 0.8, "evaluation": 0.4, "creation": 0.3})},
    {"id": "math_integral", "name": "积分", "subject": "math",
     "description": "不定积分、定积分的概念、计算及应用",
     "cognitive_level": json.dumps({"memory": 0.3, "understanding": 0.6, "application": 0.9, "analysis": 0.8, "evaluation": 0.4, "creation": 0.3})},
    {"id": "math_limit", "name": "极限", "subject": "math",
     "description": "极限的定义、运算法则及在导数中的应用",
     "cognitive_level": json.dumps({"memory": 0.5, "understanding": 0.8, "application": 0.6, "analysis": 0.7, "evaluation": 0.3, "creation": 0.2})},
    # 物理 (subject="physics")
    {"id": "physics_newton_law", "name": "牛顿运动定律", "subject": "physics",
     "description": "牛顿第一、二、三定律的内容、表达式及应用",
     "cognitive_level": json.dumps({"memory": 0.7, "understanding": 0.8, "application": 0.9, "analysis": 0.7, "evaluation": 0.4, "creation": 0.2})},
    {"id": "physics_energy", "name": "能量守恒", "subject": "physics",
     "description": "动能、势能、机械能守恒定律及应用",
     "cognitive_level": json.dumps({"memory": 0.6, "understanding": 0.8, "application": 0.9, "analysis": 0.7, "evaluation": 0.4, "creation": 0.3})},
    {"id": "physics_electric_field", "name": "电场", "subject": "physics",
     "description": "电场强度、电势、电容的基本概念及计算",
     "cognitive_level": json.dumps({"memory": 0.5, "understanding": 0.7, "application": 0.8, "analysis": 0.7, "evaluation": 0.3, "creation": 0.2})},
    {"id": "physics_magnetic_field", "name": "磁场", "subject": "physics",
     "description": "磁感应强度、安培力、洛伦兹力及电磁感应",
     "cognitive_level": json.dumps({"memory": 0.4, "understanding": 0.7, "application": 0.8, "analysis": 0.7, "evaluation": 0.3, "creation": 0.2})},
    {"id": "physics_circuit", "name": "电路分析", "subject": "physics",
     "description": "欧姆定律、串并联电路、基尔霍夫定律",
     "cognitive_level": json.dumps({"memory": 0.6, "understanding": 0.8, "application": 0.9, "analysis": 0.8, "evaluation": 0.4, "creation": 0.2})},
]

RELATIONSHIPS = [
    # 数学内部
    ("math_limit", "math_derivative", "PREREQUISITE", "prerequisite"),
    ("math_derivative", "math_integral", "PREREQUISITE", "prerequisite"),
    ("math_function_basic", "math_quadratic_function", "RELATED", "related"),
    ("math_function_basic", "math_triangle_function", "RELATED", "related"),
    ("math_quadratic_function", "math_derivative", "RELATED", "application example"),
    ("math_triangle_function", "math_derivative", "RELATED", "differentiation target"),
    # 物理内部
    ("physics_newton_law", "physics_energy", "RELATED", "theoretical basis"),
    ("physics_electric_field", "physics_circuit", "RELATED", "electric field in circuits"),
    ("physics_magnetic_field", "physics_electric_field", "RELATED", "electromagnetic unity"),
    ("physics_circuit", "physics_energy", "RELATED", "energy conversion"),
    # 跨学科
    ("math_derivative", "physics_newton_law", "APPLICATION", "kinematics application"),
    ("math_integral", "physics_energy", "APPLICATION", "work and energy calculation"),
    ("math_function_basic", "physics_circuit", "APPLICATION", "I-V characteristic curve"),
]


def seed(driver):
    with driver.session() as session:
        # 清空已有数据
        print("Clearing existing KnowledgeNode nodes...")
        session.run("MATCH (n:KnowledgeNode) DETACH DELETE n")
        print("Clear complete.\n")

        # 创建节点
        print("=== Creating knowledge nodes ===")
        for node in NODES:
            try:
                result = session.run(
                    """
                    MERGE (n:KnowledgeNode {id: $id})
                    SET n.name = $name,
                        n.subject = $subject,
                        n.description = $description,
                        n.cognitive_level = $cognitive_level,
                        n.created_at = datetime()
                    RETURN n
                    """,
                    id=node["id"],
                    name=node["name"],
                    subject=node["subject"],
                    description=node["description"],
                    cognitive_level=node["cognitive_level"],
                )
                rec = result.single()
                print(f"  [OK] {node['name']} ({node['id']}) subject={node['subject']}")
            except Exception as e:
                print(f"  [FAIL] {node['name']}: {e}")

        # 创建关系
        print("\n=== Creating relationships ===")
        for from_id, to_id, rel_type, label in RELATIONSHIPS:
            try:
                cypher = (
                    "MATCH (a:KnowledgeNode {id: $from_id}) "
                    "MATCH (b:KnowledgeNode {id: $to_id}) "
                    "MERGE (a)-[r:`%s` {type: $rel_type, label: $label}]->(b) "
                    "RETURN r"
                ) % rel_type
                result = session.run(
                    cypher,
                    from_id=from_id,
                    to_id=to_id,
                    rel_type=rel_type,
                    label=label,
                )
                rec = result.single()
                if rec:
                    print(f"  [OK] {from_id} --[{label}]--> {to_id}")
                else:
                    print(f"  [FAIL] {from_id} --> {to_id} (node may not exist)")
            except Exception as e:
                print(f"  [FAIL] {from_id} --[{label}]--> {to_id}: {e}")

        # 验证
        print("\n=== Verifying results ===")
        count_result = session.run("MATCH (n:KnowledgeNode) RETURN count(n) AS cnt")
        total = count_result.single()["cnt"]
        print(f"  Total nodes: {total}")

        subject_result = session.run(
            "MATCH (n:KnowledgeNode) RETURN n.subject AS subject, count(n) AS cnt ORDER BY cnt DESC"
        )
        for rec in subject_result:
            print(f"    subject={rec['subject']}: {rec['cnt']} nodes")

        rel_result = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt")
        rel_count = rel_result.single()["cnt"]
        print(f"  Total relationships: {rel_count}")

    print("\n=== Seed data write complete ===")


if __name__ == "__main__":
    print(f"Connecting to Neo4j: {URI}")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    try:
        driver.verify_connectivity()
        print("Neo4j connection successful.\n")
        seed(driver)
    except Exception as e:
        print(f"Neo4j connection failed: {e}")
        sys.exit(1)
    finally:
        driver.close()
