# -*- coding: utf-8 -*-
"""
    Tests for helper and utility methods
    TODO: move integration tests (e.g. all that test a full request cycle)
    into smaller, broken-up unit tests to simplify testing.
    ~~~~
    Flask-CORS is a simple extension to Flask allowing you to support cross
    origin resource sharing (CORS) using a simple decorator.

    :copyright: (c) 2016 by Cory Dolphin.
    :license: MIT, see LICENSE for more details.
"""

import unittest

from flask_cors.core import *


class InternalsTestCase(unittest.TestCase):
    def test_try_match_pattern(self):
        self.assertFalse(try_match_pattern('www.com/foo', 'www.com/fo', caseSensitive=True))
        self.assertTrue(try_match_pattern('www.com/foo', 'www.com/fo*', caseSensitive=True))
        self.assertTrue(try_match_pattern('www.com', 'WwW.CoM', caseSensitive=False))
        self.assertTrue(try_match_pattern('/foo', '/fo*', caseSensitive=True))
        self.assertFalse(try_match_pattern('/foo', '/Fo*', caseSensitive=True))

    def test_flexible_str_str(self):
        self.assertEqual(flexible_str('Bar, Foo, Qux'), 'Bar, Foo, Qux')

    def test_flexible_str_set(self):
        self.assertEqual(flexible_str({'Foo', 'Bar', 'Qux'}),
                          'Bar, Foo, Qux')

    def test_serialize_options(self):
        try:
            serialize_options({
                'origins': r'*',
                'allow_headers': True,
                'supports_credentials': True,
                'send_wildcard': True
            })
            self.assertFalse(True, "A Value Error should have been raised.")
        except ValueError:
            pass

    def test_get_allow_headers_empty(self):
        options = serialize_options({'allow_headers': r'*'})

        self.assertEqual(get_allow_headers(options, ''), None)
        self.assertEqual(get_allow_headers(options, None), None)

    def test_get_allow_headers_matching(self):
        options = serialize_options({'allow_headers': r'*'})

        self.assertEqual(get_allow_headers(options, 'X-FOO'), 'X-FOO')
        self.assertEqual(
            get_allow_headers(options, 'X-Foo, X-Bar'),
            'X-Bar, X-Foo'
        )

    def test_get_allow_headers_matching_none(self):
        options = serialize_options({'allow_headers': r'X-FLASK-.*'})

        self.assertEqual(get_allow_headers(options, 'X-FLASK-CORS'),
                          'X-FLASK-CORS')
        self.assertEqual(
            get_allow_headers(options, 'X-NOT-FLASK-CORS'),
            ''
        )

    def test_parse_resources_sorted(self):
        resources = parse_resources({
            '/foo': {'origins': 'http://foo.com'},
            re.compile(r'/.*'): {
                'origins': 'http://some-domain.com'
            },
            re.compile(r'/api/v1/.*'): {
                'origins': 'http://specific-domain.com'
            }
        })

        self.assertEqual(
            [r[0] for r in resources],
            ['/foo', re.compile(r'/api/v1/.*'), re.compile(r'/.*')]
        )

    def test_parse_resources_more_specific_regex_first(self):
        # A broad pattern listed first in the config must not shadow a more
        # specific pattern, regardless of whether patterns are strings or
        # pre-compiled regexes.
        broad = {'origins': 'http://broad.com'}
        specific = {'origins': 'http://specific.com'}

        resources = parse_resources({
            r'/api/.*': broad,
            r'/api/v1/users/.*': specific,
        })
        self.assertEqual(
            [r[0] for r in resources],
            [r'/api/v1/users/.*', r'/api/.*']
        )

        # Reverse the configured order: the result must be identical.
        resources_reversed = parse_resources({
            r'/api/v1/users/.*': specific,
            r'/api/.*': broad,
        })
        self.assertEqual(
            [r[0] for r in resources_reversed],
            [r'/api/v1/users/.*', r'/api/.*']
        )

        # Mixing compiled regexes and regex strings must not change ordering.
        resources_mixed = parse_resources({
            re.compile(r'/api/.*'): broad,
            r'/api/v1/users/.*': specific,
        })
        self.assertEqual(
            [get_regexp_pattern(r[0]) for r in resources_mixed],
            [r'/api/v1/users/.*', r'/api/.*']
        )

        # With an equal number of path segments, the longer (more specific)
        # pattern wins.
        resources_tie = parse_resources({
            r'/api/.*': broad,
            r'/api/v[0-9]': specific,
        })
        self.assertEqual(
            [r[0] for r in resources_tie],
            [r'/api/v[0-9]', r'/api/.*']
        )

    def test_probably_regex(self):
        self.assertTrue(probably_regex("http://*.example.com"))
        self.assertTrue(probably_regex("*"))
        self.assertFalse(probably_regex("http://example.com"))
        self.assertTrue(probably_regex(r"http://[\w].example.com"))
        self.assertTrue(probably_regex(r"http://\w+.example.com"))
        self.assertTrue(probably_regex("https?://example.com"))
