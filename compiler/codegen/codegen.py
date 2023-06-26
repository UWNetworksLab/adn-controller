from codegen.helper import *
from codegen.snippet import *

def compile_sql_to_rust(ast, ctx):
    if ast["type"] == "CreateTableAsStatement":
        return handle_create_table_as_statement(ast, ctx)
    if ast["type"] == "SelectStatement":
        if ast.get("join") is not None:
            return handle_select_join_statement(ast, ctx)
        elif ast.get("where") is not None:        
            return handle_select_where_statement(ast, ctx)
        else:
            return handle_select_simple_statement(ast, ctx)
    elif ast["type"] == "CreateTableStatement":
        return handle_create_table_statement(ast, ctx)
    elif ast["type"] == "InsertStatement":
        return handle_insert_statement(ast, ctx)
    elif ast["type"] == "SetStatement":
        return handle_set_statement(ast, ctx)
    else:
        print(ast)
        raise ValueError("Unsupported SQL statement")

def handle_create_table_statement(ast, ctx):
    table_name = ast["table_name"]
    if table_name == "output":
        raise ValueError("Table name 'output' is reserved")
    if table_name.endswith("_file"):
        ret = generate_create_for_file(ast, ctx, table_name)
    else:
        ret = generate_create_for_vec(ast, ctx, table_name)
    return ret
 
def handle_insert_statement(node, ctx):
    table_name = node["table_name"]
    table = ctx["tables"].get(table_name)
    if table is None:
        raise ValueError("Table does not exist")
    vec_name = table["name"]
    columns = ', '.join(node["columns"])
    value = node["values"][0]
    if type(value) != list and value["type"] == "SelectStatement":
        select = value
        select["to"] = table_name
        select_statement = handle_select_simple_statement(select, ctx)
        rust_code = f"for event in {select_statement} {{"
        if table_name.endswith("file"):
            file_name = table["file_field"]
            rust_code += f"write!(self.{file_name}, \"{{}}\", event);"
        else:
            rust_code += f"{vec_name}.push(event);"
        rust_code += f"}}"
    else:
        codes = ""
        struct_name = table["struct"]["name"]
        fields = table["struct"]["fields"]
        fields = [i["name"] for i in fields]
        for value in node["values"]:
            values = ""
            for k, v in zip(fields, value):
                if v["data_type"] == "string":
                    v = v["value"].replace("'", "")
                values += f"{k}: \"{v}\".to_string(), "
            codes += f"{vec_name}.push({struct_name} {{{values[:-2]}}})\n"
        rust_code = codes
    if table_name != "output":
        rust_code = begin_sep("init") + rust_code + end_sep("init")
    return rust_code
        
def handle_select_simple_statement(node, ctx):
    table_from = node["from"]
    if ctx["tables"].get(table_from) is None:
        raise ValueError("Table does not exist")
    table_from = ctx["tables"][table_from]
    table_from_name = table_from["name"]
    if len(node["columns"]) == 1 and node["columns"][0] == "*":
        columns = [i["name"] for i in table_from["struct"]["fields"]]
    else:
        columns = node["columns"]
    if table_from_name == "input":
        # TODO test protobuf
        columns = [input_mapping(i) for i in columns]
        columns = ', '.join(columns)
    else:
        columns = [f"req.{i}.clone()" for i in columns]
        columns = ', '.join(columns).replace("req.CURRENT_TIMESTAMP.clone()", "Utc::now()")
    if node.get("to") is not None:
        table_to = node["to"]
        if ctx["tables"].get(table_to) is None:
            raise ValueError("Table does not exist")
        table_to = ctx["tables"][table_to]
        struct = table_to["struct"]["name"]
    else:
        struct = table_from["struct"]["name"]
        
    return f"{table_from_name}.iter().map(|req| {struct}::new({columns})).collect::<Vec<_>>()"

def handle_create_table_as_statement(node, ctx):
    new_table = node["table_name"]
    if new_table != "output":
        raise NotImplementedError("Currently only output table is supported")
    select = node["select"]
    select_statement = compile_sql_to_rust(select, ctx)
    if select["type"] == "SelectJoinStatement":
        return f"let {new_table}: Vec<_> = {select_statement};"
    elif select["type"] == "SelectWhereStatement":
        return f"let {new_table}: Vec<_> = {select_statement};"
    elif select["type"] == "SelectStatement":
        return f"let {new_table}: Vec<_> = {select_statement};"
    else:
        raise ValueError("Unsupported select statement type")

