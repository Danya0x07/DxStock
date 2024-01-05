from collections import deque
from tabulate import tabulate


class CategoryException(Exception):
    pass


class ComponentCategory:
    _MULTIPLIERS = {
        # for resistance
        'k': 1000,
        'M': 1000000,
        'G': 1000000000,
        # for capacitance and inductance
        'p': 1,
        'n': 1000,
        'u': 1000000,
        'm': 1000000000,
        # for other
        'V': 1,
        'A': 1,
        'W': 1,
        '%': 1
    }

    def __init__(self, name: str, format_str: str, components=None):
        self.name = name
        self.format_str = format_str.strip()
        self.format = format_str.split(',')
        self.components = deque()
        if components is not None:
            self.components.extend(components)

    def _str_to_component(self, component_str):
        component_str = component_str.strip()
        component = component_str.split(',')
        component[-1] = int(component[-1])  # Quantity is always integer

        if len(component) != len(self.format):
            raise CategoryException(f'Incorrect format: {component_str}, expected: {self.format}')
        return component

    def find(self, component):
        for existing_component in self.components:
            for i in range(len(existing_component) - 1):
                if component[i] != existing_component[i]:
                    break
            else:  # Entry match
                return existing_component
        else:
            return None

    @staticmethod
    def _convert_value_to_abs(value_str: str) -> float:
        units = value_str[-1]
        if units.isdigit():
            return float(value_str)
        if units not in ComponentCategory._MULTIPLIERS:
            raise CategoryException(f'No such units: {units}')
        value = float(value_str[:-1]) * ComponentCategory._MULTIPLIERS[units]
        return value

    def add(self, component_str: str):
        """Append a new component entry or add to existing one."""
        new_component = self._str_to_component(component_str)
        existing_component = self.find(new_component)

        if existing_component is None:
            self.components.append(new_component)
        else:
            quantity = new_component[-1]
            existing_component[-1] += quantity

    def subtract(self, component_str: str):
        """Subtract component quantity from existing entry.
        If 0 such components left after, entry is removed.
        """
        component = self._str_to_component(component_str)
        existing_component = self.find(component)

        if existing_component is not None:
            quantity = component[-1]
            if quantity <= existing_component[-1]:
                existing_component[-1] -= quantity
                if existing_component[-1] == 0:
                    self.components.remove(existing_component)
            else:
                raise CategoryException(f'Cannot substract {component_str} from existing {existing_component[-1]}')
        else:
            raise CategoryException(f'No such component: {component_str} in {self.name}')

    def filter(self, **kwargs):
        """Return list of components matching the parametric query."""
        result = []
        for component in self.components:
            for kwarg in kwargs:
                if kwarg not in self.format:
                    raise CategoryException(f'No param {kwarg} in {self.name}')
                idx = self.format.index(kwarg)
                if not (kwarg == 'Name' and component[idx].startswith(kwargs[kwarg])
                        or component[idx] == kwargs[kwarg]):
                    break
            else:
                result.append(component)

        result.sort(reverse=False, key=lambda c: c[-1])
        return ComponentCategory(f'{self.name} filtered', self.format_str, result)

    def filter_from_bound(self, param_str, bound_str, operation_str):
        """Return list of components which have the parameter matching the condition."""
        result = []
        for component in self.components:
            if param_str not in self.format:
                raise CategoryException(f'No param {param_str} in {self.name}')
            param_idx = self.format.index(param_str)
            bound = self._convert_value_to_abs(bound_str)
            value = self._convert_value_to_abs(component[param_idx])
            if operation_str == '>=':
                if value >= bound:
                    result.append(component)
            elif operation_str == '<=':
                if value <= bound:
                    result.append(component)
            else:
                raise CategoryException(f'No such operation: {operation_str}')
        result.sort(reverse=False, key=lambda c: c[-1])
        return ComponentCategory(f'{self.name} filtered', self.format_str, result)

    def calc_difference(self, other):
        """Return list of components of same category that are not in stock"""
        if other.format != self.format:
            raise CategoryException(
                    f'Format mismatch: {other.name}:{other.format_str} <> {self.name}:{self.format_str}')
        not_in_stock = []
        for o_component in other.components:
            for component in self.components:
                for i in range(len(component) - 1):
                    if component[i] != o_component[i]:
                        break
                else:
                    quantity = o_component[-1] - component[-1]
                    if quantity > 0:
                        component = component[:]
                        component[-1] = quantity
                        not_in_stock.append(component)
                    break
            else:
                not_in_stock.append(o_component[:])
        return ComponentCategory(f'{self.name} not in stock', self.format_str, not_in_stock)

    def __str__(self):
        components = list(self.components)
        components.sort(reverse=False, key=lambda c: c[-1])
        data = [self.format] + components
        return f'{self.name}\n{tabulate(data, headers="firstrow", tablefmt="fancy_grid")}'

    def __bool__(self):
        return bool(self.components)

    def convert_to_csv(self):
        components = list(','.join(map(str, c)) for c in self.components)
        table = "{}\n{}\n{}".format(self.name, self.format_str, '\n'.join(components))
        return table

    def get_all_variants_of_param(self, param_str):
        if param_str not in self.format:
            raise CategoryException(f'No param {param_str} in {self.name}')
        idx = self.format.index(param_str)
        variants = set()
        for c in self.components:
            variants.add(c[idx])
        return list(variants)

    def has_param(self, param_str):
        return param_str in self.format
