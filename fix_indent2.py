
with open('solicitudes_minzoe.py', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the for loop body indentation around line 6701
# The for statement is at indent=20 spaces (inside the `if _activo:` block)
# The body lines need to be at indent=24 spaces
# Find the problematic for loop

result = []
i = 0
while i < len(lines):
    line = lines[i]
    # Detect the for loop with wrong indentation
    stripped = line.rstrip('\n').lstrip()
    indent = len(line.rstrip('\n')) - len(stripped)

    if (stripped.startswith('for idx_eq, (_, _eq) in enumerate(_ac_detalle.iterrows()):')
            and indent == 20):
        result.append(line)  # keep the for statement as-is
        i += 1
        # Now fix the body: lines that have indent <= 20 need 4 more spaces
        # until we hit a line at same or less indent as the for (that's not a continuation)
        while i < len(lines):
            body_line = lines[i]
            body_stripped = body_line.rstrip('\n').lstrip()
            body_indent = len(body_line.rstrip('\n')) - len(body_stripped)

            if not body_stripped:  # blank line
                result.append(body_line)
                i += 1
                continue

            # Stop if we reach a line that's at same indent as the for (20) or less
            # AND is not something that belongs to the body
            if body_indent <= 20 and body_stripped and not body_stripped.startswith('#'):
                break

            # Add 4 spaces to bring body to correct indent (24)
            if body_indent < 24 and body_stripped:
                result.append('    ' + body_line)
            else:
                result.append(body_line)
            i += 1
        continue

    result.append(line)
    i += 1

with open('solicitudes_minzoe.py', 'w', encoding='utf-8') as f:
    f.writelines(result)

import ast
try:
    ast.parse(open('solicitudes_minzoe.py', encoding='utf-8').read())
    print("OK - sintaxis correcta")
except SyntaxError as e:
    print(f"Error linea {e.lineno}: {e.msg}")
    # Show context
    lines2 = open('solicitudes_minzoe.py', encoding='utf-8').readlines()
    for j in range(max(0,e.lineno-3), min(len(lines2), e.lineno+3)):
        print(f"  {j+1}: {lines2[j]}", end='')
