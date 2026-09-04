import json
from pathlib import Path


def test_glossary_configuration_exists_and_valid():
    config_path = Path("config/glossary.json")
    assert config_path.exists(), "config/glossary.json must exist"
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "motor-control" in data, "motor-control domain must be in glossary.json"
    assert "general-tech" in data, "general-tech domain must be in glossary.json"
    
    mc_terms = data["motor-control"]
    assert "foo c" in mc_terms or "foc" in mc_terms
    assert mc_terms.get("foo c") == "FOC" or mc_terms.get("foc") == "FOC"
    assert mc_terms.get("cooper mix") == "CubeMX"
    assert mc_terms.get("无法加") == "VOFA+"


def test_note_template_exists_and_has_required_sections():
    template_path = Path("templates/note_template.md")
    assert template_path.exists(), "templates/note_template.md must exist"
    
    content = template_path.read_text(encoding="utf-8")
    assert "{{title}}" in content or "# " in content
    assert "工具链" in content or "Toolchain" in content
    assert "核心" in content or "Concepts" in content
