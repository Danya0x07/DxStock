import os, sys
from thirdparty import kicad_netlist_reader
from database import Database


PATH_TO_DB = os.path.dirname(os.path.realpath(__file__))


def is_known_parameter(param_str, value_str):
    known = {
        'Tolerance': '%',
        'Voltage': 'V',
        'Current': 'A',
        'Wattage': 'W'
    }
    return param_str in known and value_str[-1] == known[param_str]


net = kicad_netlist_reader.netlist(sys.argv[1])
components = net.getInterestingComponents(excludeBOM=True)

stock_db = Database()
project_db = Database()

with open(f'{PATH_TO_DB}/{sys.argv[3]}', 'r') as f:
    lines = f.readlines()
    stock_db.load_from_csv(lines)

known_packages = []
for catn in stock_db.categories:
    variants = stock_db.get_all_variants_of_param(catn, 'Package')
    known_packages.extend(variants)
known_packages = set(known_packages)

unnecessary_components = []

for c in components:
    ref = c.getRef()  # To find out category
    raw_value = c.getValue()  # To find out category-specific parameters
    footprint = c.getFootprint()  # To find out the package

    unnecessary = raw_value.endswith('*')
    if unnecessary:
        raw_value = raw_value[:-1]

    cat_name = 'Unknown'

    if ref.startswith('R') and ref[1].isdigit():
        cat_name = 'Resistors'
    elif ref.startswith('C') and ref[1].isdigit():
        cat_name = 'Capacitors'
    elif ref.startswith('L') and ref[1].isdigit():
        cat_name = 'Inductors'
    elif ref.startswith('FB') and ref[2].isdigit():
        cat_name = 'FerriteBeads'
    else:
        for catn in stock_db.categories:
            if stock_db.category_has_param(catn, 'Name'):
                variants = stock_db.get_all_variants_of_param(catn, 'Name')
            elif stock_db.category_has_param(catn, 'Value'):
                variants = stock_db.get_all_variants_of_param(catn, 'Value')
            else:
                continue
            if raw_value in variants:
                cat_name = catn
                break

    package = '?'
    for p in known_packages:
        if p in footprint:
            package = p

    if '/' in raw_value:
        raw_value = raw_value.split('/')
    else:
        raw_value = [raw_value]

    if ',' in raw_value[0]:
        value, tolerance = raw_value[0].split(',')
        raw_value[0] = value
        raw_value.append(tolerance)

    value = raw_value[0]
    params = {}
    if cat_name in stock_db.categories:
        cat_format = stock_db.get_category_format(cat_name)
        for i in range(1, len(cat_format) - 2):  # Skipping value (or name), package and quantity
            variants = stock_db.get_all_variants_of_param(cat_name, cat_format[i])
            params[cat_format[i]] = '?'
            for j in range(1, len(raw_value)):
                if raw_value[j] in variants or is_known_parameter(cat_format[i], raw_value[j]):
                    params[cat_format[i]] = raw_value[j]
                    break
        paramlist = [params[cat_format[i]] for i in range(1, len(cat_format) - 2)]
        param_str = ','.join(paramlist)
        component_str = f"{value},{param_str},{package},1"

        # Trying to determine as many params as possible
        if '?' in component_str:
            component = component_str.split(',')
            query = {cat_format[i]: component[i] for i in range(len(cat_format) - 1) if component[i] != '?'}
            filtered_cat = stock_db.filter_components(cat_name, **query)
            for i in range(1, len(component) - 2):
                if component[i] == '?':
                    redefined = '?'
                    for fc in filtered_cat.components:
                        if redefined == '?' or redefined == fc[i]:
                            redefined = fc[i]
                        else:
                            redefined = '!'
                            break
                    component[i] = redefined
            component_str = ','.join(component)
    else:
        param_str = '|'.join(raw_value[1:])
        component_str = f"{value},{param_str},{package},1"

    if cat_name not in project_db.categories:
        cat_format_str = 'Value,Extra,Package,Qty'
        if cat_name in stock_db.categories:
            cat_format_str = ','.join(stock_db.get_category_format(cat_name))
        project_db.add_category(cat_name, cat_format_str)

    if unnecessary:
        unnecessary_components.append((cat_name, component_str))
    else:
        project_db.add_component(cat_name, component_str)

with open(f'{sys.argv[2]}.csv', 'w') as f:
    text = project_db.convert_to_csv()
    f.write(text)

for uc in unnecessary_components:
    cat_name, component_str = uc
    if cat_name not in project_db.categories:
        project_db.add_category(cat_name, 'Value,Extra,Package,Qty')
    project_db.add_component(cat_name, component_str)

with open(f'{sys.argv[2]}_full.csv', 'w') as f:
    text = project_db.convert_to_csv()
    f.write(text)
