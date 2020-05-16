"""CPU functionality."""
import sys

'''
Local Registers/variables
* `PC`: Program Counter, address of the currently executing instruction
* `IR`: Instruction Register, contains a copy of the currently executing instruction
* `MAR`: Memory Address Register, holds the memory address we're reading or writing
* `MDR`: Memory Data Register, holds the value to write or the value just read
* `FL`: holds the current flags status

Meanings of the bits in the first byte of each instruction: `AABCDDDD`
* `AA` Number of operands for this opcode, 0-2
* `B` 1 if this is an ALU operation
* `C` 1 if this instruction sets the PC
* `DDDD` Instruction identifier


'''
HLT = 0b00000001 #1 Halt the CPU (and exit the emulator).
PRN = 0b01000111 #71 `PRN register` - Print numeric value stored in the given register.
LDI = 0b10000010 #130 `LDI register immediate` - Set the value of a register to an integer.
POP = 0b01000110 #70 Pop the value at the top of the stack into the given register
PUSH = 0b01000101 #69 Push the value in the given register on the stack.
CALL = 0b01010000 #80 Calls a subroutine (function) at the address stored in the register
RET = 0b00010001 #17 Return from subroutine

ADD = 0b10100000 #160
MUL = 0b10100010 #162

SPreg = 7 #Dedicated CPU register for Stack Pointer for RAM


class CPU:
	"""Main CPU class."""
	def __init__(self):
		"""Construct a new CPU."""
		self.running = True
		self.pc = 0
		self.registers = [0] * 8
		self.ram = [0] * 256
		self.registers[SPreg] = 244 #len(self.ram) - 1
		self.branchtable = {}
		self.branchtable[HLT] = self.handle_HLT
		self.branchtable[PRN] = self.handle_PRN
		self.branchtable[LDI] = self.handle_LDI
		self.branchtable[POP] = self.handle_POP
		self.branchtable[PUSH] = self.handle_PUSH
		self.branchtable[CALL] = self.handle_CALL
		self.branchtable[RET] = self.handle_RET
		
	def handle_HLT(self, operand_a, operand_b, Number_of_operands):
		self.running = False

	def handle_PRN(self, operand_a, operand_b, Number_of_operands):
		print( int( self.registers[operand_a]))
		self.pc += Number_of_operands + 1

	def handle_LDI(self, operand_a, operand_b, Number_of_operands):
		self.registers[operand_a] = operand_b
		self.pc += Number_of_operands + 1

	def handle_POP(self, operand_a, operand_b, Number_of_operands):
		self.registers[operand_a] = self.ram[ self.registers[ SPreg]]
		self.pc += Number_of_operands + 1
		self.registers[SPreg] += 1

	def handle_PUSH(self, operand_a, operand_b, Number_of_operands):
		self.registers[SPreg] -= 1
		self.ram[ self.registers[ SPreg]] = self.registers[operand_a]
		self.pc += Number_of_operands + 1

	def handle_CALL(self, operand_a, operand_b, Number_of_operands):
		self.registers[ SPreg] -= 1
		self.ram[ self.registers[ SPreg]] = self.pc + Number_of_operands + 1
		self.pc = self.registers[operand_a]

	def handle_RET(self, operand_a, operand_b, Number_of_operands):
		self.pc = self.ram[ self.registers[ SPreg]]
		self.registers[SPreg] += 1

	def ram_read(self, MAR):
		return self.ram[MAR]

	def ram_write(self, MAR, MDR):
		self.ram[MAR] = MDR

	def load(self):
		"""Load a program into memory."""

		if len(sys.argv) != 2:
			print("Need proper file name passed")
			sys.exit(1)

		address = 0
		filename = sys.argv[1]

		with open(filename) as f:
			for line in f:

				comment_split = line.split('#')
				num = comment_split[0].strip()

				if line == '' or num == '':
					continue

				self.ram[address] = int(num,2)
				address += 1

		# program = [
		# 	# From print8.ls8
		# 	0b10000010, # LDI R0,8
		# 	0b00000000,
		# 	0b00001000,
		# 	0b01000111, # PRN R0
		# 	0b00000000,
		# 	0b00000001, # HLTpy
		# ]

		# for instruction in program:
		# 	self.ram[address] = instruction
		# 	address += 1


	def alu(self, op, reg_a, reg_b):
		"""ALU operations."""

		if op == ADD:
			self.registers[reg_a] += self.registers[reg_b]

		elif op == MUL:
			self.registers[reg_a] *= self.registers[reg_b]

		else:
			raise Exception("Unsupported ALU operation")

		self.pc += 3

	def trace(self):
		"""
		Handy function to print out the CPU state. You might want to call this
		from run() if you need help debugging.
		"""

		print(f"TRACE: %02X | %02X %02X %02X |" % (
			self.pc,
			#self.fl,
			#self.ie,
			self.ram_read(self.pc),
			self.ram_read(self.pc + 1),
			self.ram_read(self.pc + 2)
		), end='')

		for i in range(8):
			print(" %02X" % self.registers[i], end='')

		print()

	def run(self):
		"""Run the CPU."""

		while self.running:
			IR = self.ram_read(self.pc)
			operand_a = self.ram_read(self.pc + 1)
			operand_b = self.ram_read(self.pc + 2)

			'''
			Meanings of the bits in the first byte of each instruction: `AABCDDDD`
			* `AA` Number of operands for this opcode, 0-2
			* `B` 1 if this is an ALU operation
			* `C` 1 if this instruction sets the PC
			* `DDDD` Instruction identifier
			'''
			Number_of_operands = int(IR >> 6)
			Is_ALU = IR >> 5 & 0b001
			Sets_PC = IR >> 4 & 0b0001
			I_ID = IR & 0b00001111

			if Is_ALU:
				self.alu(IR, operand_a, operand_b)
			else:
				self.branchtable[IR](operand_a, operand_b, Number_of_operands)

				# if IR == LDI:
				# 	self.registers[operand_a] = operand_b
				# 	self.pc += Number_of_operands + 1

				# elif IR == CALL:
				# 	self.registers[ SPreg] -= 1
				# 	self.ram[ self.registers[ SPreg]] = self.pc + Number_of_operands + 1
				# 	self.pc = self.registers[operand_a]

				# elif IR == RET:
				# 	self.pc = self.ram[ self.registers[ SPreg]]
				# 	self.registers[SPreg] += 1

				# elif IR == PRN:
				# 	print( int( self.registers[operand_a]))
				# 	self.pc += Number_of_operands + 1

				# elif IR == POP:
				# 	self.registers[operand_a] = self.ram[ self.registers[ SPreg]]
				# 	self.pc += Number_of_operands + 1
				# 	self.registers[SPreg] += 1

				# elif IR == PUSH:
				# 	self.registers[SPreg] -= 1
				# 	self.ram[ self.registers[ SPreg]] = self.registers[operand_a]
				# 	self.pc += Number_of_operands + 1

				# elif IR == HLT:
				# 	self.running = False
