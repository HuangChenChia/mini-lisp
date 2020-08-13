"""Thanks to Mary Rose Cook & Peter Norvig,
   Credit to djosix"""

# !/usr/bin/env python3

# Debugging functions
debugging = False


def debug(*args, **kwargs):
    if debugging:
        print(f'{" ".join(map(str, args))}', **kwargs)


def success(*args, **kwargs):
    print(f'{" ".join(map(str, args))}', **kwargs)


def warning(*args, **kwargs):
    print(f'{" ".join(map(str, args))}', **kwargs)


def parse(code):
    tokens = code.replace('(', ' ( ').replace(')', ' ) ').split()
    List = []
    for token in tokens:
        if token not in ['(', ')']:
            List.append(f'"{token}"')
        else:
            List.append(token)
        if token != '(':
            List.append(',')
    return eval(''.join(['(', *List, ')']))


def is_id(s):
    # [a-z][a-z0-9\-]*
    c, *rest = s
    if not c.islower():
        return False
    for c in rest:
        if not (c.islower() or c.isdigit() or c == '-'):
            return False
    return True


class Function:
    def __init__(self, name='anonymous', func=None, arg_type=None, arg_num=''):
        self.name = name
        self.func = func
        self.arg_type = arg_type
        self.arg_num = arg_num
        self.locked = False

    def __call__(self, *args):
        self._check_args(args)
        return self.func(*args)
    
    def _check_args(self, args):
        arg_num = len(args)
        assert eval(f'{arg_num} {self.arg_num}'), f'expect number of arguments {self.arg_num} but got {arg_num}'
        if self.arg_type is not None:
            if self.arg_type == 'same':
                arg_type = type(args[0])
            else:
                arg_type = self.arg_type
            for i, arg in enumerate(args):
                if type(arg) != arg_type:
                    n = i + 1
                    t1 = getattr(arg_type, '__name__', arg_type).lower()
                    t2 = getattr(type(arg), '__name__', type(arg)).lower()
                    assert False, f'expect argument {n} with type {t1} but got {t2}'

    def __str__(self):
        info = ''
        if self.arg_num is not None:
            arg_num = self.arg_num.replace('== ', '')
            info += ' ({} args)'.format(arg_num)
        if self.arg_type is not None:
            arg_type = getattr(self.arg_type, '__name__', str(self.arg_type))
            info += ' (type {})'.format(arg_type)
        return f'<function "{self.name}"{info}>'
    
    def __repr__(self):
        return str(self)


def evaluate(statement, scope):
    if isinstance(statement, tuple):
        debug('statement:', str(statement).replace(',', '').replace('\'', ''))
        debug('variables:', ' '.join(f'{name}={value}' for name, value in scope.items() if not callable(value)))
        debug('functions:', ' '.join(name for name, value in scope.items() if callable(value)))

        assert len(statement), 'missing function'
        primary = statement[0]
        
        if primary == 'define':
            # Define a variable in scope
            _, name, value = statement
            assert is_id(name), f'invalid id: {name}'
            if type(value) is tuple:
                temp_scope = scope.copy()
                temp_scope[name] = Function(name)
                temp_scope[name].locked = True
                temp = evaluate(value, temp_scope)
                if callable(temp) and temp != temp_scope[name]:
                    temp_scope[name].locked = False
                    temp_scope[name].func = temp.func
                    temp_scope[name].arg_num = temp.arg_num
                    scope[name] = temp_scope[name]
                    return
            scope[name] = evaluate(value, scope)
            return

        if primary == 'fun':
            # Return a function instance
            _, arg_names, *defines, exp = statement
            arg_num = len(arg_names)
            static_scope = scope.copy()  # copy scope for static variables
            for define in defines:
                # Define static local variables in copied scope
                evaluate(define, static_scope)

            def _func(*args):
                # Copy static scope to add args in it
                func_scope = static_scope.copy()
                for arg_name, arg in zip(arg_names, args):
                    func_scope[arg_name] = evaluate(arg, scope)
                return evaluate(exp, func_scope)
            return Function(func=_func, arg_num=f'== {arg_num}')

        if primary == 'if':
            _, cond, true, false = statement
            if evaluate(cond, scope):
                return evaluate(true, scope)
            else:
                return evaluate(false, scope)

        if isinstance(primary, tuple):
            # Evaluate the primary to see if it's a function
            primary = evaluate(primary, scope)
            assert type(primary) == Function, f'expect a function but got {type(primary).__name__}'
            statement = (primary, *statement[1:])
            return evaluate(statement, scope)

        func = None

        if isinstance(primary, Function):
            func, *args = statement
        
        elif type(primary) is str and primary in scope:
            func_name, *args = statement
            func = scope[func_name]
        
        if func is not None:
            assert callable(func), f'{func} is not callable'
            args = [evaluate(arg, scope) for arg in args]
            debug('call:', func.name, args)
            assert not func.locked, f'calling an incomplete function: {func.name}'
            value = func(*args)
            debug('return:', value)
            return value

        assert not is_id(primary), f'undefined function: {primary}'
        assert False, f'invalid function name: {primary}'

    else:
        # Evaluate an argument

        if callable(statement):
            return statement

        try:
            return int(statement)
        except:
            pass
        
        try:
            return {'#t': True, '#f': False}[statement]
        except:
            pass
            
        try:
            return scope[statement]
        except:
            pass
        
        assert not is_id(statement), f'undefined variable: {statement}'
        assert False, f'invalid syntax: {statement}'


def init_scope():
    # Initialize a clean variable scope with pre-defined variables

    def _add(*args):
        return sum(args)

    def _mul(*args):
        n = 1
        for i in args:
            n *= i
        return n
    
    def _equ(*args):
        for i in args[1:]:
            if args[0] != i:
                return False
        return True
    
    def _and(*args):
        return all(args)
    
    def _or(*args):
        return any(args)
    
    return {
        '+':          Function('+', _add,                        int, '>= 2'),
        '-':          Function('-', lambda x, y: x - y,          int, '== 2'),
        '*':          Function('*', _mul,                        int, '>= 2'),
        '/':          Function('/', lambda x, y: x // y,         int, '== 2'),
        'mod':        Function('mod', lambda x, y: x % y,        int, '== 2'),
        '=':          Function('=', _equ,                        'same', '>= 2'),
        '>':          Function('>', lambda x, y: x > y,          int, '== 2'),
        '<':          Function('<', lambda x, y: x < y,          int, '== 2'),
        'and':        Function('and', _and,                      bool, '>= 2'),
        'or':         Function('or', _or,                        bool, '>= 2'),
        'not':        Function('not', lambda x: not x,           bool, '== 1'),
        'print-num':  Function('print-num', lambda x: print(x),  int, '== 1'),
        'print-bool': Function('print-bool', lambda x: print({True: '#t', False: '#f'}[x]), bool, '== 1')
    }


def run(code, scope=init_scope(), interactive=False):
    try:
        statements = parse(code)
    except:
        if not (interactive or debugging):
            print('Error:', 'invalid syntax')
        else:
            warning('Error:', 'invalid syntax')
        return
    for statement in statements:
        try:
            retval = evaluate(statement, scope)
            if (debugging or interactive) and retval is not None:
                success('===>', retval)
        except Exception as e:
            if debugging:
                import traceback
                warning(traceback.format_exc())
            elif interactive:
                warning('Error:', str(e) or 'invalid syntax')
            else:
                print('Error:', str(e) or 'invalid syntax')


if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        run(open(sys.argv[1]).read())

    else:
        while True:
            try:
                run(input('> '), interactive=True)
            except:
                break
