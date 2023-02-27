from components.administration.forms import PreconfiguredChoices

EXPECTED_PROCESSING_CONFIGURATION = """
<processingMCP>
  <preconfiguredChoices>
    <!-- 病毒扫描：是 -->
    <preconfiguredChoice>
      <appliesTo>97a5ddc0-d4e0-43ac-a571-9722405a0a9b</appliesTo>
      <goToChain>3e8c0c39-3f30-4c9b-a449-85eef1b2a458</goToChain>
    </preconfiguredChoice>
  </preconfiguredChoices>
</processingMCP>
"""


def test_PreconfiguredChoices_saves_file(tmp_path):
    f = tmp_path / "myProcessingMCP.xml"
    form = PreconfiguredChoices()
    form.add_choice(
        applies_to_text="97a5ddc0-d4e0-43ac-a571-9722405a0a9b",
        go_to_chain_text="3e8c0c39-3f30-4c9b-a449-85eef1b2a458",
        comment="病毒扫描：是",
    )
    form.save(f)
    assert f.read_text().strip() == EXPECTED_PROCESSING_CONFIGURATION.strip()