def handle_select_join_statement(node, ctx):
    join_condition = handle_binary_expression(node["join"], ctx)
    where_condition = handle_binary_expression(node["where"], ctx)
    join_table_name = node["join"]["table"] 
    from_table_name = node["from"]
    from_table_name = ctx["tables"][from_table_name]["name"]
    if ctx["tables"].get(join_table_name) is None:
        raise ValueError("Table does not exist")
    if ctx["tables"].get(from_table_name) is None:
        raise ValueError("Table does not exist")
    join_vec_name = ctx["tables"][join_table_name]["name"]
    from_vec_name = ctx["tables"][from_table_name]["name"]
    if from_vec_name != "input" and from_vec_name != "output":
        from_vec_name = f"self.{from_vec_name}"
    if join_vec_name != "input" and join_vec_name != "output":
        join_vec_name = f"self.{join_vec_name}"
    func = generate_join_filter_function(join_condition, where_condition, from_table_name, join_table_name, ctx["proto"])
    #gen_filter_function(from_table_name, join_table_name, join_condition)
    return f"iproduct!({from_vec_name}.iter(), {join_vec_name}.iter()).map({func}).collect()"

def handle_binary_expression(node, ctx):
    #print(node)
    if node["type"] == "BinaryExpression":
        lt = node["left"]["table_name"] if node["left"]["data_type"] == "Column" else "Literal"
        lc = node["left"]["column_name"] if node["left"]["data_type"] == "Column" else node["left"]["value"]
        rt = node["right"]["table_name"] if node["right"]["data_type"] == "Column" else "Literal"
        rc = node["right"]["column_name"] if node["right"]["data_type"] == "Column" else node["right"]["value"]
        op = node["operator"]
    elif node["type"] == "JoinOn":
        cond = node["condition"]
        lt = cond["left"]["table_name"]
        lc = cond["left"]["column_name"]
        rt = cond["right"]["table_name"]
        rc = cond["right"]["column_name"]
        op = cond["operator"]  
        if op == '=':
            op = "=="
    if rt == "Literal":
        rc = rc.replace("'", "\"")
    if lt == "Literal":
        lc = lc.replace("'", "\"")
    return {"lt": lt, "lc": lc, "rt": rt, "rc": rc, "op": op}

def handle_set_statement(node, ctx):
    variable_name = node["variable"].replace('@', '')
    ctx["vars"][variable_name] = {
        'name': "var_" + variable_name,
        'value': node["value"]
    }
    variable_name = ctx["vars"][variable_name]["name"]
    rust_code = f"let {variable_name} = {node['value']};"
    return rust_code

def handle_select_where_statement(node, ctx):
    where_condition = handle_where_binary_expression(node["where"], ctx)
    return f"{node['from']}.iter().filter(|&item| {where_condition}).cloned().collect()"

def handle_where_binary_expression(node, ctx):
    left = handle_function(node["left"], ctx) if node["left"]["data_type"] == "Function" else node["left"]["name"]
    right = node["right"]["name"].replace('@', '')
    if ctx["vars"].get(right) is None:
        raise ValueError("Variable does not exist")
    right = ctx["vars"][right]["name"]
    op = node["operator"]
    if op == '=':
        op = "=="
    return f"{left} {op} {right}"

def handle_function(node, ctx):
    if node["name"] == "random":
        return "rand::random::<f32>()"
    else:
        raise ValueError("Unsupported function")
    
    
def init_ctx():
    return {
        "tables": {
            "input": {
                "name": "input",
                "type": "Vec",
                "struct": {
                    "name": "RpcMessageTx",
                    "fields": [
                        {"name": "meta_buf_ptr", "type": "MetaBufferPtr"},
                        {"name": "addr_backend", "type": "usize"},
                    ]
                }     
            },
            "output": {
                "name": "output",
                "type": "Vec",
                 "struct": {
                    "name": "RpcMessageTx",
                    "fields": [
                        {"name": "meta_buf_ptr", "type": "MetaBufferPtr"},
                        {"name": "addr_backend", "type": "usize"},
                    ]
                } 
            }
        },
        "vars": {
            
        },
        "proto": {
            "name": "hello",
            "req_type": "hello::HelloRequest",
            "resp_type": "hello::HelloResponse",
        }
    }