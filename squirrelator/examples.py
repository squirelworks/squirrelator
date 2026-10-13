"""Built-in example translations for testing and demos."""

EXAMPLES = [
    {
        "source": "print hello to the user",
        "from_lang": "english",
        "to_lang": "python",
        "expected_hint": "print('hello')",
    },
    {
        "source": "for i in range(1, 6): print(i)",
        "from_lang": "python",
        "to_lang": "english",
        "expected_hint": "Print the numbers 1 through 5",
    },
    {
        "source": "repeat 5 times: show the count",
        "from_lang": "pseudocode",
        "to_lang": "quickbasic",
        "expected_hint": "FOR loop with PRINT",
    },
]
