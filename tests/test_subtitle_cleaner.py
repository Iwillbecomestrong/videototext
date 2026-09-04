import pytest
from scripts.subtitle_cleaner import SubtitleCleaner


@pytest.fixture
def sample_glossary():
    return {
        "motor-control": {
            "foo c": "FOC",
            "foc": "FOC",
            "cooper mix": "CubeMX",
            "cubemx": "CubeMX",
            "无法加": "VOFA+",
            "j link": "J-Link",
            "clark变换": "Clarke变换",
            "sv pwm": "SVPWM",
            "马鞍波": "马鞍波",
            "p i": "PI",
            "g p i o": "GPIO",
        }
    }


def test_clean_text_phrase_and_single_word(sample_glossary):
    cleaner = SubtitleCleaner(glossary=sample_glossary, domain="motor-control")
    raw_text = "今天我们讲一下 foo c 算法，配合 cooper mix 进行配置，最后用 无法加 观察波形。"
    cleaned, matches = cleaner.clean_text(raw_text)
    
    assert "FOC" in cleaned
    assert "CubeMX" in cleaned
    assert "VOFA+" in cleaned
    assert "foo c" not in cleaned
    assert "cooper mix" not in cleaned
    assert "无法加" not in cleaned
    
    term_map = {m["original"].lower(): m["replacement"] for m in matches}
    assert term_map.get("foo c") == "FOC"
    assert term_map.get("cooper mix") == "CubeMX"
    assert term_map.get("无法加") == "VOFA+"


def test_clean_text_case_insensitivity(sample_glossary):
    cleaner = SubtitleCleaner(glossary=sample_glossary, domain="motor-control")
    raw = "foc in lower and FOC in upper and Foo C mixed"
    cleaned, _ = cleaner.clean_text(raw)
    assert "FOC in lower and FOC in upper and FOC mixed" == cleaned


def test_clean_srt_preserves_timestamps_and_indices(sample_glossary):
    cleaner = SubtitleCleaner(glossary=sample_glossary, domain="motor-control")
    raw_srt = """1
00:00:01,000 --> 00:00:03,500
欢迎来到 foo c 课程

2
00:00:04,000 --> 00:00:07,200
打开 cooper mix 配置 g p i o

3
00:00:08,000 --> 00:00:11,000
使用 无法加 观察 sv pwm 波形
"""
    cleaned_srt, matches = cleaner.clean_srt(raw_srt)
    
    # Verify timestamps are completely preserved
    assert "00:00:01,000 --> 00:00:03,500" in cleaned_srt
    assert "00:00:04,000 --> 00:00:07,200" in cleaned_srt
    assert "00:00:08,000 --> 00:00:11,000" in cleaned_srt
    
    # Verify content updated
    assert "欢迎来到 FOC 课程" in cleaned_srt
    assert "打开 CubeMX 配置 GPIO" in cleaned_srt
    assert "使用 VOFA+ 观察 SVPWM 波形" in cleaned_srt
    
    assert len(matches) >= 4


def test_clean_empty_or_malformed_srt(sample_glossary):
    cleaner = SubtitleCleaner(glossary=sample_glossary)
    assert cleaner.clean_srt("") == ("", [])
    assert cleaner.clean_text("") == ("", [])
