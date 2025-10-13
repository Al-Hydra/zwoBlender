import struct
import sys
import json
import zlib
from pathlib import Path
from typing import Dict, Optional, List, Tuple

class XMCNode:
    """Represents a node in the XMC structure (16 bytes)"""
    def __init__(self, data: bytes):
        # Node structure from decompiled code:
        # offset 0x00: CRC32 of tag name (4 bytes)
        # offset 0x04: parent index (2 bytes, signed short)
        # offset 0x06: child count (2 bytes, signed short)
        # offset 0x08: first child index (2 bytes, signed short)
        # offset 0x0A: attribute count (2 bytes, signed short)
        # offset 0x0C: first attribute index (2 bytes, signed short)
        # offset 0x0E: padding (2 bytes)
        unpacked = struct.unpack('<IhhhhhH', data)
        self.tag_crc = unpacked[0]
        self.parent_idx = unpacked[1]
        self.child_count = unpacked[2]
        self.first_child = unpacked[3]
        self.attr_count = unpacked[4]
        self.first_attr = unpacked[5]
        
    def __repr__(self):
        return (f"XMCNode(crc={self.tag_crc:08X}, parent={self.parent_idx}, "
                f"children={self.child_count}@{self.first_child}, "
                f"attrs={self.attr_count}@{self.first_attr})")


class XMCAttribute:
    """Represents an attribute in the XMC structure (8 bytes)"""
    def __init__(self, data: bytes):
        # Attribute structure:
        # offset 0x00: CRC32 of attribute name (4 bytes)
        # offset 0x04: string pool offset for value (4 bytes)
        self.name_crc, self.value_offset = struct.unpack('<II', data)
        
    def __repr__(self):
        return f"XMCAttr(name_crc={self.name_crc:08X}, value_offset={self.value_offset})"


