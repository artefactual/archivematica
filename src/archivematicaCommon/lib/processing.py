"""Manage MCP processing configuration.

This is mostly responsiblity of MCPServer but it's here as a shared module so
the dashboard can reset the documents. Long-term solution should probably
avoid sharing the code, e.g. let MCPServer handle it and expose the
functionality via RPC as we do in other situations (see ``RPCServer``).
"""

import os

from django.conf import settings as django_settings


DEFAULT_PROCESSING_CONFIG = u"""<processingMCP>
  <preconfiguredChoices>
    <!-- Select compression level -->
    <preconfiguredChoice>
      <appliesTo>01c651cb-c174-4ba4-b985-1d87a44d6754</appliesTo>
      <goToChain>414da421-b83f-4648-895f-a34840e3c3f5</goToChain>
    </preconfiguredChoice>
    <!-- Examine contents -->
    <preconfiguredChoice>
      <appliesTo>accea2bf-ba74-4a3a-bb97-614775c74459</appliesTo>
      <goToChain>e0a39199-c62a-4a2f-98de-e9d1116460a8</goToChain>
    </preconfiguredChoice>
    <!-- Remove from quarantine after (days) -->
    <preconfiguredChoice>
      <appliesTo>19adb668-b19a-4fcb-8938-f49d7485eaf3</appliesTo>
      <goToChain>333643b7-122a-4019-8bef-996443f3ecc5</goToChain>
      <delay unitCtime="yes">2419200.0</delay>
    </preconfiguredChoice>
    <!-- Select compression algorithm -->
    <preconfiguredChoice>
      <appliesTo>01d64f58-8295-4b7b-9cab-8f1b153a504f</appliesTo>
      <goToChain>9475447c-9889-430c-9477-6287a9574c5b</goToChain>
    </preconfiguredChoice>
    <!-- Bind PIDs -->
    <preconfiguredChoice>
      <appliesTo>05357876-a095-4c11-86b5-a7fff01af668</appliesTo>
      <goToChain>fcfea449-158c-452c-a8ad-4ae009c4eaba</goToChain>
    </preconfiguredChoice>
    <!-- Transcribe files (OCR) -->
    <preconfiguredChoice>
      <appliesTo>7079be6d-3a25-41e6-a481-cee5f352fe6e</appliesTo>
      <goToChain>1170e555-cd4e-4b2f-a3d6-bfb09e8fcc53</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Transfer) -->
    <preconfiguredChoice>
      <appliesTo>f09847c2-ee51-429a-9478-a860477f6b8d</appliesTo>
      <goToChain>bed4eeb1-d654-4d97-b98d-40eb51d3d4bb</goToChain>
    </preconfiguredChoice>
    <!-- Store DIP location -->
    <preconfiguredChoice>
      <appliesTo>cd844b6e-ab3c-4bc6-b34f-7103f88715de</appliesTo>
      <goToChain>/api/v2/location/default/DS/</goToChain>
    </preconfiguredChoice>
    <!-- Generate transfer structure report -->
    <preconfiguredChoice>
      <appliesTo>56eebd45-5600-4768-a8c2-ec0114555a3d</appliesTo>
      <goToChain>df54fec1-dae1-4ea6-8d17-a839ee7ac4a7</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on originals -->
    <preconfiguredChoice>
      <appliesTo>70fc7040-d4fb-4d19-a0e6-792387ca1006</appliesTo>
      <goToChain>3e891cc4-39d2-4989-a001-5107a009a223</goToChain>
    </preconfiguredChoice>
    <!-- Reminder: add metadata if desired -->
    <preconfiguredChoice>
      <appliesTo>eeb23509-57e2-4529-8857-9d62525db048</appliesTo>
      <goToChain>5727faac-88af-40e8-8c10-268644b0142d</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on access derivatives -->
    <preconfiguredChoice>
      <appliesTo>8ce07e94-6130-4987-96f0-2399ad45c5c2</appliesTo>
      <goToChain>76befd52-14c3-44f9-838f-15a4e01624b0</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Ingest) -->
    <preconfiguredChoice>
      <appliesTo>7a024896-c4f7-4808-a240-44c87c762bc5</appliesTo>
      <goToChain>3c1faec7-7e1e-4cdd-b3bd-e2f05f4baa9b</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on preservation derivatives -->
    <preconfiguredChoice>
      <appliesTo>153c5f41-3cfb-47ba-9150-2dd44ebc27df</appliesTo>
      <goToChain>b7ce05f0-9d94-4b3e-86cc-d4b2c6dba546</goToChain>
    </preconfiguredChoice>
    <!-- Assign UUIDs to directories -->
    <preconfiguredChoice>
      <appliesTo>bd899573-694e-4d33-8c9b-df0af802437d</appliesTo>
      <goToChain>2dc3f487-e4b0-4e07-a4b3-6216ed24ca14</goToChain>
    </preconfiguredChoice>
    <!-- Store AIP location -->
    <preconfiguredChoice>
      <appliesTo>b320ce81-9982-408a-9502-097d0daa48fa</appliesTo>
      <goToChain>/api/v2/location/default/AS/</goToChain>
    </preconfiguredChoice>
    <!-- Document empty directories -->
    <preconfiguredChoice>
      <appliesTo>d0dfa5fc-e3c2-4638-9eda-f96eea1070e0</appliesTo>
      <goToChain>29881c21-3548-454a-9637-ebc5fd46aee0</goToChain>
    </preconfiguredChoice>
    <!-- Send transfer to quarantine -->
    <preconfiguredChoice>
      <appliesTo>755b4177-c587-41a7-8c52-015277568302</appliesTo>
      <goToChain>d4404ab1-dc7f-4e9e-b1f8-aa861e766b8e</goToChain>
    </preconfiguredChoice>
    <!-- Extract packages -->
    <preconfiguredChoice>
      <appliesTo>dec97e3c-5598-4b99-b26e-f87a435a6b7f</appliesTo>
      <goToChain>01d80b27-4ad1-4bd1-8f8d-f819f18bf685</goToChain>
    </preconfiguredChoice>
  </preconfiguredChoices>
</processingMCP>
"""

