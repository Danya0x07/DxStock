from category import ComponentCategory


class DatabaseException(Exception):
    pass


class Database:

    def __init__(self):
        self.categories = {}

    def _check_catname(self, cat_name):
        cat_name = cat_name.strip()
        if cat_name not in self.categories:
            raise DatabaseException(f'Category {cat_name} does not exist')
        return cat_name

    def add_category(self, cat_name, cat_format_str):
        cat_name = cat_name.strip()
        if cat_name in self.categories:
            raise DatabaseException(f'Category {cat_name} already exists')
        self.categories[cat_name] = ComponentCategory(cat_name, cat_format_str)

    def add_component(self, cat_name, component_str):
        cat_name = self._check_catname(cat_name)
        self.categories[cat_name].add(component_str)

    def subtract_component(self, cat_name, component_str):
        cat_name = self._check_catname(cat_name)
        self.categories[cat_name].subtract(component_str)

    def filter_components(self, cat_name, **kwargs):
        cat_name = self._check_catname(cat_name)
        return self.categories[cat_name].filter(**kwargs)

    def filter_components_from_bound(self, cat_name, param_str, bound_str, operation_str):
        cat_name = self._check_catname(cat_name)
        return self.categories[cat_name].filter_from_bound(param_str, bound_str, operation_str)

    def calc_difference(self, other):
        ns_db = Database()
        for o_cat_name in other.categories:
            o_cat = other.categories[o_cat_name]
            if o_cat_name in self.categories:
                cat = self.categories[o_cat_name]
                ns_components = cat.calc_difference(o_cat).components
                if ns_components:
                    ns_db.add_category(o_cat.name, o_cat.format_str)
                    for ns_component in ns_components:
                        ns_db.add_component(o_cat.name, ','.join(map(str, ns_component)))
            else:
                ns_db.add_category(o_cat.name, o_cat.format_str)
                for ns_component in o_cat.components:
                    ns_db.add_component(o_cat.name, ','.join(map(str, ns_component)))
        return ns_db

    def subtract_other(self, other):
        if self.calc_difference(other):
            raise DatabaseException(f'Cannot subtract components of other DB from self')
        for o_cat_name in other.categories:
            for o_component in other.categories[o_cat_name].components:
                self.categories[o_cat_name].subtract(','.join(map(str, o_component)))

    def __str__(self):
        return '\n\n'.join(str(self.categories[c]) for c in self.categories)

    def category_to_str(self, cat_name):
        cat_name = self._check_catname(cat_name)
        return str(self.categories[cat_name])

    def convert_to_csv(self):
        return '\n'.join(self.categories[cat].convert_to_csv() for cat in self.categories)

    def load_from_csv(self, lines):
        cat_name = 'NoName'
        new_cat = False
        for line in lines:
            if line[-1] == '\n':
                line = line[:-1]
            elif line[-2:] == '\r\n':
                line = line[:-2]

            if new_cat:
                new_cat = False
                format_str = line
                if cat_name not in self.categories:
                    self.add_category(cat_name, format_str)
                continue

            if ',' not in line:
                cat_name = line
                new_cat = True
                continue

            self.add_component(cat_name, line)

    def clear(self):
        self.categories.clear()

    def __bool__(self):
        return bool(self.categories)
