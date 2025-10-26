

class BitsetsSerializer:
    def __init__(self, bits_per_entry: int, bitset_length_in_bits: int):
        self._bits_per_entry = bits_per_entry
        self._bitset_length_in_bits = bitset_length_in_bits

    def to_bitsets(self, entries: list[int]) -> list[int]:
        bitsets = []
        for i, entry in enumerate(entries):
            if i % (self._bitset_length_in_bits // self._bits_per_entry) == 0:
                bitsets.append(0)
            bitsets[-1] |= (entry & ((1 << self._bits_per_entry) - 1)) << (i % (self._bitset_length_in_bits // self._bits_per_entry) * self._bits_per_entry)
        return bitsets
    
    def from_bitsets(self, entries_in_bitsets: int, bitsets: list[int]) -> list[int]:
        map: list[int] = []
        for bitset in bitsets:
            map.extend((bitset >> (i * self._bits_per_entry) & ((1 << self._bits_per_entry) - 1) for i in range(self._bitset_length_in_bits // self._bits_per_entry)))
        return map[:entries_in_bitsets]
    
def to_signed(unsigned_value: int, bits: int) -> int:
    '''
    Convert an unsigned integer to a signed integer.
    '''
    if unsigned_value >= (1 << (bits - 1)):
        return unsigned_value - (1 << bits)
    return unsigned_value

def to_unsigned(signed_value: int, bits: int) -> int:
    '''
    Convert a signed integer to an unsigned integer.
    '''
    if signed_value < 0:
        signed_value += (1 << bits)
    return signed_value