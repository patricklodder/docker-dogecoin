#!/usr/bin/env python3
# Copyright (c) 2021 The Dogecoin Core developers
"""
Runs the integration tests
"""

import subprocess
import sys

from .integration.framework.test_runner import TestRunner

class IntegrationRunner(TestRunner):
    """Runs the integration tests"""

    def __init__(self):
        """Constructor"""
        TestRunner.__init__(self)
        self.found_failure = False
        self.result_map = {}


    def add_options(self, parser):
        """Add test-specific --version option"""
        parser.add_argument("--version", dest="version", required=True,
            help="The version that is expected to be installed, eg: '1.14.5'")

    def run_test(self):
        """Run all specified tests and inherit any failures"""

        tests = [
            [ "version", [ "--version", self.options.version ] ]
        ]

        for test in tests:
            self.result_map[test[0]] = self.run_individual_test(test)

        self.print_summary()

        if self.found_failure:
            sys.exit(1)

        sys.exit(0)

    def run_individual_test(self, test):
        """Run the actual test"""
        command = [
            "/usr/bin/env", "python3",
            "-m", f"tests.integration.{ test[0] }",
            "--platform", self.options.platform,
            "--image", self.options.image,
        ]

        if len(test) > 1 and len(test[1]) > 0:
            for arg in test[1]:
                command.append(arg)

        if self.options.verbose:
            command.append("--verbose")

        try:
            output = subprocess.run(command, capture_output=True, check=True)
        except subprocess.CalledProcessError as test_err:
            self.found_failure = True
            print("\n")
            print(test[0])
            print("----------------------")
            print(test_err.stderr.decode("utf-8"))
            print(test_err.stdout.decode("utf-8"))
            return False

        if self.options.verbose:
            print("\n")
            print(test[0])
            print("----------------------")
            print(output.stdout.decode("utf-8"))

        return True

    def print_summary(self):
        """Print a summary to stdout"""
        print("\n")
        print(f"RESULTS: for { self.options.image } on { self.options.platform }")

        successes = 0
        failures = 0
        for test, result in self.result_map.items():
            if result:
                successes += 1
                result_str = "Success"
            else:
                failures += 1
                result_str = "Failure"

            print(f"{ test }: { result_str }")

        sum_str = f"{ successes } successful tests and { failures } failures"
        print(f"\nFinished test suite with { sum_str }")

if __name__ == '__main__':
    IntegrationRunner().main()
