from lark import Lark

class ADNParser:
    def __init__(self):
        with open("frontend/parser/sql.lark", "r") as file:
            # Perform operations on the opened file here
            # For example, you can read its contents or process it line by line
            file_contents = file.read()
        self.parser = Lark(file_contents, start="start")

    def parse(self, sql):
        return self.parser.parse(sql)

