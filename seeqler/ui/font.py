from typing import Generator


__all__ = ("ENCODING_CHARMAPS", "ENCODING_TRANSLITERATION", "TAG_DEFAULT_FONT")


def __get_font_remap(as_translation: bool = False) -> dict[int, int] | Generator:
    cp1251 = list(range(0xC0, 0xFF + 1))
    unicode = list(range(0xC0 + 0x350, 0xFF + 1 + 0x350))

    # fmt: off
    cp1251.extend([
        0x80, 0x81, 0x83, 0x88, 0x8A, 0x8C, 0x8D, 0x8E, 0x8F,
        0x90, 0x9A, 0x9C, 0x9D, 0x9E, 0x9F,
        0xA1, 0xA2, 0xA3, 0xA5, 0xA8, 0xAA, 0xAF,
        0xB2, 0xB3, 0xB4, 0xB8, 0xB9, 0xBA, 0xBC, 0xBD, 0xBE, 0xBF
    ])
    unicode.extend([
        0x0402, 0x0403, 0x0453, 0x20AC, 0x0409, 0x040A, 0x040C, 0x040B, 0x040F,
        0x0452, 0x0459, 0x045A, 0x045C, 0x045B, 0x045F,
        0x040E, 0x045E, 0x0408, 0x0490, 0x0401, 0x0404, 0x0407,
        0x0406, 0x0456, 0x0491, 0x0451, 0x2116, 0x0454, 0x0458, 0x0405, 0x0455, 0x0457
    ])
    # fmt: on

    if as_translation:
        return str.maketrans(''.join(chr(x) for x in cp1251), ''.join(chr(x) for x in unicode))

    return zip(cp1251, unicode)


ENCODING_TRANSLITERATION = __get_font_remap(True)
ENCODING_CHARMAPS = __get_font_remap()
TAG_DEFAULT_FONT = 'default font'
