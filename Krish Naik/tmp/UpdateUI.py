import xml.etree.ElementTree as ET
import os

class UIUpdater:
    def __init__(self, ui_file_path, update_file_list):
        # Hardcoded file path
        self.ui_file_path = ui_file_path
        # Hardcoded file paths
        self.update_file_list = update_file_list
        self.variable_names = {}
        # Key-value pair where key is the property name and value is the property value
        self.new_properties = {}
        # Key-value pair where key is the old property name and value is the new property name
        self.rename_properties = {}
        # List of property names to be removed
        self.remove_properties = []
        # Variable name prefix appended to the object name
        self.variable_name_prefix = ""
        # Append class headers for form container
        self.form_container_header = ""
        # Append class headers for input stepper
        self.input_stepper_header = ""
    
    def read_ui_file(self):
        with open(self.ui_file_path, "r", encoding="UTF-8") as file:
            return file.read()
    
    def prettify_xml(self, root):
        """Formats the XML output with proper indentation."""
        import xml.dom.minidom
        #xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")  # Ensure we decode bytes to string
        parsed = xml.dom.minidom.parseString(root)
        return parsed.toprettyxml(indent=" ", encoding="UTF-8").decode("UTF-8")
    
    def write_ui_file(self, content):
        with open(self.ui_file_path, "w", encoding="UTF-8") as file:
            file.write(self.prettify_xml(content))
    
    def initialize_form_container_updates(self, widget):
        widget.set("class", "zui::components::FormContainer")
        caption = widget.find("property[@name=\"Caption\"]")
        caption_attribute = caption.find("string")
        
        # Add new properties
        self.new_properties = {
            ("formContainerInputType", "<enum>zui::Types::ZuiFormContainerInputType::ZuiInputStepper</enum>"),
            ("labelText", f"<string>{caption_attribute.text}</string>"),
            ("sizePolicy", "<sizepolicy hsizetype=\"Preferred\" vsizetype=\"Maximum\"><horstretch>0</horstretch><verstretch>0</verstretch></sizepolicy>"),
        }
        # Rename property
        self.rename_properties = {}
        # Remove all properties
        self.remove_properties = [prop.get("name") for prop in widget.findall("property")]
        # Variable name prefix appended to the object name
        self.variable_name_prefix = "zuiFormContainer"
        # Append class headers
        self.form_container_header = "<customwidget><class>zui::components::FormContainer</class><extends>QFrame</extends><header>ZUiQtWidgets/Components/FormContainer.h</header></customwidget>"
    
    def initialize_input_stepper_updates(self, widget):
        widget.set("class", "zui::components::InputStepper")
        # Add new properties
        self.new_properties = {
            ("zuiInputStepperType", "<enum>zui::Types::ZuiInputStepperType::ZuiInputStepperInputField</enum>"),
            ("showButtons", "<bool>false</bool>"),
            ("alignRight", "<bool>true</bool>")
        }
        # Rename property
        self.rename_properties = {    
            "suffix": "unit",
            "decimals": "decimalPlaces",
            "maximum": "upperValue",
            "value": "currentValue",
        }
        # Remove all properties
        self.remove_properties = ["locale", "Caption"]
        # Variable name prefix appended to the object name
        self.variable_name_prefix = "zuiInputStepper"
        # Append class headers
        self.input_stepper_header = "<customwidget><class>zui::components::InputStepper</class><extends>QFrame</extends><header>ZUiQtWidgets/Components/InputStepper.h</header><container>1</container></customwidget>"
    
    def print_widget_properties(self, widget, new_name):
        
        displayString = f"Property name,{new_name}"
        # print unit with property name
        if widget.find(f"property[@name='Suffix']") is not None:
            suffix = widget.find(f"property[@name='Suffix']").find("string")
            displayString = displayString + f", Unit, {suffix.text}"
        # print decimals with property name
        if widget.find(f"property[@name='decimals']") is not None:
            decimals = widget.find(f"property[@name='decimals']").find("number")
            displayString = displayString + f", decimals, {decimals.text}"
        print(displayString)
    def modify_widget(self, widget):
        if widget.get("class") == "czm::neo::custom_widgets::widgets::NumberInput":
            caption_property = widget.find("property[@name=\"Caption\"]")
            caption_string = ""
            if caption_property is not None:
                caption_string_attribute = caption_property.find("string")
                if caption_string_attribute is not None:
                    caption_string = caption_string_attribute.text
            
            if caption_string:
                self.initialize_form_container_updates(widget)
            else:
                self.initialize_input_stepper_updates(widget)
            old_name = widget.get("name")
            new_name = ""
            if old_name:
                if old_name.startswith("lineEdit"):
                    new_name = self.variable_name_prefix + old_name[len("lineEdit"):]
                elif old_name.startswith("numberInput"):
                    new_name = self.variable_name_prefix + old_name[len("numberInput"):]
                else:
                    new_name = self.variable_name_prefix + old_name
                widget.set("name", new_name)
                self.print_widget_properties(widget, new_name)                
                self.variable_names[old_name] = new_name

            for prop in list(widget.findall("property")):
                property_name = prop.get("name").lower()
                if self.rename_properties.get(property_name) is not None:
                    prop.set("name", self.rename_properties.get(property_name))
                elif prop.get("name") in self.remove_properties:
                    widget.remove(prop)
            for name, value in self.new_properties:
                if not widget.find(f"property[@name='{name}']"):
                    prop = ET.Element("property", name=name)
                    prop.append(ET.fromstring(value))
                    widget.append(prop)
    
    def update_tabstops(self, root):
        for tabstop in root.findall(".//tabstop"):
            if self.variable_names.get(tabstop.text) is not None:
                tabstop.text = self.variable_names.get(tabstop.text)
    
    def update_custom_widgets(self, root):
        custom_widgets = root.find("customwidgets")
        if custom_widgets is not None:
            widget_to_remove = custom_widgets.find(".//customwidget[class='czm::neo::custom_widgets::widgets::NumberInput']")
            if widget_to_remove is not None:
                custom_widgets.remove(widget_to_remove)
            if self.form_container_header:
                custom_widgets.append(ET.fromstring(self.form_container_header))
            if self.input_stepper_header:
                custom_widgets.append(ET.fromstring(self.input_stepper_header))
    
    def modify_ui_content(self, content):
        root = ET.fromstring(content)
        for widget in root.findall(".//widget"):
            self.modify_widget(widget)
        self.update_custom_widgets(root)
        self.update_tabstops(root)
        return root
    
    def modify_cpp_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                lines = file.readlines()
            modified_lines = []
            for line in lines:
                for old_name, new_name in self.variable_names.items():
                    line = line.replace(old_name, new_name)
                modified_lines.append(line)

            with open(filepath, "w", encoding="utf-8") as file:
                file.writelines(modified_lines)
        except Exception as e:
            print(f"Error modifying file '{filepath}': {e}")
    
    def run(self):
        original_content = self.read_ui_file()
        root = self.modify_ui_content(original_content)
        xml_str = ET.tostring(root, encoding="unicode").splitlines()
        truncatedLines = [str.strip() for str in xml_str]
        xml_str = ''.join(truncatedLines)
        # self.write_ui_file(xml_str)
        # for file_name in self.update_file_list: self.modify_cpp_file(file_name)
        #print(self.prettify_xml(xml_str))
        print("Modification completed successfully.")


if __name__ == "__main__":
    updater = UIUpdater(r"C:\CZ\zui\ZUi-Integration\FemtoPlanningViews\Source\Views\TreatmentPlanningSmilePanelView.ui", 
                        [
                            r"C:\CZ\zui\ZUi-Integration\FemtoPlanningViews\Source\Views\TreatmentPlanningSmilePanelView.cpp",
                            r"C:\CZ\zui\ZUi-Integration\FemtoPlanningViews\Source\Views\TreatmentPlanningSmilePanelView.h"
                        ])
    updater.run()