class XMCParser:
    """
    Parser for XMC (XML Compiled) format based on complete CZXmlLite structure.
    
    CZXmlLite structure (0x1C bytes):
    offset 0x00: node_count (uint32)
    offset 0x04: node_data_ptr (pointer to 16-byte node array)
    offset 0x08: node_lite_ptr (pointer to 8-byte CZXmlNodeLite array)
    offset 0x0C: attribute_count (uint32)
    offset 0x10: attribute_data_ptr (pointer to 8-byte attribute array)
    offset 0x14: string_pool_size (uint32)
    offset 0x18: string_pool_ptr (pointer to string pool)
    """
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.node_count = 0
        self.attribute_count = 0
        self.string_pool_size = 0
        self.nodes: List[XMCNode] = []
        self.attributes: List[XMCAttribute] = []
        self.string_pool = b''
        
    def read_uint(self, f) -> Optional[int]:
        """Read a 32-bit unsigned integer (little-endian)"""
        data = f.read(4)
        if len(data) != 4:
            return None
        return struct.unpack('<I', data)[0]
    
    def get_string(self, offset: int) -> str:
        """
        Get null-terminated string from string pool at given offset.
        Based on GetAttributeASCII implementation.
        """
        if offset >= len(self.string_pool):
            return ""
        
        # Find null terminator
        end = self.string_pool.find(b'\x00', offset)
        if end == -1:
            end = len(self.string_pool)
        
        try:
            return self.string_pool[offset:end].decode('utf-8', errors='replace')
        except:
            return self.string_pool[offset:end].decode('latin-1', errors='replace')
    
    def parse(self):
        """
        Parse XMC file following CZXmlLite::LoadRaw structure.
        
        File format:
        1. Header: 3 uint32 values (node_count, attribute_count, string_pool_size)
        2. Node array: node_count * 16 bytes
        3. Attribute array: attribute_count * 8 bytes
        4. String pool: string_pool_size bytes
        """
        with open(self.filepath, 'rb') as f:
            # Read header (matches the three ReadUint calls in LoadRaw)
            self.node_count = self.read_uint(f)
            if self.node_count is None:
                raise ValueError("Failed to read node count")
            
            self.attribute_count = self.read_uint(f)
            if self.attribute_count is None:
                raise ValueError("Failed to read attribute count")
            
            self.string_pool_size = self.read_uint(f)
            if self.string_pool_size is None:
                raise ValueError("Failed to read string pool size")
            
            print(f"Header: nodes={self.node_count}, attrs={self.attribute_count}, "
                  f"strings={self.string_pool_size} bytes")
            
            # Read node array (*(int *)this << 4 = node_count * 16)
            if self.node_count > 0:
                node_data_size = self.node_count * 16
                node_data = f.read(node_data_size)
                if len(node_data) != node_data_size:
                    raise ValueError(f"Failed to read node data")
                
                for i in range(self.node_count):
                    offset = i * 16
                    node = XMCNode(node_data[offset:offset + 16])
                    self.nodes.append(node)
                    
                print(f"Loaded {len(self.nodes)} nodes")
            
            # Read attribute array (*(int *)(this + 0xc) << 3 = attr_count * 8)
            if self.attribute_count > 0:
                attr_data_size = self.attribute_count * 8
                attr_data = f.read(attr_data_size)
                if len(attr_data) != attr_data_size:
                    raise ValueError(f"Failed to read attribute data")
                
                for i in range(self.attribute_count):
                    offset = i * 8
                    attr = XMCAttribute(attr_data[offset:offset + 8])
                    self.attributes.append(attr)
                    
                print(f"Loaded {len(self.attributes)} attributes")
            
            # Read string pool
            if self.string_pool_size > 0:
                self.string_pool = f.read(self.string_pool_size)
                if len(self.string_pool) != self.string_pool_size:
                    raise ValueError("Failed to read string pool")
                    
                print(f"Loaded {len(self.string_pool)} byte string pool")
    
    def resolve_name(self, crc: int, crc_dict: Optional[Dict[int, str]], 
                     prefix: str = "tag") -> str:
        """Resolve CRC32 to name using dictionary, or return hex representation"""
        if crc_dict and crc in crc_dict:
            return crc_dict[crc]
        return f"{prefix}_{crc:08X}"
    
    def get_node_attributes(self, node: XMCNode, crc_dict: Optional[Dict[int, str]]) -> List[Tuple[str, str]]:
        """
        Get all attributes for a node.
        Based on GetAttributeASCII logic.
        """
        attrs = []
        
        if node.attr_count > 0:
            for i in range(node.attr_count):
                attr_idx = node.first_attr + i
                if 0 <= attr_idx < len(self.attributes):
                    attr = self.attributes[attr_idx]
                    
                    # Resolve attribute name
                    attr_name = self.resolve_name(attr.name_crc, crc_dict, "attr")
                    
                    # Get attribute value from string pool
                    attr_value = self.get_string(attr.value_offset)
                    
                    attrs.append((attr_name, attr_value))
        
        return attrs
    
    def build_xml_recursive(self, node_idx: int, indent: int, 
                           crc_dict: Optional[Dict[int, str]],
                           visited: set) -> str:
        """
        Recursively build XML string from parsed data.
        Based on the hierarchical structure revealed in the decompiled code.
        """
        if node_idx >= len(self.nodes) or node_idx < 0:
            return ""
        
        # Prevent infinite recursion
        if node_idx in visited:
            return f"{'  ' * indent}<!-- Circular reference to node {node_idx} -->\n"
        visited.add(node_idx)
        
        node = self.nodes[node_idx]
        indent_str = "  " * indent
        
        # Resolve tag name from CRC32
        tag_name = self.resolve_name(node.tag_crc, crc_dict, "tag")
        
        xml = f"{indent_str}<{tag_name}"
        
        # Add attributes
        attrs = self.get_node_attributes(node, crc_dict)
        for attr_name, attr_value in attrs:
            xml += f' {attr_name}="{escape_xml(attr_value)}"'
        
        # Handle children (based on child_count and first_child from node structure)
        if node.child_count > 0:
            xml += ">\n"
            
            # Process each child
            for i in range(node.child_count):
                child_idx = node.first_child + i
                if 0 <= child_idx < len(self.nodes):
                    xml += self.build_xml_recursive(child_idx, indent + 1, crc_dict, visited)
            
            xml += f"{indent_str}</{tag_name}>\n"
        else:
            xml += " />\n"
        
        visited.remove(node_idx)
        return xml
    
    def to_xml(self, crc_dict: Optional[Dict[int, str]] = None) -> str:
        """
        Convert XMC to XML string.
        Starts from root node (index 0) as per GetRootNode() implementation.
        """
        if not self.nodes:
            return '<?xml version="1.0" encoding="UTF-8"?>\n'
        
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        visited = set()
        xml += self.build_xml_recursive(0, 0, crc_dict, visited)
        return xml
    
    def debug_print(self):
        """Print debug information about the parsed structure"""
        print("\n=== Debug Information ===")
        print(f"\nNodes ({len(self.nodes)}):")
        for i, node in enumerate(self.nodes[:10]):  # Show first 10
            print(f"  [{i}] {node}")
        if len(self.nodes) > 10:
            print(f"  ... and {len(self.nodes) - 10} more")
            
        print(f"\nAttributes ({len(self.attributes)}):")
        for i, attr in enumerate(self.attributes[:10]):  # Show first 10
            value = self.get_string(attr.value_offset)
            print(f"  [{i}] {attr} = '{value}'")
        if len(self.attributes) > 10:
            print(f"  ... and {len(self.attributes) - 10} more")


