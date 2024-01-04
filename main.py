from category import CategoryException
from database import Database, DatabaseException


__author__ = "Daniel Efimenko"
__copyright__ = "Copyright 2024, The DxStock command-line electronic components management tool"
__license__ = "MIT"
__version__ = "0.9.0"


stock_db = Database()
project_db = Database()


def cmd_load_stock_db(args):
    filename = args[0]
    with open(filename, 'r') as f:
        lines = f.readlines()
        stock_db.load_from_csv(lines)
        print('Stock database loaded.')


def cmd_save_stock_db(args):
    filename = args[0]
    with open(filename, 'w') as f:
        text = stock_db.convert_to_csv()
        f.write(text)
        print('Stock database saved.')


def cmd_print_stock_db(args):
    if args:
        print('Stock DB category:')
        print(stock_db.category_to_str(args[0]))
    else:
        print('In stock:\n')
        print(stock_db)


def cmd_clear_stock_db(args):
    stock_db.clear()
    print('Stock database cleared.')


def cmd_load_project_db(args):
    filename = args[0]
    with open(filename, 'r') as f:
        lines = f.readlines()
        project_db.load_from_csv(lines)
        print('Project database loaded.')


def cmd_print_project_db(args):
    if args:
        print('Project DB category:')
        print(project_db.category_to_str(args[0]))
    else:
        print('Project BOM:\n')
        print(project_db)


def cmd_clear_project_db(args):
    project_db.clear()
    print('Project database cleared.')


def cmd_add_category(args):
    cat_name = args[0]
    cat_format_str = args[1]
    stock_db.add_category(cat_name, cat_format_str)


def cmd_print_category_fmt(args):
    cat_name = args[0]
    print(stock_db.get_category_format(cat_name))


def cmd_print_all_variants_of_param(args):
    cat_name = args[0]
    param_str = args[1]
    print(f'All variants of {cat_name}/{param_str} in stock database:')
    print(stock_db.get_all_variants_of_param(cat_name, param_str))
    print(f'All variants of {cat_name}/{param_str} in project database:')
    print(project_db.get_all_variants_of_param(cat_name, param_str))


def cmd_add_component(args):
    cat_name = args[0]
    component_str = args[1]
    stock_db.add_component(cat_name, component_str)


def cmd_subtract_component(args):
    cat_name = args[0]
    component_str = args[1]
    stock_db.subtract_component(cat_name, component_str)


def cmd_filter_components(args):
    cat_name = args[0]
    query = {}
    for pair in args[1:]:
        try:
            k, v = pair.split('=')
        except ValueError as e:
            print('Error: Query must look like KEY0=VAL0 KEY1=VAL1 ...')
        else:
            query[k] = v
    filtered_cat = stock_db.filter_components(cat_name, **query)
    print(filtered_cat)


def cmd_filter_components_from_bound(args):
    cat_name = args[0]
    query = args[1]

    if '>=' in query:
        operation_str = '>='
    elif '<=' in query:
        operation_str = '<='
    else:
        print('Error: Query must look like PARAM>=VALUE or PARAM<=VALUE')
        return
    param_str, bound_str = query.split(operation_str)
    filtered_cat = stock_db.filter_components_from_bound(cat_name, param_str, bound_str, operation_str)
    print(filtered_cat)


def cmd_print_difference(args):
    not_in_stock_db = stock_db.calc_difference(project_db)
    if not_in_stock_db:
        print('Not in stock:')
        print(not_in_stock_db)
    else:
        print('All components are in stock.')


def cmd_subtract_project_from_stock(args):
    stock_db.subtract_other(project_db)
    print('Project BOM database subtracted from stock database.')


def print_help(args):
    print('Available commands:')
    for cmd in COMMANDS:
        help_str = COMMANDS[cmd][1]
        print(f'\t{cmd}\t\t{help_str}')


COMMANDS = {
    'q': ((lambda args: quit(0)), 'Quit'),
    '?': (print_help, 'Print this'),
    'lds':  (cmd_load_stock_db, 'Load stock database from FILE.csv (append)'),
    'ss':   (cmd_save_stock_db, 'Save stock database to FILE.csv'),
    'ps':   (cmd_print_stock_db, 'Print stock database (category NAME or full DB)'),
    'cs':   (cmd_clear_stock_db, 'Clear stock database'),
    'ldp':  (cmd_load_project_db, 'Load project database from FILE.csv (append)'),
    'pp':   (cmd_print_project_db, 'Print project database (category NAME or full DB)'),
    'cp':   (cmd_clear_project_db, 'Clear project database'),
    'add-c':    (cmd_add_category, 'Add category NAME with format FORMAT'),
    'pf':   (cmd_print_category_fmt, 'Print format of category NAME'),
    'add':  (cmd_add_component, 'Add component to category NAME'),
    'sub':  (cmd_subtract_component, 'Subtract component matching PARAMS from category NAME'),
    'sub-p':    (cmd_subtract_project_from_stock, 'Subtract project BOM database from stock database'),
    'f':    (cmd_filter_components, 'Filter components matching QUERY'),
    'fb':   (cmd_filter_components_from_bound, 'Filter components with PARAM >= or <= VALUE'),
    'pd':   (cmd_print_difference, 'Print difference between stock and project databases'),
    'v':    (cmd_print_all_variants_of_param, 'Print all variants of parameter PARAM in category NAME')
}

if __name__ == '__main__':
    print(__copyright__)
    print(f'by {__author__}')
    print(f'Version: {__version__}')

    while True:
        command = input('> ').strip()
        args = []
        if ' ' in command:
            words = command.split(' ')
            command, args = words[0], words[1:]

        if not command:
            continue
        if command not in COMMANDS:
            print(f'Error: No such command {command}')
            continue

        callback = COMMANDS[command][0]
        try:
            callback(args)
        except (CategoryException, DatabaseException) as e:
            print(e)
        except FileNotFoundError as e:
            print(e)
        except IndexError as e:
            print(f'{e} => Maybe not enough arguments?')
