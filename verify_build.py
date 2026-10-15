"""Check that the executable contains the same icon images as assets/brand.ico."""
import hashlib
import struct
import sys
from pathlib import Path

import pefile


def verify(path):
    ico = Path(__file__).resolve().parent / "assets" / "brand.ico"
    data = ico.read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", data)
    if reserved != 0 or kind != 1:
        raise ValueError("Invalid ICO header")
    expected = []
    for index in range(count):
        _, _, _, _, _, _, length, offset = struct.unpack_from("<BBBBHHII", data, 6 + 16 * index)
        expected.append(hashlib.sha256(data[offset:offset + length]).hexdigest())
    actual = []
    with pefile.PE(str(path)) as executable:
        for entry in executable.DIRECTORY_ENTRY_RESOURCE.entries:
            if entry.id == pefile.RESOURCE_TYPE["RT_ICON"]:
                for resource in entry.directory.entries:
                    for language in resource.directory.entries:
                        item = language.data.struct
                        actual.append(hashlib.sha256(executable.get_data(item.OffsetToData, item.Size)).hexdigest())
    if sorted(expected) != sorted(actual):
        raise AssertionError("EXE icon resources differ from assets/brand.ico")
    print(f"ICON_RESOURCES_OK: {count} matching image sizes")


if __name__ == "__main__":
    verify(Path(sys.argv[1] if len(sys.argv) > 1 else "dist/VideoFlow.exe"))
