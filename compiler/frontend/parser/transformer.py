from lark import Transformer

class ADNTransformer(Transformer):
    
    def __init__(self):
        self.variables = {}

    def start(self, n):
        # print("start", n)
        return n

    def statement(self, s):
        s = s[0]
        return s

    def create_table_as_statement(self, c):
        # print("create_table_as_statement", c)
        res = {
            "type": "CreateTableAsStatement",
            "table_name": c[0]["table_name"],
            "select": {
                "type": "SelectStatement",
                "columns": c[1]["columns"],
                "from": c[1]["from"],
            }
        }

        if "where" in c[1]:
            res["select"]["where"] = c[1]["where"]
        if "join" in c[1]:
            res["select"]["join"] = c[1]["join"]

        return res
    
    def select_statement(self, s):
        # (s,) = s
        #print("select_statement", s)
        res = {
            "type": "SelectStatement",
            "columns": s[0]["columns"],
            "from": s[1]["table_name"],
        }
        if len(s) > 2 and s[2][0] == "where":
            res["where"] = s[2][1]["where"]
        elif len(s) > 2 and s[2][0] == "join":
            res["join"] = s[2][1]
            res["where"] = s[3][1]["where"]
        return res

    def set_statement(self, n):
        (n,) = n
        # print("set_statement", n)
        res = {
            "type": "SetStatement",
            "variable": n["variable"],
            "value": n["value"],
            "data_type": n["data_type"]
        }
        self.variables[n["variable"]] = n["value"]
        # print("set_statement", n)
        return res
    
    def create_table_statement(self, c):
        # print("create_table_statement", c)
        res = {
            "type": "CreateTableStatement",
            "table_name": c[0]["table_name"],
            "columns": c[1:]
        }
        return res
    
    def insert_statement(self, i):
        # print("insert_statement", i)
        res = {
            "type": "InsertStatement",
            "table_name": i[0]["table_name"],
            "columns": i[1]["columns"],
            "values": i[2:]
        }
        return res
    
    def identifier(self, i):
        (i,) = i
        res = {"variable": i.value}
        return res

    def number(self, n):
        # print(n)
        (n,) = n
        res =  {"data_type": "number", "value": n.value}
        return res

    def assignment(self, a):
        res = {
            "type": "assignment",
            "variable": a[0]["variable"],
            "value": a[1]["value"],
            "data_type": a[1]["data_type"]
        }
        # print("assignment", n)
        return res
    
    def data_type(self, d):
        (d,) = d
        # print("data_type", d)
        res = {"data_type": d.value}
        return res

    def length(self, l):
        (l,) = l
        res = {"length": l.value}
        return res
    
    def cname(self, c):
        (c,) = c
        res = {"name": c.value}
        if c.value in self.variables:
            res.update({"data_type": "Variable"})
        return res
    
    def column_definition(self, c):
        # print("column_definition", c)
        res = {"column_name": c[0]["name"], 
            "data_type": c[1]["data_type"]}

        if c[2] != None and "length" in c[2]:
            res["length"] = c[2]["length"]
        return res

    def table_name(self, t):
        (t,) = t
        res = {"table_name": t.value}
        return res
    
    def quoted_string(self, s):
        (s,) = s
        res = {"data_type": "string", "value": s.value}
        return res
    
    def string(self, s):
        return s[0]

    def value_list(self, v):
        return v
    
    def column_list(self, c):
        columns = [column['name'] for column in c]
        # print("column_list", columns)
        res = {"columns": columns}
        return res
    
    def all(self, a):
        # print("all", a)
        return "all"

    def select_list(self, s):
        # print("select_list", s)
        res = {}
        if s == ["all"]:
            res["columns"] = "*"
        else:
            res["columns"] = [column["name"] for column in s]
        return res
    
    def l(self, l):
        return "<"

    def random_func(self, r):
        return "random"
    
    def function(self, f):
        # print("function", f)
        res = {'data_type': 'Function', 'name': f[0]}
        return res

    def comparison_condition(self, c):
        # print("comparision_condition", c)
        res = {
            "type": "BinaryExpression",
            "left": c[0],
            "right": c[2],
            "operator": c[1]
        }
        return res

    def eq(self, c):
        return "=="
    
    def neq(self, c):
        return "!="

    def g(self, c):
        return ">"
    
    def l(self, c):
        return "<"

    def ge(self, c):
        return ">="
    
    def le(self, c):
        return "<="

    def search_condition(self, s):
        # print("search_condition", s)
        (s,) = s
        return s
    
    def where_clause(self, w):
        # print("where_clause", w)
        (w,) = w
        res = ("where", {"where": w})
        return res

    def join_clause(self, j):
        # print("join_clause", j)
        res = ("join", {
            "type": "JoinOn",
            "table": j[0]["table_name"],
            "condition": {
                "left": {"data_type": "Column", "table_name": j[1]['table_name'], "column_name" : j[1]['column_name']},
                "operator": "=",
                "right":{"data_type": "Column", "table_name": j[2]['table_name'], "column_name" : j[2]['column_name']},
            }
        })
        return res

    def column_field(self, c):
        # print("column_field", c)
        res = {
            "data_type": "Column",
            "table_name": c[0]["table_name"],
            "column_name": c[1]["variable"]
        }
        return res
    
    