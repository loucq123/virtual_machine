import operator


class Register():

    def __init__(self, value=None):
        self.regValue = value

    def get_reg_value(self):
        return self.regValue

    def set_reg_value(self, new_value):
        self.regValue = new_value


class Node():

    def __init__(self, value=None, next_node=None):
        self.value = value
        self.next = next_node

    def get_node_value(self):
        return self.value

    def set_next_node(self, next_node):
        self.next = next_node

    def get_next_node(self):
        return self.next


class Stack():

    def __init__(self):
        self.top = None

    def empty(self):
        return self.top is None

    def pop(self):
        if self.empty():
            raise Exception("pop an empty stack")
        pop_value = self.top.get_node_value()
        self.top = self.top.get_next_node()
        return pop_value

    def push(self, value):
        new_node = Node(value)
        new_node.set_next_node(self.top)
        self.top = new_node


class Machine():

    def __init__(self):
        self.pc = None
        self.flag = Register()
        self.stack = Stack()
        self.inst_sequence = None
        self.register_table = {}
        self.ops = {}

    def make_machine(self, regs, ops, controller):
        for reg in regs:
            self.allocate_register(reg)
        for op in ops:
            self.ops[op[0]] = op[1]
        assembler = Assembler(self)
        assembler.extract_labels(controller)

    def start(self):
        self.pc = self.inst_sequence
        # print(machine.pc[0]())
        # print(machine.get_register('n').get_reg_value())
        self.execute()

    def run_pc_inst(self):
        self.pc[0]()

    def update_pc(self):
        self.pc = self.pc[1:]

    def execute(self):
        while self.pc is not None and len(self.pc) > 0:
            self.run_pc_inst()
            # self.update_pc()

    def allocate_register(self, reg_name):
        if reg_name in self.register_table.keys():
            raise Exception("Multiple register")

        self.register_table[reg_name] = Register()

    def get_register(self, reg_name):
        return self.register_table[reg_name]

    def get_stack(self):
        return self.stack

    def get_ops(self):
        return self.ops

    def get_pc(self):
        return self.pc

    def get_flag(self):
        return self.flag


class Assembler():

    def __init__(self, machine):
        self.machine = machine
        self.labels = {}
        self.insts = []
        self.extract_machine_info()

    def extract_machine_info(self):
        self.pc = self.machine.get_pc()
        self.flag = self.machine.get_flag()
        self.stack = self.machine.get_stack()
        self.ops = self.machine.get_ops()

    def extract_labels(self, ast):
        label_number = 0
        while label_number < len(ast):
            label_statement = ast[label_number]
            label_name = label_statement[0]
            if len(label_statement) == 1:
                self.labels[label_name] = []
                label_number += 1
                continue
            label_insts = label_statement[1]
            for inst in label_insts:
                inst_procedure = self.make_inst_procedure(inst)
                if label_name not in self.labels.keys():
                    self.labels[label_name] = [inst_procedure]
                else:
                    self.labels[label_name].append(inst_procedure)
                self.insts.append(inst_procedure)
            label_number += 1
        self.machine.inst_sequence = self.insts

    def make_inst_procedure(self, inst):
        exp_type = inst[0]
        if exp_type == 'assign':
            return self.make_assign_procedure(inst[1:])
        elif exp_type == 'test':
            return self.make_test_procedure(inst[1:])
        elif exp_type == 'branch':
            return self.make_branch_procedure(inst[1:])
        elif exp_type == 'goto':
            return self.make_goto_procedure(inst[1:])
        elif exp_type == 'restore':
            return self.make_restore_procedure(inst[1:])
        elif exp_type == 'save':
            return self.make_save_procedure(inst[1:])
        else:
            raise Exception("Unknown instruction")

    @staticmethod
    def operation_part(op):
        return op[1]

    def make_operation_exp(self, exp):
        op_name = self.operation_part(exp[0])
        op_procedure = self.ops[op_name]
        params = []
        for p in exp[1:]:
            value = None
            if p[0] == 'reg':
                value = self.machine.get_register(p[1]).get_reg_value()
            elif p[0] == 'const':
                value = p[1]
            params.append(value)
        return op_procedure(*params)

    def make_primitive_exp(self, exp):
        value = None
        if exp[0] == 'reg':
            value = self.machine.get_register(exp[1]).get_reg_value()
        elif exp[0] == 'const':
            value = exp[1]
        elif exp[0] == 'label':
            value = self.labels[exp[1]]
        return value

    def make_assign_procedure(self, inst):
        reg_name = inst[0]
        exp = inst[1]

        def proc():
            self.machine.update_pc()
            if type(exp[0]) != str:
                return self.make_operation_exp(exp)
            else:
                return self.make_primitive_exp(exp)
        return lambda: self.machine.get_register(reg_name).set_reg_value(proc())

    def make_test_procedure(self, inst):

        def proc():
            self.machine.update_pc()
            return self.make_operation_exp(inst[0])
        return lambda: self.flag.set_reg_value(proc())

    def make_branch_procedure(self, inst):

        def proc():
            if self.flag.get_reg_value():
                self.machine.pc = self.make_primitive_exp(inst)
            else:
                self.machine.update_pc()
        return lambda: proc()

    def make_goto_procedure(self, inst):

        def proc():
            self.machine.pc = self.make_primitive_exp(inst)
        return lambda: proc()

    def make_save_procedure(self, inst):

        def proc():
            self.machine.update_pc()
            reg_name = inst[0]
            value = self.machine.get_register(reg_name).get_reg_value()
            self.stack.push(value)
        return lambda: proc()

    def make_restore_procedure(self, inst):

        def proc():
            self.machine.update_pc()
            reg_name = inst[0]
            value = self.stack.pop()
            self.machine.get_register(reg_name).set_reg_value(value)
        return lambda: proc()


