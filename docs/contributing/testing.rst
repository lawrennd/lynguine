Testing Guidelines
==================

Testing is an integral part of our development process. Here's how you can run and write tests for the project.

Running Tests
-------------

To run the test suite, use the following command from the project's root directory:

.. code-block:: bash

    poetry run pytest

This will execute all the tests and display the results.

Writing Tests
-------------

When contributing new features or fixes, include corresponding tests. We use pytest as our testing framework.

- Write clear, concise tests.
- Ensure tests cover both successful and failure cases.
- Follow the naming conventions: test functions should start with `test_`.

Test Coverage
-------------

Aim to maintain or increase the test coverage with your contributions. You can check the coverage report generated after running the tests.

Continuous Integration
----------------------

All pull requests will undergo automated testing through our CI pipeline. Ensure your changes pass these tests before requesting a review.
