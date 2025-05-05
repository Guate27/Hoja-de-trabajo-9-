import os
import heapq
import pickle
from collections import Counter
import unittest
import time

class HuffmanNode:
    def __init__(self, char=None, freq=0):
        self.char = char        
        self.freq = freq        
        self.left = None        
        self.right = None       
        
    def __lt__(self, other):
        return self.freq < other.freq
    
    def is_leaf(self):
        return self.char is not None
        
class HuffmanCompressor:
    def __init__(self):
        self.frequency_map = {}      
        self.huffman_tree = None     
        self.codes = {}              
        
    def calculate_frequencies(self, text):

        self.frequency_map = Counter(text)
        return self.frequency_map
    
    def build_huffman_tree(self):

        if not self.frequency_map:
            raise ValueError("No hay frecuencias calculadas. Ejecute calculate_frequencies primero.")

        priority_queue = [HuffmanNode(char, freq) for char, freq in self.frequency_map.items()]
        heapq.heapify(priority_queue)

        while len(priority_queue) > 1:
            left = heapq.heappop(priority_queue)
            right = heapq.heappop(priority_queue)

            internal_node = HuffmanNode(freq=left.freq + right.freq)
            internal_node.left = left
            internal_node.right = right
            
            heapq.heappush(priority_queue, internal_node)

        self.huffman_tree = priority_queue[0] if priority_queue else None
        return self.huffman_tree
    
    def generate_codes(self, node=None, code=""):

        if node is None:
            if self.huffman_tree is None:
                raise ValueError("No hay árbol de Huffman. Ejecute build_huffman_tree primero.")
            node = self.huffman_tree
            self.codes = {}
        
        if node.is_leaf():
            self.codes[node.char] = code if code else "0" 
            return
        
        if node.left:
            self.generate_codes(node.left, code + "0")
        if node.right:
            self.generate_codes(node.right, code + "1")
            
        return self.codes
    
    def serialize_tree(self, node=None):

        if node is None:
            if self.huffman_tree is None:
                raise ValueError("No hay árbol de Huffman. Ejecute build_huffman_tree primero.")
            node = self.huffman_tree
        
        serialized = []
        if node.is_leaf():
            serialized.append(True)
            serialized.append(node.char)
        else:
            serialized.append(False)
            if node.left:
                serialized.extend(self.serialize_tree(node.left))
            if node.right:
                serialized.extend(self.serialize_tree(node.right))
                
        return serialized
    
    def deserialize_tree(self, serialized):

        if not serialized:
            return None, []
        
        is_leaf = serialized[0]
        
        if is_leaf:
            char = serialized[1]
            node = HuffmanNode(char, 0)
            return node, serialized[2:]
        else:
            node = HuffmanNode()
            left_node, remaining = self.deserialize_tree(serialized[1:])
            node.left = left_node
            right_node, remaining = self.deserialize_tree(remaining)
            node.right = right_node
            
            return node, remaining
    
    def compress(self, input_file, output_file_prefix):
        try:
            with open(input_file, 'r', encoding='utf-8') as file:
                text = file.read()
        except Exception as e:
            raise IOError(f"Error al leer el archivo: {e}")

        self.calculate_frequencies(text)
        self.build_huffman_tree()
        self.generate_codes()
        
        encoded_text = ""
        for char in text:
            encoded_text += self.codes[char]
        padding = 8 - (len(encoded_text) % 8) if (len(encoded_text) % 8) != 0 else 0
        padded_text = encoded_text + '0' * padding

        bytes_array = bytearray()
        for i in range(0, len(padded_text), 8):
            byte = padded_text[i:i+8]
            bytes_array.append(int(byte, 2))
        
        serialized_tree = self.serialize_tree()
        try:
            with open(f"{output_file_prefix}.hufftree", 'wb') as file:
                pickle.dump((serialized_tree, padding), file)
            with open(f"{output_file_prefix}.huff", 'wb') as file:
                file.write(bytes_array)
                
            return os.path.getsize(input_file), os.path.getsize(f"{output_file_prefix}.huff")
        except Exception as e:
            raise IOError(f"Error al escribir los archivos: {e}")
    
    def decompress(self, huff_file, hufftree_file, output_file=None):
        try:
            with open(hufftree_file, 'rb') as file:
                serialized_tree, padding = pickle.load(file)

            self.huffman_tree, _ = self.deserialize_tree(serialized_tree)
            
            with open(huff_file, 'rb') as file:
                byte_data = file.read()
        except Exception as e:
            raise IOError(f"Error al leer los archivos: {e}")

        bits = ""
        for byte in byte_data:
            bits += bin(byte)[2:].zfill(8)

        bits = bits[:-padding] if padding else bits
 
        decoded_text = ""
        current_node = self.huffman_tree
        for bit in bits:
            current_node = current_node.left if bit == '0' else current_node.right
            
            if current_node.is_leaf():
                decoded_text += current_node.char
                current_node = self.huffman_tree

        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as file:
                    file.write(decoded_text)
            except Exception as e:
                raise IOError(f"Error al escribir el archivo descomprimido: {e}")
                
        return decoded_text


