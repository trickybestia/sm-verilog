from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Self


def reverse_bits(n: int, width: int) -> int:
    result = 0

    for _ in range(width):
        result <<= 1
        result |= n & 1
        n >>= 1

    return result


class InstructionBuilder:
    _n: int
    _length: int

    def __init__(self, length: int) -> None:
        self._n = 0
        self._length = length

    def write(self, n: int, n_length: int, index: int) -> Self:
        n &= 2**n_length - 1

        self._n |= reverse_bits(n, n_length) << (self._length * 8 - index - n_length)

        return self

    def to_bytes(self) -> bytes:
        return self._n.to_bytes(self._length)


class Instruction(ABC):
    @abstractmethod
    def to_bytes(self) -> bytes:
        ...


@dataclass
class Jump(Instruction):
    addr: int

    def to_bytes(self) -> bytes:
        return InstructionBuilder(2).write(3, 2, 0).write(self.addr, 8, 8).to_bytes()


@dataclass
class IORead(Instruction):
    input: int
    rd: int

    def to_bytes(self) -> bytes:
        return (
            InstructionBuilder(1)
            .write(self.input, 1, 5)
            .write(self.rd, 2, 6)
            .to_bytes()
        )


@dataclass
class IOWrite(Instruction):
    rs: int
    output: int

    def to_bytes(self) -> bytes:
        return (
            InstructionBuilder(1)
            .write(1, 1, 4)
            .write(self.output, 1, 5)
            .write(self.rs, 2, 2)
            .to_bytes()
        )


@dataclass
class Load(Instruction):
    rd: int
    imm: int

    def to_bytes(self) -> bytes:
        return (
            InstructionBuilder(2)
            .write(2, 2, 0)
            .write(self.rd, 2, 6)
            .write(self.imm, 8, 8)
            .to_bytes()
        )


@dataclass
class Add(Instruction):
    rs1: int
    rs2: int
    rd: int

    def to_bytes(self) -> bytes:
        return (
            InstructionBuilder(2)
            .write(1, 2, 0)
            .write(self.rs1, 2, 2)
            .write(self.rs2, 2, 4)
            .write(self.rd, 2, 6)
            .to_bytes()
        )


@dataclass
class Sub(Instruction):
    rs1: int
    rs2: int
    rd: int

    def to_bytes(self) -> bytes:
        return (
            InstructionBuilder(2)
            .write(1, 2, 0)
            .write(1, 1, 15)
            .write(self.rs1, 2, 2)
            .write(self.rs2, 2, 4)
            .write(self.rd, 2, 6)
            .to_bytes()
        )


def compile_instructions(instructions: list[Instruction]) -> bytes:
    result = b""

    for byte in b"".join(i.to_bytes() for i in instructions):
        result += reverse_bits(byte, 8).to_bytes()

    return result


# Calculates Fibonacci sequence
# 2 - a
# 3 - b

instructions: list[Instruction] = [
    Load(rd=3, imm=1),
    Add(rs1=2, rs2=3, rd=2),
    IOWrite(rs=2, output=1),
    Add(rs1=3, rs2=2, rd=3),
    IOWrite(rs=3, output=1),
    Jump(addr=2),
]

Path("instructions.bin").write_bytes(compile_instructions(instructions))
