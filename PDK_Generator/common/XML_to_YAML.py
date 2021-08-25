## XML to YAML Parser
#  WARNING: MANUAL EDITTING REQUIRED TO CONVERT THE OUTPUT TO PDK-GENERATOR
#           YAML FORMAT.
# 
#  PLEASE USE https://onlineyamltools.com/convert-xml-to-yaml INSTEAD

import xml.etree.ElementTree as ET

tree = ET.parse("Technology.lyt")
root = tree.getroot()
yaml_file = []

def create_subelement(yaml, root, subelement, indentations):
    num_children = len(subelement)
    if num_children == 0:
        yaml.append("  "*(indentations+1) + "{}: {}".format(subelement.tag, subelement.text))
    elif num_children > 0:
        yaml.append("  "*(indentations+1) + "{}:".format(subelement.tag))
        for child in subelement:
            create_subelement(yaml, subelement, child, indentations+1)

create_subelement(yaml_file, None, root, 0)

with open('xml_to_yaml.yaml', 'w') as writer:    
    for line in yaml_file:
        writer.write(line+"\n")
        print(line)
