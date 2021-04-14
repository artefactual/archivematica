# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from django.conf import settings as django_settings


DEFAULT_PROCESSING_CONFIG = u"""<processingMCP>
  <preconfiguredChoices>
    <!-- Select compression level -->
    <preconfiguredChoice>
      <appliesTo>01c651cb-c174-4ba4-b985-1d87a44d6754</appliesTo>
      <goToChain>414da421-b83f-4648-895f-a34840e3c3f5</goToChain>
    </preconfiguredChoice>
    <!-- Perform file format identification (Submission documentation & metadata) -->
    <preconfiguredChoice>
      <appliesTo>087d27be-c719-47d8-9bbb-9a7d8b609c44</appliesTo>
      <goToChain>4dec164b-79b0-4459-8505-8095af9655b5</goToChain>
    </preconfiguredChoice>
    <!-- Bind PIDs -->
    <preconfiguredChoice>
      <appliesTo>a2ba5278-459a-4638-92d9-38eb1588717d</appliesTo>
      <goToChain>44a7c397-8187-4fd2-b8f7-c61737c4df49</goToChain>
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
    <!-- Generate thumbnails -->
    <preconfiguredChoice>
      <appliesTo>498f7a6d-1b8c-431a-aa5d-83f14f3c5e65</appliesTo>
      <goToChain>c318b224-b718-4535-a911-494b1af6ff26</goToChain>
    </preconfiguredChoice>
    <!-- Select compression algorithm -->
    <preconfiguredChoice>
      <appliesTo>01d64f58-8295-4b7b-9cab-8f1b153a504f</appliesTo>
      <goToChain>9475447c-9889-430c-9477-6287a9574c5b</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on access derivatives -->
    <preconfiguredChoice>
      <appliesTo>8ce07e94-6130-4987-96f0-2399ad45c5c2</appliesTo>
      <goToChain>76befd52-14c3-44f9-838f-15a4e01624b0</goToChain>
    </preconfiguredChoice>
    <!-- Perform file format identification (Ingest) -->
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
      <goToChain>891f60d0-1ba8-48d3-b39e-dd0934635d29</goToChain>
    </preconfiguredChoice>
    <!-- Document empty directories -->
    <preconfiguredChoice>
      <appliesTo>d0dfa5fc-e3c2-4638-9eda-f96eea1070e0</appliesTo>
      <goToChain>65273f18-5b4e-4944-af4f-09be175a88e8</goToChain>
    </preconfiguredChoice>
    <!-- Virus scanning: Yes -->
    <preconfiguredChoice>
      <appliesTo>856d2d65-cd25-49fa-8da9-cabb78292894</appliesTo>
      <goToChain>6e431096-c403-4cbf-a59a-a26e86be54a8</goToChain>
    </preconfiguredChoice>
    <!-- Virus scanning: Yes -->
    <preconfiguredChoice>
      <appliesTo>1dad74a2-95df-4825-bbba-dca8b91d2371</appliesTo>
      <goToChain>1ac7d792-b63f-46e0-9945-d48d9e5c02c9</goToChain>
    </preconfiguredChoice>
    <!-- Virus scanning: Yes -->
    <preconfiguredChoice>
      <appliesTo>7e81f94e-6441-4430-a12d-76df09181b66</appliesTo>
      <goToChain>97be337c-ff27-4869-bf63-ef1abc9df15d</goToChain>
    </preconfiguredChoice>
    <!-- Virus scanning: Yes -->
    <preconfiguredChoice>
      <appliesTo>390d6507-5029-4dae-bcd4-ce7178c9b560</appliesTo>
      <goToChain>34944d4f-762e-4262-8c79-b9fd48521ca0</goToChain>
    </preconfiguredChoice>
    <!-- Virus scanning: Yes -->
    <preconfiguredChoice>
      <appliesTo>97a5ddc0-d4e0-43ac-a571-9722405a0a9b</appliesTo>
      <goToChain>3e8c0c39-3f30-4c9b-a449-85eef1b2a458</goToChain>
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
    <!-- Examine contents -->
    <preconfiguredChoice>
      <appliesTo>accea2bf-ba74-4a3a-bb97-614775c74459</appliesTo>
      <goToChain>e0a39199-c62a-4a2f-98de-e9d1116460a8</goToChain>
    </preconfiguredChoice>
    <!-- Perform file format identification (Submission documentation & metadata) -->
    <preconfiguredChoice>
      <appliesTo>087d27be-c719-47d8-9bbb-9a7d8b609c44</appliesTo>
      <goToChain>4dec164b-79b0-4459-8505-8095af9655b5</goToChain>
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
      <appliesTo>a2ba5278-459a-4638-92d9-38eb1588717d</appliesTo>
      <goToChain>44a7c397-8187-4fd2-b8f7-c61737c4df49</goToChain>
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
      <appliesTo>82ee9ad2-2c74-4c7c-853e-e4eaf68fc8b6</appliesTo>
      <goToChain>0a24787c-00e3-4710-b324-90e792bfb484</goToChain>
    </preconfiguredChoice>
    <!-- Perform file format identification (Transfer) -->
    <preconfiguredChoice>
      <appliesTo>f09847c2-ee51-429a-9478-a860477f6b8d</appliesTo>
      <goToChain>d97297c7-2b49-4cfe-8c9f-0613d63ed763</goToChain>
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
    <!-- Generate thumbnails -->
    <preconfiguredChoice>
      <appliesTo>498f7a6d-1b8c-431a-aa5d-83f14f3c5e65</appliesTo>
      <goToChain>972fce6c-52c8-4c00-99b9-d6814e377974</goToChain>
    </preconfiguredChoice>
    <!-- Select compression algorithm -->
    <preconfiguredChoice>
      <appliesTo>01d64f58-8295-4b7b-9cab-8f1b153a504f</appliesTo>
      <goToChain>9475447c-9889-430c-9477-6287a9574c5b</goToChain>
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
    <!-- Perform file format identification (Ingest) -->
    <preconfiguredChoice>
      <appliesTo>7a024896-c4f7-4808-a240-44c87c762bc5</appliesTo>
      <goToChain>5b3c8268-5b33-4b70-b1aa-0e4540fe03d1</goToChain>
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
    <!-- Virus scanning: Yes -->
    <preconfiguredChoice>
      <appliesTo>856d2d65-cd25-49fa-8da9-cabb78292894</appliesTo>
      <goToChain>6e431096-c403-4cbf-a59a-a26e86be54a8</goToChain>
    </preconfiguredChoice>
    <!-- Virus scanning: Yes -->
    <preconfiguredChoice>
      <appliesTo>1dad74a2-95df-4825-bbba-dca8b91d2371</appliesTo>
      <goToChain>1ac7d792-b63f-46e0-9945-d48d9e5c02c9</goToChain>
    </preconfiguredChoice>
    <!-- Virus scanning: Yes -->
    <preconfiguredChoice>
      <appliesTo>7e81f94e-6441-4430-a12d-76df09181b66</appliesTo>
      <goToChain>97be337c-ff27-4869-bf63-ef1abc9df15d</goToChain>
    </preconfiguredChoice>
    <!-- Virus scanning: Yes -->
    <preconfiguredChoice>
      <appliesTo>390d6507-5029-4dae-bcd4-ce7178c9b560</appliesTo>
      <goToChain>34944d4f-762e-4262-8c79-b9fd48521ca0</goToChain>
    </preconfiguredChoice>
    <!-- Virus scanning: Yes -->
    <preconfiguredChoice>
      <appliesTo>97a5ddc0-d4e0-43ac-a571-9722405a0a9b</appliesTo>
      <goToChain>3e8c0c39-3f30-4c9b-a449-85eef1b2a458</goToChain>
    </preconfiguredChoice>
  </preconfiguredChoices>
</processingMCP>
"""

BUILTIN_CONFIGS = {
    "default": DEFAULT_PROCESSING_CONFIG,
    "automated": AUTOMATED_PROCESSING_CONFIG,
}


def install_builtin_config(name, force=False):
    """
    Install the original version of a builtin processing configuration
    """
    if name in BUILTIN_CONFIGS:
        config = BUILTIN_CONFIGS[name]
        path = os.path.join(
            django_settings.SHARED_DIRECTORY,
            "sharedMicroServiceTasksConfigs/processingMCPConfigs",
            "%sProcessingMCP.xml" % name,
        )
        if force or not os.path.isfile(path):
            with open(path, "w") as fd:
                fd.write(config)
        return config
