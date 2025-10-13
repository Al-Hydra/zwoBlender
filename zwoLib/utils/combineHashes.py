from zlib import crc32
import json



hashes_dict = json.load(open(r"G:\Dev\HVFilePacker\hashes.json", "r"))

new_strings_path = (r"C:\Users\Hydra\Desktop\extracted")

with open(new_strings_path, "r", encoding="utf-8") as f:
    new_strings = [line.strip() for line in f if line.strip()]

new_hash_count = 0
collision_count = 0
old_hash_count = len(hashes_dict)
total_strings = len(new_strings)

for s in new_strings:
    h = str(crc32(s.encode('utf-8')) & 0xFFFFFFFF)
    if h not in hashes_dict:
        hashes_dict[h] = s
        print(f'Added: "{s}" with hash {h}')
        new_hash_count += 1
    else:
        if hashes_dict[h] != s:
            print(f'Hash collision: "{s}" and "{hashes_dict[h]}" both hash to {h}')
            collision_count += 1
print(f"Processed {total_strings} strings.")
print(f"Added {new_hash_count} new hashes.")
print(f"Detected {collision_count} hash collisions.")
print(f"Total hashes in dictionary: {len(hashes_dict)} (was {old_hash_count})")


with open(r"G:\Dev\zwoBlender\zwoLib\utils\hashes.json", "w", encoding="utf-8") as f:
    json.dump(hashes_dict, f, ensure_ascii=False, indent=4)

'''wrong_hash_count = 0
#compare existing hashes with their strings
for h, s in list(hashes_dict.items()):
    if str(crc32(s.encode('utf-8')) & 0xFFFFFFFF) != h:
        print(f'Hash mismatch: "{s}" is stored with hash {h} but actually hashes to {str(crc32(s.encode("utf-8")) & 0xFFFFFFFF)}')
        wrong_hash_count += 1'''

#print(crc32("ch12_musé_confrerie_b.mib".encode('utf-8')) & 0xFFFFFFFF)