import sys
import os
import json
import difflib
import entrypoint

class CommandNotFound(Exception):
    """Raised when entrypoint command is not found or test fail."""

class Command:
    """
    Represent a single execve command, with
    its arguments and environment.

    Can represent an entrypoint hooked command, the expected
    result or the input of a test.
    """
    def __init__(self, argv, environ):
        #sort cli arguments to facilitate comparaison
        sorted_args = argv[1:]
        sorted_args.sort()
        self.argv = [argv[0]] + sorted_args
        self.environ = environ

    def __eq__(self, other):
        """Compare 2 Command, result of a test and expected command."""
        return self.argv == other.argv and self.environ == other.environ

    def __str__(self):
        """Render single command into string for error outputs."""
        argv_str = json.dumps(self.argv, indent=4)
        command_str = f"argv: {argv_str}\n"
        environ_str = json.dumps(self.environ, indent=4)
        command_str += f"environ: {environ_str}"
        return command_str

    def diff(self, other):
        """Perform diff between result command and expected command."""
        command = str(self).splitlines()
        other_command = str(other).splitlines()

        return difflib.unified_diff(command, other_command,
                fromfile="result", tofile="expected", lineterm="")

class EntrypointHook:
    """
    Hook to perform test of the Dockerfile entrypoint.py. Manage all
    informations about test input, test output and expected output.

    Hook system calls os.execve, os.setuid & os.setgid used
    by entrypoint. Catch execve arguments to perform comparaison tests,
    disable setuid & setgid behavior.
    """
    def __init__(self):
        self._reset_attributes()
        self._setup_hooks()

    def entrypoint(self, test_argv, test_environ):
        """
        Run a command using entrypoint. Can be used manually
        if no need to compare command launched by entrypoint.

        Fake entrypoint arguments (sys.argv) and environment variables.
        """
        #Clean hook from previous test, store the command to test.
        self._reset_attributes()

        #Manage system arguments & environment used by the script
        sys.argv[1:] = test_argv.copy()
        os.environ = test_environ.copy()

        #Launch entrypoint script
        entrypoint.main()

        if self.result is None:
            raise CommandNotFound("Test fail, do not return a command")

    def test(self, test_argv, test_environ, \
            result_argv, result_environ):
        """
        Run a test of entrypoint and store expected result in the hook
        for further comparaison.
        """
        self.entrypoint(test_argv, test_environ)
        self.reference = Command(result_argv, result_environ)

    def _execve_hook(self, executable, argv, environ):
        """
        Hook for os.execve function, to catch arguments/environment
        instead of launching processes.
        """
        self.result = Command(argv, environ)

    def _reset_attributes(self):
        """Clean state between each test"""
        self.result = None
        self.reference = None

    def _setup_hooks(self):
        """Enable hooks of entrypoint.py system calls."""
        #Save system functions to restore it
        self._execve_backup = os.execve
        self._setgid_backup = os.setgid
        self._setuid_backup = os.setuid

        #Add execve hook globally to catch entrypoint arguments
        os.execve = self._execve_hook

        #Disable setgid & setuid behavior
        os.setgid = lambda _ : None
        os.setuid = lambda _ : None

    def _reset_hooks(self):
        """Restore python system calls to default functions"""
        os.execve = self._execve_backup
        os.setgid = self._setgid_backup
        os.setuid = self._setuid_backup