def escape_xml(text: str) -> str:
    """Escape special XML characters"""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))


def load_crc_dictionary(dict_file: str) -> Dict[int, str]:
    """
    Load CRC32 to name mapping from JSON or text file.
    Supports both hash->name mappings and plain name lists.
    """
    crc_map = {}
    
    try:
        with open(dict_file, 'r', encoding='utf-8') as f:
            # Try to parse as JSON first
            try:
                data = json.load(f)
                
                # Handle dict format: {"12345": "name", ...}
                if isinstance(data, dict):
                    for key, value in data.items():
                        try:
                            # Try to interpret key as integer (hash value)
                            crc = int(key)
                            crc_map[crc] = value
                        except ValueError:
                            # If key isn't a number, calculate CRC32 from it
                            crc = zlib.crc32(key.encode('utf-8')) & 0xFFFFFFFF
                            crc_map[crc] = value
                    print(f"Loaded {len(crc_map)} hashes from JSON dictionary")
                    
                # Handle list format: ["name1", "name2", ...]
                elif isinstance(data, list):
                    for name in data:
                        if isinstance(name, str) and name:
                            crc = zlib.crc32(name.encode('utf-8')) & 0xFFFFFFFF
                            crc_map[crc] = name
                    print(f"Loaded {len(crc_map)} names from JSON list")
                    
            except json.JSONDecodeError:
                # Fall back to text file format (one name per line)
                f.seek(0)
                for line in f:
                    name = line.strip()
                    if name:
                        crc = zlib.crc32(name.encode('utf-8')) & 0xFFFFFFFF
                        crc_map[crc] = name
                print(f"Loaded {len(crc_map)} names from text dictionary")
                
    except FileNotFoundError:
        print(f"Warning: Dictionary file '{dict_file}' not found")
        print("         Using CRC values as names")
    except Exception as e:
        print(f"Error loading dictionary: {e}")
        print("Continuing without dictionary...")
    
    return crc_map


def main():
    '''if len(sys.argv) < 2:
        print("XMC to XML Converter - Based on CZXmlLite reverse engineering")
        print("\nUsage: python xmc_converter.py <input.xmc> [output.xml] [dictionary.json]")
        print("\nDictionary formats supported:")
        print("  - JSON hash map: {\"228449\": \"filename.ext\", \"440148\": \"other.ext\"}")
        print("  - JSON name list: [\"tagname\", \"attrname\", ...]")
        print("  - Text file: one tag/attribute name per line")
        print("\nOptions:")
        print("  --debug    Show debug information about the file structure")
        sys.exit(1)'''
    
    debug_mode = '--debug' in sys.argv
    if debug_mode:
        sys.argv.remove('--debug')
    
    input_file = r"G:\SteamLibrary\steamapps\common\Obscure2\datapack\characters\combos.xmc"
    output_file = str(Path(input_file).with_suffix('.xml'))
    dict_file = r"G:\Dev\zwoBlender\zwoLib\utils\hashes.json"
    
    # Load CRC dictionary if provided
    crc_dict = load_crc_dictionary(dict_file) if dict_file else None
    
    # Parse XMC file
    print(f"\nParsing: {input_file}")
    parser = XMCParser(input_file)
    parser.parse()
    
    # Show debug info if requested
    if debug_mode:
        parser.debug_print()
    
    # Convert to XML
    print(f"\nConverting to XML...")
    xml_output = parser.to_xml(crc_dict)
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_output)
    
    print(f"✓ Successfully converted: {output_file}")
    print(f"  Generated {xml_output.count('<')} XML elements")


if __name__ == "__main__":
    main()
