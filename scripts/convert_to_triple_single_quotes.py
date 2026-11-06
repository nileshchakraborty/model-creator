import glob
import re

for p in sorted(glob.glob('/Users/nileshchakraborty/workspace/model-creator/curriculum/*.py')):
    if p.endswith('__init__.py') or p.endswith('verifier.py'):
        continue
    with open(p, 'r') as f:
        text = f.read()

    # In each file, response blocks start with: r_var = r""" or r_var = """
    # and end with ```"""
    # We want to change the outer delimiter to r'''...```'''
    # and change any \"\"\" back to normal """
    
    lines = text.split('\n')
    fixed_lines = []
    in_r_block = False
    
    for line in lines:
        if re.match(r'^\s*r[_\w]*\s*=\s*r?\"\"\"', line):
            in_r_block = True
            # Change start from r""" or """ to r'''
            var_name = line.split('=')[0].strip()
            indent = line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}{var_name} = r'''")
        elif in_r_block and line.strip().endswith('```"""'):
            in_r_block = False
            # Change end from ```""" to ```'''
            indent = line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}```'''")
        elif in_r_block:
            # Replace \"\"\" with """
            fixed_lines.append(line.replace('\\"\\"\\"', '"""'))
        else:
            fixed_lines.append(line)

    new_text = '\n'.join(fixed_lines)
    with open(p, 'w') as f:
        f.write(new_text)

print("Check syntax:")
for p in sorted(glob.glob('/Users/nileshchakraborty/workspace/model-creator/curriculum/*.py')):
    try:
        with open(p) as f:
            compile(f.read(), p, 'exec')
        print(f'{p}: VALID SYNTAX')
    except SyntaxError as e:
        print(f'{p}: SYNTAX ERROR line {e.lineno}: {e.msg}')
