from intbase import InterpreterBase, ErrorType
import bparser as b

BREWIN_TYPE_MAP = {
    "int": int,
    "bool": bool,
    "str": str,
}

CLASS_DEF = 'class'
METHOD_DEF = 'method'
FIELD_DEF = 'field'
NULL_DEF = 'null'
BEGIN_DEF = 'begin'
SET_DEF = 'set'
INPUTI_DEF = 'inputi'
WHILE_DEF = 'while'
RETURN_DEF = 'return'
PRINT_DEF = 'print'
CALL_DEF = 'call'
IF_DEF = 'if'
VARIABLE_DEF = 'variable'
MAIN_DEF = 'main'
NEW_DEF = 'new'
INPUTS_DEF = 'inputs'

currentClass = None

class ReturnSignal(Exception):
    def __init__(self, value=None):
        self.value = value

class BrewinClass:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.fields = {}
        self.methods = {}

    def get_name(self):
        return self.name

    def add_field(self, field_name, value):
        self.fields[field_name] = value

    def change_field(self, field_name, value):
        self.fields[field_name] = value

    def add_method(self, method_name, method):
        self.methods[method_name] = method
        
    def get_field(self, field_name):
        field = self.fields.get(field_name)
        if field is None and self.parent:
            return self.parent.get_field(field_name)
        return field

    def get_method(self, method_name):
        method = self.methods.get(method_name)
        if method is None and self.parent:
            return self.parent.get_method(method_name)
        return method

    def get_all_fields(self):
        fields = self.fields.copy()
        if self.parent:
            fields.update(self.parent.get_all_fields())
        return fields

    def get_all_methods(self):
        methods = self.methods.copy()
        if self.parent:
            methods.update(self.parent.get_all_methods())
        return methods

    def execute_method(self, method_name, *args):
        method = self.get_method(method_name)
        return method.execute(*args)


class BrewinMethod:
    def __init__(self, name, params, return_type, body, interpreter, parent_class):
        self.name = name
        self.params = params
        self.return_type = return_type[0] if return_type else None
        self.body = body
        self.interpreter = interpreter
        self.parent_class = parent_class
    
    def get_params(self):
        return self.params

    def execute(self, *args):
        if len(args) != len(self.params):
            raise RuntimeError(f"Invalid number of arguments for method {self.name}")

        local_scope = dict(zip(self.params, args))
        

        result = self.interpreter.interpret_body(self.body, local_scope)


        python_return_type = BREWIN_TYPE_MAP.get(self.return_type)
        if python_return_type is not None and not isinstance(result, python_return_type):
            raise RuntimeError(f"Return type mismatch in method {self.name}: expected {self.return_type}, got {type(result)}")

        return result

