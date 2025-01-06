from pathlib import Path

def view_code():
    dir = Path(__file__).resolve().parent
    html = open(f"{dir}/../../res/templates/index.html",'r')
    code = ''

    for line in html:

        if line[0:7] == '</body>':
            code += '<script>\n'
            code += read(f"{dir}/../../res/static/script.js")
            code += '</script>\n' 

        elif line[0:7] == '</head>':
            code += '<style>\n'
            code += read(f"{dir}/../../res/static/styles.css")
            code += '</style>\n'

        code += line

    html.close()
    return code

def read(path):
    code = ''
    with open(path,'r') as file:
        for line in file:
            code += "   " + line
    return code 
