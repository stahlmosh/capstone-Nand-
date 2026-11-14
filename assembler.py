import sys
import os

class Parser:
    def __init__(self, filepath):
        with open(filepath, 'r') as f:
            raw_lines = f.readlines()
        
        self.lines = []
        for line_num, line in enumerate(raw_lines, 1):
            clean = line.split('//')[0].strip()
            if clean:
                self.lines.append((clean, line_num))
        
        self.current_idx = 0

    def has_more_lines(self):
        return self.current_idx < len(self.lines)

    def advance(self):
        if self.has_more_lines():
            self.current_idx += 1

    def current_instruction(self):
        return self.lines[self.current_idx][0] if self.has_more_lines() else ""

    def current_line_number(self):
        return self.lines[self.current_idx][1] if self.has_more_lines() else 0

    def instruction_type(self):
        inst = self.current_instruction()
        if inst.startswith('@'):
            return 'A_INSTRUCTION'
        elif inst.startswith('('):
            return 'L_INSTRUCTION'
        else:
            return 'C_INSTRUCTION'

    def symbol(self):
        inst = self.current_instruction()
        itype = self.instruction_type()
        if itype == 'A_INSTRUCTION':
            return inst[1:]
        elif itype == 'L_INSTRUCTION':
            return inst[1:-1]
        return None

    def dest(self):
        inst = self.current_instruction()
        if '=' in inst:
            return inst.split('=')[0]
        return 'null'

    def comp(self):
        inst = self.current_instruction()
        if '=' in inst:
            temp = inst.split('=')[1]
        else:
            temp = inst
        if ';' in temp:
            return temp.split(';')[0]
        return temp

    def jump(self):
        inst = self.current_instruction()
        if ';' in inst:
            return inst.split(';')[1]
        return 'null'


class Code:
    @staticmethod
    def dest(mnemonic):
        table = {
            'null': '000', 'M': '001', 'D': '010', 'MD': '011',
            'A': '100', 'AM': '101', 'AD': '110', 'AMD': '111'
        }
        return table.get(mnemonic, '000')

    @staticmethod
    def comp(mnemonic):
        table = {
            '0': '0101010', '1': '0111111', '-1': '0111010', 'D': '0001100',
            'A': '1100000', '!D': '0001101', '!A': '1100001', '-D': '0001111',
            '-A': '1100011', 'D+1': '0011111', 'A+1': '1100111', 'D-1': '0001110',
            'A-1': '1100010', 'D+A': '0000010', 'D-A': '0010011', 'A-D': '0000111',
            'D&A': '0000000', 'D|A': '0010101',
            'M': '1100000', '!M': '1100001', '-M': '1100011', 'M+1': '1100111',
            'M-1': '1100010', 'D+M': '0000010', 'D-M': '0010011', 'M-D': '0000111',
            'D&M': '0000000', 'D|M': '0010101'
        }
        return table.get(mnemonic, '0000000')

    @staticmethod
    def jump(mnemonic):
        table = {
            'null': '000', 'JGT': '001', 'JEQ': '010', 'JGE': '011',
            'JLT': '100', 'JNE': '101', 'JLE': '110', 'JMP': '111'
        }
        return table.get(mnemonic, '000')


class SymbolTable:
    def __init__(self):
        self.table = {
            'SP': 0, 'LCL': 1, 'ARG': 2, 'THIS': 3, 'THAT': 4,
            'SCREEN': 16384, 'KBD': 24576
        }
        for i in range(16):
            self.table[f'R{i}'] = i

    def add_entry(self, symbol, address):
        self.table[symbol] = address

    def contains(self, symbol):
        return symbol in self.table

    def get_address(self, symbol):
        return self.table.get(symbol, -1)


def assemble(input_file, K_value):
    parser = Parser(input_file)
    sym_table = SymbolTable()
    extra_mode = K_value % 3
    
    rom_address = 0
    while parser.has_more_lines():
        itype = parser.instruction_type()
        if itype == 'L_INSTRUCTION':
            symbol = parser.symbol()
            if sym_table.contains(symbol) and extra_mode == 2:
                print(f"WARNING: Duplicate label '{symbol}' detected at line {parser.current_line_number()}.")
            sym_table.add_entry(symbol, rom_address)
        else:
            rom_address += 1
        parser.advance()

    parser = Parser(input_file)
    variable_address = 16
    machine_code = []
    
    while parser.has_more_lines():
        itype = parser.instruction_type()
        line_num = parser.current_line_number()
        
        if itype == 'A_INSTRUCTION':
            symbol = parser.symbol()
            if symbol.isdigit():
                address = int(symbol)
            else:
                if not sym_table.contains(symbol):
                    sym_table.add_entry(symbol, variable_address)
                    variable_address += 1
                address = sym_table.get_address(symbol)
            machine_code.append(format(address, '016b'))
            
        elif itype == 'C_INSTRUCTION':
            try:
                d_mnemonic = parser.dest()
                c_mnemonic = parser.comp()
                j_mnemonic = parser.jump()
                
                a_bit = '1' if 'M' in c_mnemonic else '0'
                c_bits = Code.comp(c_mnemonic)
                d_bits = Code.dest(d_mnemonic)
                j_bits = Code.jump(j_mnemonic)
                
                machine_code.append(f"111{a_bit}{c_bits}{d_bits}{j_bits}")
            except Exception as e:
                if extra_mode == 1:
                    print(f"Line {line_num}: invalid instruction ({parser.current_instruction()})")
                    machine_code.append("0000000000000000")
                else:
                    raise SyntaxError(f"Invalid instruction at line {line_num}: {e}")
                    
        parser.advance()

    if extra_mode == 0:
        with open("symbols.txt", "w") as sym_file:
            for sym, addr in sym_table.table.items():
                sym_file.write(f"{sym}: {addr}\n")

    output_file = os.path.splitext(input_file)[0] + '.hack'
    with open(output_file, 'w') as f:
        for code in machine_code:
            f.write(code + '\n')
    print(f"Successfully assembled {input_file} -> {output_file}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python assembler.py <file.asm> <K_value>")
        sys.exit(1)
    assemble(sys.argv[1], int(sys.argv[2]))
