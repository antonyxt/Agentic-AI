import re
import os
import chardet

def detect_encoding(path):
    with open(path, 'rb') as f:
        raw = f.read()
    result = chardet.detect(raw)
    encoding = result['encoding'] or 'utf-8'
    print(f"[📄] Encoding for {path}: {encoding}")
    return encoding

def modify_file(file_path, line_number, transform_fn):
    if not os.path.exists(file_path):
        print(f"[!] File not found: {file_path}")
        return

    encoding = detect_encoding(file_path)
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()

        if line_number < 1 or line_number > len(lines):
            print(f"[!] Line number out of range in {file_path}")
            return

        original_line = lines[line_number - 1]
        modified_line = transform_fn(original_line)

        if modified_line == original_line:
            print(f"[•] No change needed on line {line_number} in {file_path}")
            return

        lines[line_number - 1] = modified_line

        with open(file_path, 'w', encoding=encoding) as f:
            f.writelines(lines)

        print(f"[✓] Updated line {line_number} in {file_path}")
    except Exception as e:
        print(f"[!] Error processing {file_path}: {e}")

def handle_c4100(param_name, file_path, line_number):
    def transformer(line):
        return re.sub(rf'\b{param_name}\b', f'/*{param_name}*/', line)
    modify_file(file_path, line_number, transformer)

def handle_c4996(deprecated_symbol, replacement, file_path, line_number):
    func_name = deprecated_symbol.split("::")[-1]
    def transformer(line):
        return re.sub(rf'\b{func_name}\b', replacement, line)
    modify_file(file_path, line_number, transformer)

def process_warnings_from_string(warning_string):
    for line in warning_string.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        if "C4100" in line:
            match = re.search(r"C4100\s+'(\w+)'.*?([A-Z]:\\[^\s]+\.cpp)\s+(\d+)", line)
            if match:
                param = match.group(1)
                path = match.group(2)
                line_num = int(match.group(3))
                handle_c4100(param, path, line_num)
            else:
                print(f"[!] Invalid C4100 format: {line}")

        elif "C4996" in line:
            # Match pattern like: 'Class::Function': Use newFunction() instead
            match = re.search(r"C4996\s+'([\w:]+)'.*?Use\s+([\w:]+)\(\)", line)
            path_match = re.search(r"([A-Z]:\\[^\s]+\.cpp)\s+(\d+)", line)
            if match and path_match:
                deprecated_symbol = match.group(1)
                replacement = match.group(2)
                path = path_match.group(1)
                line_num = int(path_match.group(2))
                handle_c4996(deprecated_symbol, replacement, path, line_num)
            else:
                print(f"[!] Invalid C4996 format: {line}")
        else:
            print(f"[i] Skipping non-matching warning: {line}")