class Test():

    def test_creation(self):
        self.test_stack()
        self.test_assign()
        self.test_branch()
        self.test_goto()
        self.test_recursion()

    @staticmethod
    def test_stack():
        s = Stack()
        assert s.empty()
        s.push(1)
        assert not s.empty()
        assert s.pop() == 1
        assert s.empty()
        s.push(2)
        s.push(3)
        assert s.pop() == 3
        assert s.pop() == 2
        assert s.empty()

    @staticmethod
    def test_assign():

        controllers = [[['controller', [['assign', 'n', ['reg', 'a']]]]],
                       [['controller', [['assign', 'n', ['const', 1]]]]]]
        ans = [2, 1]
        for i in range(len(controllers)):
            assign_machine = Machine()
            assign_machine.make_machine(['n', 'a'], [], controllers[i])
            assign_machine.get_register('a').set_reg_value(2)
            assign_machine.start()
            assert assign_machine.get_register('n').get_reg_value() == ans[i]

        controller = [['controller', [['assign', 'n', [['op', '+'], ['reg', 'a'], ['const', 2]]]]]]
        assign_machine = Machine()
        assign_machine.make_machine(['n', 'a'], [['+', operator.add]], controller)
        assign_machine.get_register('a').set_reg_value(2)
        assign_machine.start()
        assert assign_machine.get_register('n').get_reg_value() == 4

        controller = [['controller', [['assign', 'n', ['const', 1]],
                                      ['assign', 'b', ['reg', 'n']]]]]
        assign_machine = Machine()
        assign_machine.make_machine(['n', 'b'], [], controller)
        assign_machine.start()
        assert assign_machine.get_register('b').get_reg_value() == 1

    @staticmethod
    def test_branch():

        controller = [['controller', [['assign', 'sum', ['const', 1]]]],
                      ['if-loop', [['test', [['op', '=='], ['reg', 'a'], ['reg', 'b']]],
                                   ['branch', 'label', 'done'],
                                   ['assign', 'sum', [['op', '+'], ['reg', 'sum'], ['reg', 'a']]],
                                   ['assign', 'a', [['op', '+'], ['reg', 'a'], ['const', 1]]]]],
                      ['done']]
        test_machine = Machine()
        test_machine.make_machine(['sum', 'a', 'b'], [['+', operator.add], ['==', operator.eq]], controller)
        test_machine.get_register('a').set_reg_value(2)
        test_machine.get_register('b').set_reg_value(5)
        test_machine.start()
        assert test_machine.get_register('sum').get_reg_value() == 3
        assert test_machine.get_register('a').get_reg_value() == 3

    @staticmethod
    def test_goto():
        controller = [['controller', [['assign', 'sum', ['const', 0]]]],
                      ['if-loop', [['test', [['op', '=='], ['reg', 'a'], ['reg', 'b']]],
                                   ['branch', 'label', 'done'],
                                   ['assign', 'sum', [['op', '+'], ['reg', 'sum'], ['reg', 'a']]],
                                   ['assign', 'a', [['op', '+'], ['reg', 'a'], ['const', 1]]],
                                   ['goto', 'label', 'if-loop']]],
                      ['done']]
        test_machine = Machine()
        test_machine.make_machine(['sum', 'a', 'b'], [['+', operator.add], ['==', operator.eq]], controller)
        test_machine.get_register('a').set_reg_value(2)
        test_machine.get_register('b').set_reg_value(5)
        test_machine.start()
        assert test_machine.get_register('sum').get_reg_value() == 9
        assert test_machine.get_register('a').get_reg_value() == 5

    @staticmethod
    def test_recursion():
        controller = [['controller', [['assign', 'continue', ['label', 'fact-done']]]],
                      ['fact-loop', [['test', [['op', '=='], ['reg', 'n'], ['const', 1]]],
                                     ['branch', 'label', 'base-case'],
                                     ['save', 'continue'],
                                     ['save', 'n'],
                                     ['assign', 'n', [['op', '-'], ['reg', 'n'], ['const', 1]]],
                                     ['assign', 'continue', ['label', 'after-fact']],
                                     ['goto', 'label', 'fact-loop']]],
                      ['after-fact', [['restore', 'n'],
                                      ['restore', 'continue'],
                                      ['assign', 'val', [['op', '*'], ['reg', 'n'], ['reg', 'val']]],
                                      ['goto', 'reg', 'continue']]],
                      ['base-case', [['assign', 'val', ['const', 1]],
                                     ['goto', 'reg', 'continue']]],
                      ['fact-done']]
        test_machine = Machine()
        ops = [['==', operator.eq], ['-', operator.sub], ['*', operator.mul]]
        test_machine.make_machine(['continue', 'n', 'val'], ops, controller)
        test_machine.get_register('n').set_reg_value(4)
        test_machine.start()
        assert test_machine.get_register('val').get_reg_value() == 24


if __name__ == '__main__':
    test = Test()
    test.test_creation()