AUTOMATED_PROCESSING_CONFIG = """<processingMCP>
  <preconfiguredChoices>
    <!-- Store DIP -->
    <preconfiguredChoice>
      <appliesTo>5e58066d-e113-4383-b20b-f301ed4d751c</appliesTo>
      <goToChain>8d29eb3d-a8a8-4347-806e-3d8227ed44a1</goToChain>
    </preconfiguredChoice>
    <!-- Select compression level -->
    <preconfiguredChoice>
      <appliesTo>01c651cb-c174-4ba4-b985-1d87a44d6754</appliesTo>
      <goToChain>414da421-b83f-4648-895f-a34840e3c3f5</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Submission documentation & metadata) -->
    <preconfiguredChoice>
      <appliesTo>087d27be-c719-47d8-9bbb-9a7d8b609c44</appliesTo>
      <goToChain>25a91595-37f0-4373-a89a-56a757353fb8</goToChain>
    </preconfiguredChoice>
    <!-- Examine contents -->
    <preconfiguredChoice>
      <appliesTo>accea2bf-ba74-4a3a-bb97-614775c74459</appliesTo>
      <goToChain>e0a39199-c62a-4a2f-98de-e9d1116460a8</goToChain>
    </preconfiguredChoice>
    <!-- Select compression algorithm -->
    <preconfiguredChoice>
      <appliesTo>01d64f58-8295-4b7b-9cab-8f1b153a504f</appliesTo>
      <goToChain>9475447c-9889-430c-9477-6287a9574c5b</goToChain>
    </preconfiguredChoice>
    <!-- Normalize (match 1 for "Normalize for preservation") -->
    <preconfiguredChoice>
      <appliesTo>cb8e5706-e73f-472f-ad9b-d1236af8095f</appliesTo>
      <goToChain>612e3609-ce9a-4df6-a9a3-63d634d2d934</goToChain>
    </preconfiguredChoice>
    <!-- Normalize (match 2 for "Normalize for preservation") -->
    <preconfiguredChoice>
      <appliesTo>7509e7dc-1e1b-4dce-8d21-e130515fce73</appliesTo>
      <goToChain>612e3609-ce9a-4df6-a9a3-63d634d2d934</goToChain>
    </preconfiguredChoice>
    <!-- Bind PIDs -->
    <preconfiguredChoice>
      <appliesTo>05357876-a095-4c11-86b5-a7fff01af668</appliesTo>
      <goToChain>fcfea449-158c-452c-a8ad-4ae009c4eaba</goToChain>
    </preconfiguredChoice>
    <!-- Create SIP(s) -->
    <preconfiguredChoice>
      <appliesTo>bb194013-597c-4e4a-8493-b36d190f8717</appliesTo>
      <goToChain>61cfa825-120e-4b17-83e6-51a42b67d969</goToChain>
    </preconfiguredChoice>
    <!-- Delete packages after extraction -->
    <preconfiguredChoice>
      <appliesTo>f19926dd-8fb5-4c79-8ade-c83f61f55b40</appliesTo>
      <goToChain>85b1e45d-8f98-4cae-8336-72f40e12cbef</goToChain>
    </preconfiguredChoice>
    <!-- Transcribe files (OCR) -->
    <preconfiguredChoice>
      <appliesTo>7079be6d-3a25-41e6-a481-cee5f352fe6e</appliesTo>
      <goToChain>1170e555-cd4e-4b2f-a3d6-bfb09e8fcc53</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Transfer) -->
    <preconfiguredChoice>
      <appliesTo>f09847c2-ee51-429a-9478-a860477f6b8d</appliesTo>
      <goToChain>bed4eeb1-d654-4d97-b98d-40eb51d3d4bb</goToChain>
    </preconfiguredChoice>
    <!-- Store DIP location -->
    <preconfiguredChoice>
      <appliesTo>cd844b6e-ab3c-4bc6-b34f-7103f88715de</appliesTo>
      <goToChain>/api/v2/location/default/DS/</goToChain>
    </preconfiguredChoice>
    <!-- Generate transfer structure report -->
    <preconfiguredChoice>
      <appliesTo>56eebd45-5600-4768-a8c2-ec0114555a3d</appliesTo>
      <goToChain>e9eaef1e-c2e0-4e3b-b942-bfb537162795</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on originals -->
    <preconfiguredChoice>
      <appliesTo>70fc7040-d4fb-4d19-a0e6-792387ca1006</appliesTo>
      <goToChain>3e891cc4-39d2-4989-a001-5107a009a223</goToChain>
    </preconfiguredChoice>
    <!-- Reminder: add metadata if desired -->
    <preconfiguredChoice>
      <appliesTo>eeb23509-57e2-4529-8857-9d62525db048</appliesTo>
      <goToChain>5727faac-88af-40e8-8c10-268644b0142d</goToChain>
    </preconfiguredChoice>
    <!-- Store AIP -->
    <preconfiguredChoice>
      <appliesTo>2d32235c-02d4-4686-88a6-96f4d6c7b1c3</appliesTo>
      <goToChain>9efab23c-31dc-4cbd-a39d-bb1665460cbe</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on access derivatives -->
    <preconfiguredChoice>
      <appliesTo>8ce07e94-6130-4987-96f0-2399ad45c5c2</appliesTo>
      <goToChain>76befd52-14c3-44f9-838f-15a4e01624b0</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Ingest) -->
    <preconfiguredChoice>
      <appliesTo>7a024896-c4f7-4808-a240-44c87c762bc5</appliesTo>
      <goToChain>3c1faec7-7e1e-4cdd-b3bd-e2f05f4baa9b</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on preservation derivatives -->
    <preconfiguredChoice>
      <appliesTo>153c5f41-3cfb-47ba-9150-2dd44ebc27df</appliesTo>
      <goToChain>b7ce05f0-9d94-4b3e-86cc-d4b2c6dba546</goToChain>
    </preconfiguredChoice>
    <!-- Assign UUIDs to directories -->
    <preconfiguredChoice>
      <appliesTo>bd899573-694e-4d33-8c9b-df0af802437d</appliesTo>
      <goToChain>2dc3f487-e4b0-4e07-a4b3-6216ed24ca14</goToChain>
    </preconfiguredChoice>
    <!-- Store AIP location -->
    <preconfiguredChoice>
      <appliesTo>b320ce81-9982-408a-9502-097d0daa48fa</appliesTo>
      <goToChain>/api/v2/location/default/AS/</goToChain>
    </preconfiguredChoice>
    <!-- Document empty directories -->
    <preconfiguredChoice>
      <appliesTo>d0dfa5fc-e3c2-4638-9eda-f96eea1070e0</appliesTo>
      <goToChain>65273f18-5b4e-4944-af4f-09be175a88e8</goToChain>
    </preconfiguredChoice>
    <!-- Send transfer to quarantine -->
    <preconfiguredChoice>
      <appliesTo>755b4177-c587-41a7-8c52-015277568302</appliesTo>
      <goToChain>d4404ab1-dc7f-4e9e-b1f8-aa861e766b8e</goToChain>
    </preconfiguredChoice>
    <!-- Extract packages -->
    <preconfiguredChoice>
      <appliesTo>dec97e3c-5598-4b99-b26e-f87a435a6b7f</appliesTo>
      <goToChain>01d80b27-4ad1-4bd1-8f8d-f819f18bf685</goToChain>
    </preconfiguredChoice>
    <!-- Approve normalization -->
    <preconfiguredChoice>
      <appliesTo>de909a42-c5b5-46e1-9985-c031b50e9d30</appliesTo>
      <goToChain>1e0df175-d56d-450d-8bee-7df1dc7ae815</goToChain>
    </preconfiguredChoice>
    <!-- Upload DIP -->
    <preconfiguredChoice>
      <appliesTo>92879a29-45bf-4f0b-ac43-e64474f0f2f9</appliesTo>
      <goToChain>6eb8ebe7-fab3-4e4c-b9d7-14de17625baa</goToChain>
    </preconfiguredChoice>
  </preconfiguredChoices>
</processingMCP>
"""

BUILTIN_CONFIGS = {
    'default': DEFAULT_PROCESSING_CONFIG,
    'automated': AUTOMATED_PROCESSING_CONFIG,
}


def install_builtin_config(name, force=False):
    """Install the original version of a builtin processing configuration."""
    if name in BUILTIN_CONFIGS:
        config = BUILTIN_CONFIGS[name].encode('utf-8')
        path = os.path.join(
            django_settings.SHARED_DIRECTORY,
            'sharedMicroServiceTasksConfigs/processingMCPConfigs',
            '%sProcessingMCP.xml' % name
        )
        if force or not os.path.isfile(path):
            with open(path, 'w') as fd:
                fd.write(config)
        return config
