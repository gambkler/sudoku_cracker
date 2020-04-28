import json
import copy
import collections

class Unit:
    def __init__(self, row, column, box, value):
        self.row = row
        self.column = column
        self.box = box
        self.value = value
        self.candidate = set()
    
    def __str__(self):
        return '{} {} {} {} {}'.format(self.row, self.column, self.box, self.value, self.candidate)


class Cracker:
    default_filename = 'board.json'
    lines_index = [[(i, j) for j in range(9)] for i in range(9)] + \
                  [[(j, i) for j in range(9)] for i in range(9)]
    boxes_index = [[(m+i, n+j) for i in range(3) for j in range(3)] for m in range(0, 8, 3) for n in range(0, 8, 3)]
    numbers = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    cracker_count = 0
    filled_count = 0

    def init_board(self, filename=None):
        if filename is None:
            filename = self.default_filename
        with open(filename, 'w') as f:
            f.write(
'''[
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0]
]'''
            )
    
    def load_board(self, filename=None):
        if filename is None:
            filename = self.default_filename
        with open(filename) as f:
            self.board = json.load(f)
    
    def update_detail(self):
        self.update_line_detail()
        self.update_box_detail()
        self.update_unit_detail()
    
    def update_line_detail(self):
        self.line_sets = {}
        for i in range(9):
            row_name = 'R{}'.format(i)
            row_set = set(self.board[i])
            row_set.remove(0)
            self.line_sets[row_name] = row_set

            col_name = 'C{}'.format(i)
            col_set = set()
            for j in range(9):
                col_set.add(self.board[j][i])
            col_set.remove(0)
            self.line_sets[col_name] = col_set
    
    def update_box_detail(self):
        self.box_sets = {}
        for num, box in enumerate(self.boxes_index):
            box_set = set()
            for index in box:
                box_set.add(self.board[index[0]][index[1]])
            box_set.remove(0)
            self.box_sets['B{}'.format(num+1)] = box_set

    def update_unit_detail(self):
        self.units = []
        self.lines = collections.defaultdict(list)
        self.boxes = collections.defaultdict(list)
        for row in range(9):
            for col in range(9):
                box_num = (row//3)*3 + col//3 + 1
                unit = Unit(row, col, box_num, self.board[row][col])
                self.units.append(unit)
                self.lines['R{}'.format(row)].append(unit)
                self.lines['C{}'.format(col)].append(unit)
                self.boxes['B{}'.format(box_num)].append(unit)
    
    def crack(self):
        self.cracker_count = 0
        self.filled_count = 0
        self.scanner()
        print('crack loop {} time(s)'.format(self.cracker_count))
        print('filled {} unit(s)'.format(self.filled_count))

    def scanner(self):
        while True:
            hit_count = 0
            while True:
                count = self.exclusion()
                if not count:
                    break
                hit_count += count
            while True:
                count = self.single()
                if not count:
                    break
                hit_count += count
            self.cracker_count += 1
            if hit_count == 0:
                zero_count = 0
                for unit in self.units:
                    if not unit.value:
                        zero_count += 1
                if zero_count:
                    print('has {} zero'.format(zero_count))
                else:
                    print('complete')
                break

    def exclusion(self):
        hit_count = 0
        for unit in self.units:
            if unit.value:
                continue
            row_name = 'R{}'.format(unit.row)
            col_name = 'C{}'.format(unit.column)
            box_name = 'B{}'.format(unit.box)
            row_diff = self.numbers.difference(self.line_sets[row_name])
            col_diff = self.numbers.difference(self.line_sets[col_name])
            box_diff = self.numbers.difference(self.box_sets[box_name])
            result = row_diff.intersection(col_diff).intersection(box_diff)
            if len(result) == 1:
                unit.value = result.pop()
                self.line_sets[row_name].add(unit.value)
                self.line_sets[col_name].add(unit.value)
                self.box_sets[box_name].add(unit.value)
                unit.candidate = set()
                hit_count += 1
                self.filled_count += 1
                self.board[unit.row][unit.column] = unit.value
                print('set {} {} as {}'.format(unit.row, unit.column, unit.value))
                print(self.board)
            else:
                if unit.candidate and not result.issubset(unit.candidate):
                    raise Exception('{}, {}'.format(unit, result))
                unit.candidate = result
            if not unit.value and not unit.candidate:
                # raise Exception('here')
                pass
        return hit_count

    def single(self):
        hit_count = 0
        for key, units in self.lines.items():
            for unit in units:
                if unit.value:
                    continue
                row_name = 'R{}'.format(unit.row)
                col_name = 'C{}'.format(unit.column)
                box_name = 'B{}'.format(unit.box)
                diff = copy.deepcopy(unit.candidate)
                for u in units:
                    if u != unit:
                        if u.value and u.value in diff:
                            diff.remove(u.value)
                if len(diff) != 1:
                    for u in units:
                        if u != unit and not u.value:
                            diff.difference_update(u.candidate)
                if len(diff) == 1:
                    unit.value = diff.pop()
                    self.line_sets[row_name].add(unit.value)
                    self.line_sets[col_name].add(unit.value)
                    self.box_sets[box_name].add(unit.value)
                    unit.candidate = set()
                    hit_count += 1
                    self.filled_count += 1
                    self.board[unit.row][unit.column] = unit.value
                    print('set {} {} as {}'.format(unit.row, unit.column, unit.value))
                    print(self.board)
        
        for key, units in self.boxes.items():
            for unit in units:
                if unit.value:
                    continue
                row_name = 'R{}'.format(unit.row)
                col_name = 'C{}'.format(unit.column)
                box_name = 'B{}'.format(unit.box)
                diff = copy.deepcopy(unit.candidate)
                for u in units:
                    if u != unit:
                        if u.value and u.value in diff:
                            diff.remove(u.value)
                if len(diff) != 1:
                    for u in units:
                        if u != unit and not u.value:
                            diff.difference_update(u.candidate)
                if len(diff) == 1:
                    unit.value = diff.pop()
                    self.line_sets[row_name].add(unit.value)
                    self.line_sets[col_name].add(unit.value)
                    self.box_sets[box_name].add(unit.value)
                    unit.candidate = set()
                    hit_count += 1
                    self.filled_count += 1
                    self.board[unit.row][unit.column] = unit.value
                    print('set {} {} as {}'.format(unit.row, unit.column, unit.value))
                    print(self.board)
        
        return hit_count

    def print_board(self):
        count = 0
        for unit in self.units:
            print('{} '.format(unit.value), end='')
            count += 1
            if count % 9 == 0:
                print('')

if __name__ == "__main__":
    b = Cracker()
    # b.load_board(input('board_file_name: '))
    b.load_board()
    b.update_detail()
    b.crack()
    b.print_board()