class HuffmanTests(unittest.TestCase):
    def setUp(self):
        """Preparación para las pruebas."""
        self.compressor = HuffmanCompressor()
        self.test_text = "este es un texto de prueba para el algoritmo de huffman"
        with open('test_file.txt', 'w', encoding='utf-8') as file:
            file.write(self.test_text)
    
    def tearDown(self):
        """Limpieza después de las pruebas."""
        files_to_remove = ['test_file.txt', 'test_file.huff', 'test_file.hufftree', 'test_file_decompressed.txt']
        for file in files_to_remove:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass
    
    def test_frequency_calculation(self):
        """Prueba el cálculo de frecuencias."""
        frequencies = self.compressor.calculate_frequencies(self.test_text)
        self.assertEqual(frequencies['e'], 8)  
        self.assertEqual(frequencies['t'], 4)  
        self.assertEqual(frequencies[' '], 10)  
    
    def test_tree_construction(self):
        """Prueba la construcción del árbol de Huffman."""
        self.compressor.calculate_frequencies(self.test_text)
        tree = self.compressor.build_huffman_tree()

        self.assertIsNotNone(tree)

        total_freq = sum(self.compressor.frequency_map.values())
        self.assertEqual(tree.freq, total_freq)
    
    def test_code_generation(self):
        """Prueba la generación de códigos Huffman."""
        self.compressor.calculate_frequencies(self.test_text)
        self.compressor.build_huffman_tree()
        codes = self.compressor.generate_codes()

        self.assertEqual(len(codes), len(self.compressor.frequency_map))

        freq_list = [(char, self.compressor.frequency_map[char]) for char in self.compressor.frequency_map]
        freq_list.sort(key=lambda x: x[1], reverse=True)

        most_frequent = freq_list[0][0]
        least_frequent = freq_list[-1][0]
        self.assertLessEqual(len(codes[most_frequent]), len(codes[least_frequent]))
    
    def test_compression_decompression_cycle(self):
        """Prueba el ciclo completo de compresión y descompresión."""

        original_size, compressed_size = self.compressor.compress('test_file.txt', 'test_file')
        
        self.assertTrue(os.path.exists('test_file.huff'))
        self.assertTrue(os.path.exists('test_file.hufftree'))

        decompressed_text = self.compressor.decompress('test_file.huff', 'test_file.hufftree', 'test_file_decompressed.txt')

        self.assertEqual(decompressed_text, self.test_text)

        self.assertTrue(os.path.exists('test_file_decompressed.txt'))

        with open('test_file_decompressed.txt', 'r', encoding='utf-8') as file:
            file_content = file.read()

        self.assertEqual(file_content, self.test_text)

        if len(self.test_text) > 10:
            self.assertLess(compressed_size, original_size)


def main():
    compressor = HuffmanCompressor()
    
    while True:
        print("\nCompresor de Huffman")
        print("1. Comprimir archivo")
        print("2. Descomprimir archivo")
        print("3. Ejecutar pruebas unitarias")
        print("4. Salir")
        
        choice = input("Seleccione una opción: ")
        
        if choice == '1':
            input_file = input("Ingrese la ruta del archivo a comprimir: ")
            output_prefix = input("Ingrese el prefijo para los archivos de salida: ")
            
            try:
                start_time = time.time()
                original_size, compressed_size = compressor.compress(input_file, output_prefix)
                elapsed_time = time.time() - start_time
                
                compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                
                print(f"\nCompresión exitosa:")
                print(f"Tamaño original: {original_size} bytes")
                print(f"Tamaño comprimido: {compressed_size} bytes")
                print(f"Ratio de compresión: {compression_ratio:.2f}%")
                print(f"Tiempo de ejecución: {elapsed_time:.4f} segundos")
                print(f"\nArchivos generados:")
                print(f"- {output_prefix}.huff")
                print(f"- {output_prefix}.hufftree")
            except Exception as e:
                print(f"Error: {e}")
                
        elif choice == '2':
            huff_file = input("Ingrese la ruta del archivo .huff: ")
            hufftree_file = input("Ingrese la ruta del archivo .hufftree: ")
            output_file = input("Ingrese la ruta para el archivo descomprimido: ")
            
            try:
                start_time = time.time()
                decompressed_text = compressor.decompress(huff_file, hufftree_file, output_file)
                elapsed_time = time.time() - start_time
                
                print(f"\nDescompresión exitosa:")
                print(f"Archivo descomprimido guardado en: {output_file}")
                print(f"Tamaño descomprimido: {len(decompressed_text)} bytes")
                print(f"Tiempo de ejecución: {elapsed_time:.4f} segundos")
                
                preview_length = min(100, len(decompressed_text))
                print(f"\nVista previa del texto descomprimido:")
                print(f"{decompressed_text[:preview_length]}...")
            except Exception as e:
                print(f"Error: {e}")
                
        elif choice == '3':
            print("\nEjecutando pruebas unitarias...")
            unittest.main(argv=['first-arg-is-ignored'], exit=False)
            
        elif choice == '4':
            print("¡Adiós!")
            break
            
        else:
            print("Opción no válida. Intente de nuevo.")


if __name__ == "__main__":
    main()