class Interpreter(InterpreterBase):

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output=console_output, inp=inp)
        self.trace_output = trace_output
        self.classes = {}

    def run(self, program):
        global currentClass
        success, parsed_program = b.BParser.parse(program)
        if not success:
            super().error(ErrorType.NAME_ERROR, "Parsing failed")
        try:
            self._create_definitions(parsed_program)
        except not super().ErrorType.TYPE_ERROR:
            super().error(ErrorType.NAME_ERROR, "Error creating definitions from the parsed program")
        
        main_class = self.classes.get(MAIN_DEF)
        if not main_class:
            super().error(ErrorType.TYPE_ERROR, "Main class 'main' not found")
        main_method = main_class.get_method(MAIN_DEF)
        if not main_method:
            super().error(ErrorType.TYPE_ERROR, "Main method 'main' not found in main class")
        currentClass = main_class
        result = main_class.execute_method(MAIN_DEF)

        return result
    
    def interpret_body(self, body, local_scope):
        result = None
        for node in body:
            node_type = node[0]
            if node_type == PRINT_DEF:
                values = [self.evaluate_expression(arg, local_scope) for arg in node[1:]]
                output = "".join(str(value).lower() if isinstance(value, bool) else str(value) for value in values)
                if output != 'None':
                    if self.console_output:
                        super().output(output)
                    else:
                        super().output(output)

            elif node_type == INPUTI_DEF:
                var_name = node[1]
                user_input = self.get_input()
                if node_type == INPUTI_DEF:
                    user_input = int(user_input)
                local_scope[var_name] = user_input
            
            elif node_type == INPUTS_DEF:
                var_name = node[1]
                user_input = self.get_input()
                if node_type == INPUTS_DEF:
                    user_input = str(user_input)
                local_scope[var_name] = user_input

            elif node_type == SET_DEF:
                var_name = node[1]
                value = self.evaluate_expression(node[2], local_scope)
                local_scope[var_name] = value
                if var_name in currentClass.get_all_fields():
                        currentClass.change_field(var_name, value)
                        

            elif node_type == BEGIN_DEF:
                result = self.interpret_body(node[1:], local_scope)

            elif node_type == CALL_DEF:
                callee = node[1]
                method_name = node[2]
                method_args = [self.evaluate_expression(arg, local_scope) for arg in node[3:]]
                result = self._call_method(callee, local_scope, method_name, method_args)

            elif node_type == WHILE_DEF:
                condition = node[1]
                if not isinstance(self.evaluate_expression(condition, local_scope), bool):
                    super().error(ErrorType.TYPE_ERROR)
                while_body = node[2]
                while self.evaluate_expression(condition, local_scope):
                    try:
                        self.interpret_body(while_body[1:], local_scope)
                    except ReturnSignal as signal:
                        if signal.value is not None:
                            return signal.value
                        break
            elif node_type == IF_DEF:
                condition = node[1]
                evaluated_condition = self.evaluate_expression(condition, local_scope)

                if not isinstance(evaluated_condition, bool):
                    super().error(ErrorType.TYPE_ERROR)
                true_body = node[2]
                false_body = node[3] if len(node) > 3 else None

                if evaluated_condition:
                    if(true_body[0] == PRINT_DEF or true_body[0] == INPUTI_DEF or true_body[0] == RETURN_DEF or true_body[0] == WHILE_DEF or true_body[0] == SET_DEF or true_body[0] == CALL_DEF or true_body[0] == BEGIN_DEF):
                        true_body = [true_body]
                        result = self.interpret_body(true_body, local_scope)
                    else:
                        result = self.interpret_body(true_body[1:], local_scope)
                elif false_body:
                    if(false_body[0] == PRINT_DEF or false_body[0] == INPUTI_DEF or false_body[0] == RETURN_DEF or false_body[0] == WHILE_DEF or false_body[0] == SET_DEF or false_body[0] == CALL_DEF or false_body[0] == BEGIN_DEF):
                        false_body = [false_body]
                        result = self.interpret_body(false_body, local_scope)
                    else:
                        result = self.interpret_body(false_body[1:], local_scope)

            elif node_type == RETURN_DEF:
                if(len(node) > 1):
                    return self.evaluate_expression(node[1], local_scope)
                else:
                    raise ReturnSignal()
                break

        return result

    def _call_method(self, callee, local_scope, method_name, method_args):
        global currentClass
        oldClass = currentClass
        try:
            if callee == "me":
                try:
                    result = currentClass.execute_method(method_name, *method_args)
                except AttributeError:
                    super().error(ErrorType.NAME_ERROR, f"Undefined method '{method_name}'")
                except RuntimeError:
                    super().error(ErrorType.TYPE_ERROR)
            else:
                        

                if callee in local_scope:
                    newClass = local_scope[callee]

                elif callee in self.classes:
                    newClass = self.classes[callee]
                else:
                    newClass = currentClass.get_field(callee)
                    if newClass is None:
                        super().error(ErrorType.TYPE_ERROR)
                    currentClass = newClass
                try:
                    result = newClass.execute_method(method_name, *method_args)
                except AttributeError:
                    super().error(ErrorType.NAME_ERROR, f"Undefined method '{method_name}' for object '{callee}'")
        except ReturnSignal as signal:
            if signal.value is not None:
                return signal.value
            else:
                super().error(ErrorType.FAULT_ERROR, "Call made to an object reference of null")

        currentClass = oldClass
        return result

    def evaluate_expression(self, expression, local_scope):
        global currentClass
        if isinstance(expression, str):
            if expression in local_scope:
                return local_scope[expression]
            elif expression in currentClass.fields:
                return currentClass.fields[expression]
            elif expression.startswith('"') and expression.endswith('"'):
                return expression[1:-1]
            elif expression == NULL_DEF:
                return None
            else:
                try:
                    return int(expression)
                except ValueError:
                    try:
                        return int(expression)
                    except ValueError:
                        if expression.lower() == "true":
                            return True
                        elif expression.lower() == "false":
                            return False
                        else:
                            super().error(ErrorType.NAME_ERROR, f"Undefined class name, field, or parameter: '{expression}'")
        elif isinstance(expression, list):
            
            expression_type = expression[0]
            if expression_type == VARIABLE_DEF:
                return local_scope[expression[1]]
            elif expression_type == NEW_DEF:
                class_name = expression[1]
                if class_name in self.classes:
                    original_class = self.classes[class_name]
                    newInstance = BrewinClass(class_name, original_class.parent)
                    newInstance.fields = original_class.fields.copy()
                    newInstance.methods = original_class.methods.copy()
                    return newInstance
                else:
                    super().error(ErrorType.TYPE_ERROR)
            elif expression_type == CALL_DEF:
                callee = expression[1]
                method_name = expression[2]
                args = [self.evaluate_expression(arg, local_scope) for arg in expression[3:]]
                result = None
                result = self._call_method( callee, local_scope, method_name, args)
                return result
            elif expression_type in ['+', '-', '*', '/', '>', '<', '==', '!=', '>=', '<=', '%', '&', '|']:
                left = self.evaluate_expression(expression[1], local_scope)
                right = self.evaluate_expression(expression[2], local_scope)
                if (isinstance(left, str) and not isinstance(right, str)) or (isinstance(right, str) and not isinstance(left, str)):
                    super().error(ErrorType.TYPE_ERROR)
                elif(isinstance(left,bool) and not isinstance(right, bool)) or (isinstance(right, bool) and not isinstance(left, bool)):
                    super().error(ErrorType.TYPE_ERROR)
                if(expression_type == '/'):
                    expression_type = '//'
                if(isinstance(left, bool) and isinstance(right, bool) and (expression_type in ['+', '-', '*', '/', '%', '>', '<', '>=', '<='])):
                    super().error(ErrorType.TYPE_ERROR)
                try:
                    return eval(f'{left} {expression_type} {right}')
                except:
                    super().error(ErrorType.TYPE_ERROR)
            elif expression_type in ['!']:
                operand = self.evaluate_expression(expression[1], local_scope)
                if isinstance(operand, bool):
                    return not operand
                else:
                    super().error(ErrorType.TYPE_ERROR)

            else:
                super().error(ErrorType.NAME_ERROR)
        else:
            super().error(ErrorType.NAME_ERROR)

    def _create_definitions(self, parsed_program):
        for line_nodes in parsed_program:
          self._process_line_nodes(line_nodes)

    def _process_line_nodes(self, line_nodes):
        if not line_nodes:
            return

        node_type = line_nodes[0]

        if node_type == CLASS_DEF:
            class_name = line_nodes[1]
            if class_name in self.classes:
                super().error(ErrorType.TYPE_ERROR)
            parent = None
            if len(line_nodes) > 2 and not isinstance(line_nodes[2], list):
                parent_class_name = line_nodes[2]
                parent = self.classes.get(parent_class_name)
                members_start_index = 3
            else:
                members_start_index = 2
            
            brewin_class = BrewinClass(class_name, parent)
            self.classes[class_name] = brewin_class

            if len(line_nodes) > members_start_index:
                for member_node in line_nodes[members_start_index:]:
                    self._process_line_nodes(member_node)

        elif node_type == FIELD_DEF:
            current_class = list(self.classes.values())[-1]
            field_name = line_nodes[1]
            if field_name in current_class.get_all_fields():
                super().error(ErrorType.NAME_ERROR)
            field_value = line_nodes[2]
            current_class = list(self.classes.values())[-1]

            if field_value.isdigit():
                field_value = int(field_value)
            elif field_value.lower() == 'true':
                field_value = True
            elif field_value.lower() == 'false':
                field_value = False
            elif field_value == 'None' or field_value == NULL_DEF:
                field_value = None
            elif field_value.startswith('"') and field_value.endswith('"'):
                field_value = field_value[1:-1]  
            else:
                super().error(ErrorType.TYPE_ERROR)
            current_class.add_field(field_name, field_value)

        elif node_type == METHOD_DEF:
            if(self.classes is not {}):
                current_class = list(self.classes.values())[-1]
            else:
                raise 
            method_name = line_nodes[1]
            if method_name in current_class.get_all_methods():
                super().error(ErrorType.NAME_ERROR)
            params = line_nodes[2]
            body = line_nodes[3:]
            method = BrewinMethod(method_name, params, None, body, self, current_class)
            current_class.add_method(method_name, method)

        elif node_type in (BEGIN_DEF, WHILE_DEF, RETURN_DEF):
            for nested_node in line_nodes[1:]:
                if isinstance(nested_node, list):
                    self._process_line_nodes(nested_node)

        else:
            raise NotImplementedError(f"Node type {node_type} not implemented")

if __name__ == "__main__":
    stringProgram = """
    (class main
        (method main ()
        (if(== "dog" "dog")
        (print "oh yea")
        )
        )
        )


        """

    sample_program = []
    for line in stringProgram.splitlines():
        sample_program.append(line.strip())

    sample_program = [line for line in sample_program if line]


    interpreter = Interpreter()
    interpreter.run(sample_program)
