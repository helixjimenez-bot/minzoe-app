"""
Fix HVAC Phase 1 form double-click issue.

Problem:
  - st.stop() inside with st.form() clears form values when validation fails
  - After setting _hvac_raw_key, no st.rerun() → user must click again to see Phase 2

Fix:
  1. Replace st.stop() with else: block (wrap HTML generation in else)
  2. Add st.rerun() after saving _hvac_raw_key so Phase 2 appears immediately
"""

with open('solicitudes_minzoe.py', encoding='utf-8') as f:
    lines = f.readlines()

# Line numbers (1-indexed):
# 4576: "                                    st.stop()"  ← inside if _campos_vacios:
# 4577: "                                tipo_mto = ..."  ← start of HTML generation (32 spaces indent)
# 4833: "                                st.session_state[f\"hvac_fec_{id_ot_sel}\"] = ..."
# 4834: blank line

STOP_LINE    = 4576  # line with st.stop() to remove
ELSE_INSERT  = 4577  # insert "else:" before this line (after removing stop)
RERUN_AFTER  = 4833  # insert st.rerun() after this line
INDENT_FROM  = 4577  # first line to add 4 spaces
INDENT_TO    = 4833  # last line to add 4 spaces (inclusive)

result = []
i = 0
rerun_inserted = False

while i < len(lines):
    lineno = i + 1
    line = lines[i]

    # Step 1: Remove st.stop() at line 4576
    if lineno == STOP_LINE:
        stripped = line.strip()
        if stripped == 'st.stop()':
            # Replace with 'else:' at the same base indent (32 spaces = 8 * 4)
            base_indent = ' ' * 32
            result.append(base_indent + 'else:\n')
            i += 1
            continue
        else:
            print(f"WARNING: Expected 'st.stop()' at line {lineno}, got: {repr(stripped)}")

    # Step 2: Add 4 spaces to lines in range INDENT_FROM..INDENT_TO
    if INDENT_FROM <= lineno <= INDENT_TO:
        stripped = line.rstrip('\n').lstrip()
        if stripped:  # non-blank line
            result.append('    ' + line)
        else:
            result.append(line)
        # Step 3: After RERUN_AFTER, insert st.rerun()
        if lineno == RERUN_AFTER:
            result.append(' ' * 36 + 'st.rerun()\n')
            rerun_inserted = True
        i += 1
        continue

    result.append(line)
    i += 1

print(f"st.rerun() inserted: {rerun_inserted}")

with open('solicitudes_minzoe.py', 'w', encoding='utf-8') as f:
    f.writelines(result)

import ast
try:
    src = open('solicitudes_minzoe.py', encoding='utf-8').read()
    ast.parse(src)
    print("OK - sintaxis correcta")
except SyntaxError as e:
    print(f"Error linea {e.lineno}: {e.msg}")
    src_lines = src.splitlines()
    for j in range(max(0, e.lineno-4), min(len(src_lines), e.lineno+3)):
        print(f"  {j+1}: {src_lines[j]}")
