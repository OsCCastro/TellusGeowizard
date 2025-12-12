#!/usr/bin/env python3
"""
Script para reemplazar QMessageBox con CustomMessageBox en main_window.py
"""

import re

# Archivo a modificar
file_path = r"a:\Windows\Usuarios\ContrerasO\Escritorio\GeoWizard\ui\main_window.py"

# Leer el archivo
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Contador de reemplazos
replacements = 0

# 1. Reemplazar QMessageBox.information()
pattern1 = r'QMessageBox\.information\s*\('
replacement1 = 'CustomMessageBox.information('
content, count1 = re.subn(pattern1, replacement1, content)
replacements += count1
print(f"Reemplazados {count1} usos de QMessageBox.information()")

# 2. Reemplazar QMessageBox.warning()
pattern2 = r'QMessageBox\.warning\s*\('
replacement2 = 'CustomMessageBox.warning('
content, count2 = re.subn(pattern2, replacement2, content)
replacements += count2
print(f"Reemplazados {count2} usos de QMessageBox.warning()")

# 3. Reemplazar QMessageBox.critical()
pattern3 = r'QMessageBox\.critical\s*\('
replacement3 = 'CustomMessageBox.critical('
content, count3 = re.subn(pattern3, replacement3, content)
replacements += count3
print(f"Reemplazados {count3} usos de QMessageBox.critical()")

# 4. Reemplazar QMessageBox.question()
pattern4 = r'QMessageBox\.question\s*\('
replacement4 = 'CustomMessageBox.question('
content, count4 = re.subn(pattern4, replacement4, content)
replacements += count4
print(f"Reemplazados {count4} usos de QMessageBox.question()")

# 5. Reemplazar las constantes de botones
button_replacements = [
    (r'QMessageBox\.Yes', 'CustomMessageBox.Yes'),
    (r'QMessageBox\.No', 'CustomMessageBox.No'),
    (r'QMessageBox\.Ok', 'CustomMessageBox.Ok'),
    (r'QMessageBox\.Cancel', 'CustomMessageBox.Cancel'),
]

for pattern, replacement in button_replacements:
    content, count = re.subn(pattern, replacement, content)
    if count > 0:
        print(f"Reemplazados {count} usos de {pattern}")
    replacements += count

# Escribir el archivo modificado
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Total de reemplazos: {replacements}")
print(f"Archivo modificado: {file_path}")
