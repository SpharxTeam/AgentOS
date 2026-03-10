# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# TokenCounter 单元测试

import unittest
from agentos_cta.utils.token_counter import TokenCounter

class TestTokenCounter(unittest.TestCase):
    def setUp(self):
        self.counter = TokenCounter("gpt-4")

    def test_count_tokens(self):
        text = "Hello, world!"
        count = self.counter.count_tokens(text)
        self.assertGreater(count, 0)

    def test_adaptive_truncate(self):
        long_text = "word " * 1000
        truncated = self.counter.adaptive_truncate(long_text, 100)
        self.assertLessEqual(self.counter.count_tokens(truncated), 100)

if __name__ == "__main__":
    unittest.main()