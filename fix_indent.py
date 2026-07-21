
with open('solicitudes_minzoe.py', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the indentation issue around line 6703
# The for loop body needs 4 more spaces
in_fix_zone = False
old_for_indent = None
new_lines = []

for i, line in enumerate(lines):
    ln = line.rstrip('\n')

    # Detect the problematic for loop
    if '                    for idx_eq, (_, _eq) in enumerate(_ac_detalle.iterrows()):' in ln and in_fix_zone is False:
        in_fix_zone = True
        old_for_indent = len(ln) - len(ln.lstrip())
        new_lines.append(line)
        continue

    if in_fix_zone:
        stripped = ln.lstrip()
        current_indent = len(ln) - len(stripped)

        # Stop when we find a line at same or less indent as the for loop (or another elif/else)
        if stripped and current_indent <= old_for_indent and not stripped.startswith('#'):
            in_fix_zone = False
            new_lines.append(line)
            continue

        # Add 4 spaces to body lines
        if stripped:  # non-empty line
            new_lines.append(' ' * 4 + line)
        else:
            new_lines.append(line)
        continue

    new_lines.append(line)

with open('solicitudes_minzoe.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

import ast
try:
    ast.parse(open('solicitudes_minzoe.py', encoding='utf-8').read())
    print("OK - sintaxis correcta")
except SyntaxError as e:
    print(f"Error en linea {e.lineno}: {e.msg}")
