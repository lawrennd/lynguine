from nose.tools import eq_, ok_, raises

import yaml
import os
import re
import sys
import filecmp
import unittest


import ndlpy.talk as nt

    

class TalkTests(unittest.TestCase):
    def test_talk_field(self):
        """talk_tests: Test the talk_field"""
        
        filename = "my_yaml_file.yml"
        testdict = {'cat': 'dog',
                    'butcher': 'baker',
                    'candlestick': 'maker'}
        
        with open(filename, 'w') as file:
            yaml.dump(testdict, file)
        for key, item in testdict.items():
            self.assertTrue(nt.talk_field(key, filename)==item)
