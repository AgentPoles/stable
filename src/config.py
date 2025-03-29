"""
Configuration settings for the project.
"""

# Whether to analyze multiple chains or just Ethereum
MULTICHAIN = False

# Governor IDs for different chains
GOVERNOR_IDS = {
    "ethereum": "eip155:1:0xEC568fffba86c094cf06b22134B23074DFE2252c",
    "arbitrum": "eip155:42161:0x789fC99093B09adD01d79dFBe6AA0d9a6e471c77",
    "optimism": "eip155:10:0x6E17cdef07F64192Bf7747c56F1Fd6fB4D6e4276",
    "base": "eip155:8453:0x6E17cdef07F64192Bf7747c56F1Fd6fB4D6e4276",
    "polygon": "eip155:137:0x6E17cdef07F64192Bf7747c56F1Fd6fB4D6e4276"
} 