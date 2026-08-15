import base64, os
class icon():   
    def __init__(self):
        self.icon_path = os.path.join(os.path.dirname(__file__), '../../res/icon/')
        self.icons = {}
        self.generate_icon()
          
    def set_base64_svg(self, icon_name):
            with open(self.icon_path + icon_name, 'r', encoding='utf-8') as svg_file:
                svg_content = svg_file.read()
            base64_svg = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')

            data_url = f"data:image/svg+xml;base64,{base64_svg}"
            return data_url
    
    def generate_icon(self):
         for icon_name in os.listdir(self.icon_path):
            self.icons[icon_name] = self.set_base64_svg(icon_name)
        