# ✅ Example multi-line warning input
warnings_input = r"""
Warning	C4996	'QDateTime::QDateTime': Pass QTimeZone instead	ApplicationFramework	C:\CZ\zui\ZUi-Integration\ApplicationFramework\Source\DomainDataToQtTypeConverter.cpp	42		
Warning	C4996	'QLocale::nativeCountryName': Use nativeTerritoryName() instead	ApplicationFramework	C:\CZ\zui\ZUi-Integration\ApplicationFramework\Source\TranslationManager.cpp	88		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\MovableModePinCheckView.cpp	41		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\NetworkSettingsView.cpp	61		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\NetworkSettingsView.cpp	62		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientExportView.cpp	272		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientExportView.cpp	273		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientExportView.cpp	274		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientManagementView.cpp	600		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientManagementView.cpp	601		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientManagementView.cpp	602		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientManagementView.cpp	603		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientManagementView.cpp	604		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientManagementView.cpp	605		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientManagementView.cpp	607		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientManagementView.cpp	608		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientManagementView.cpp	609		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientManagementView.cpp	611		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientManagementView.cpp	612		
Warning	C4996	'QCheckBox::stateChanged': Use checkStateChanged() instead	PlanningAssistantViews	C:\CZ\zui\ZUi-Integration\PlanningAssistantViews\Source\Views\PatientManagementView.cpp	613		
Warning	C4996	'QLocale::countryToString': Use territoryToString(Territory) instead	PlanningAssistant.Test	C:\CZ\zui\ZUi-Integration\PlanningAssistant\Source\Presenters\UserSettingsPresenter.cpp	577		
Warning	C4996	'QLocale::country': Use territory() instead	PlanningAssistant.Test	C:\CZ\zui\ZUi-Integration\PlanningAssistant\Source\Presenters\UserSettingsPresenter.cpp	686		
Warning	C4996	'QLocale::country': Use territory() instead	PlanningAssistantModels	C:\CZ\zui\ZUi-Integration\PlanningAssistantModels\Source\Models\UserSettingsModel.cpp	404		
Warning	C4996	'QLocale::country': Use territory() instead	PlanningAssistantModels.Test	C:\CZ\zui\ZUi-Integration\PlanningAssistantModels\Source\Models\UserSettingsModel.cpp	404		
Warning	C4996	'QLocale::country': Use territory() instead	PlanningAssistant.Test	C:\CZ\zui\ZUi-Integration\PlanningAssistant.Test\Source\Tests\UserSettingsPresenterTest.cpp	854		
Warning	C4996	'QLocale::country': Use territory() instead	PlanningAssistant.Test	C:\CZ\zui\ZUi-Integration\PlanningAssistant.Test\Source\Tests\UserSettingsPresenterTest.cpp	856		
Warning	C4996	'QLocale::countryToString': Use territoryToString(Territory) instead	PlanningAssistant	C:\CZ\zui\ZUi-Integration\PlanningAssistant\Source\Presenters\UserSettingsPresenter.cpp	577		
Warning	C4996	'QLocale::country': Use territory() instead	PlanningAssistant	C:\CZ\zui\ZUi-Integration\PlanningAssistant\Source\Presenters\UserSettingsPresenter.cpp	686		
Warning	C4996	'QDateTime::QDateTime': Pass QTimeZone instead	PlanningAssistantModels.Test	C:\CZ\zui\ZUi-Integration\PlanningAssistantModels.Test\Source\Tests\PatientDetailsModelTest.cpp	1923		
Warning	C4996	'QDateTime::QDateTime': Pass QTimeZone instead	PlanningAssistantModels.Test	C:\CZ\zui\ZUi-Integration\PlanningAssistantModels.Test\Source\Tests\SessionKeyTest.cpp	46		
Warning	C4996	'QDateTime::QDateTime': Pass QTimeZone instead	PlanningAssistantModels.Test	C:\CZ\zui\ZUi-Integration\PlanningAssistantModels.Test\Source\Tests\SessionKeyTest.cpp	53		
Warning	C4996	'QDateTime::QDateTime': Pass QTimeZone instead	PlanningAssistantModels.Test	C:\CZ\zui\ZUi-Integration\PlanningAssistantModels.Test\Source\Tests\SessionKeyTest.cpp	56		
Warning	C4996	'QDateTime::QDateTime': Pass QTimeZone instead	PlanningAssistantModels.Test	C:\CZ\zui\ZUi-Integration\PlanningAssistantModels.Test\Source\Tests\SessionKeyTest.cpp	59		
Warning	C4996	'QDateTime::QDateTime': Pass QTimeZone instead	PlanningAssistantModels.Test	C:\CZ\zui\ZUi-Integration\PlanningAssistantModels.Test\Source\Tests\SessionKeyTest.cpp	62		
Warning	C4996	'QLocale::country': Use territory() instead	PlanningAssistantModels.Test	C:\CZ\zui\ZUi-Integration\PlanningAssistantModels.Test\Source\Tests\StartModelTest.cpp	806	
"""

process_warnings_from_string(warnings_input)
