'''Various utility functions that are used throughout SRST2'''

import re
import logging
from subprocess import call, check_output, CalledProcessError, STDOUT

# Exception to raise if the command we try to run fails for some reason
class CommandError(Exception):
	pass

def run_command(command, **kwargs):
	'Execute a shell command and check the exit status and any O/S exceptions'
	command_str = ' '.join(command)
	logging.info('Running: {}'.format(command_str))
	try:
		exit_status = call(command, **kwargs)
	except OSError as e:
		message = "Command '{}' failed due to O/S error: {}".format(command_str, str(e))
		raise CommandError({"message": message})
	if exit_status != 0:
		message = "Command '{}' failed with non-zero exit status: {}".format(command_str, exit_status)
		raise CommandError({"message": message})


def check_command_version(command_list, version_checker, command_name, required_version):
    '''Check that an acceptable version of a command is installed
    Exits the program if it can't be found.
    - command_list is the command to run to determine the version.
    - version_checker is a function that checks is the stdout of the program
      satisfies the version information somehow
    - command_name is the name of the command to show in error messages.
    - required_version is the version number to show in error messages.
    '''
    try:
        command_stdout = check_output(command_list, stderr=STDOUT)
    except OSError as e:
        logging.error("Failed command: {}".format(' '.join(command_list)))
        logging.error(str(e))
        logging.error("Could not determine the version of {}.".format(command_name))
        logging.error("Do you have {} installed in your PATH?".format(command_name))
        exit(-1)
    except CalledProcessError as e:
        # some programs such as samtools return a non-zero exit status
        # when you ask for the version (sigh). We ignore it here.
        command_stdout = e.output

    if not version_checker(command_stdout):
        logging.error("Incorrect version of {} installed.".format(command_name))
        logging.error("{} version {} is required by SRST2.".format(command_name, required_version))
        exit(-1)

def check_command_version_literal(command_list, version_str, command_name, required_version):
    'Check that the version number of a program contains some literal text'
    def checker(stdout_text):
        return version_str in stdout_text
    return check_command_version(command_list, checker, command_name, required_version)

SAMTOOLS_VERSION_STR = '0.1.18'

def check_samtools_version():
    'Check that the version number of bowtie is == SAMTOOLS_VERSION_STR'
    return check_command_version_literal(['samtools'],
               'Version: ' + SAMTOOLS_VERSION_STR,
               'samtools',
               SAMTOOLS_VERSION_STR)

# regular expression to find the version number of bowtie2 from the output of
# the command "bowtie2 --version".
# We assume bowtie will report a version number in the form major.minor.patch 
BOWTIE_VERSION_REGEX = \
    re.compile(r'bowtie2.* version (?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)')

def check_bowtie_version():
    'Check that the version number of bowtie is >= MINIMUM_BOWTIE_VERSION'

    MINIMUM_BOWTIE_VERSION = (2, 1, 0)
    MINIMUM_BOWTIE_VERSION_STR = "%d.%d.%d" % MINIMUM_BOWTIE_VERSION
    BOWTIE_VERSION_COMMAND = ['bowtie2', '--version']
    BOWTIE_VERSION_COMMAND_STR = ' '.join(BOWTIE_VERSION_COMMAND)

    def checker(stdout_text):
        match = BOWTIE_VERSION_REGEX.search(stdout_text)
        if match is not None:
           major = int(match.group('major'))
           minor = int(match.group('minor'))
           patch = int(match.group('patch'))
           return (major, minor, patch) >= MINIMUM_BOWTIE_VERSION
        else:
           logging.error('Cannot find bowtie version number in output of {}'
                             .format(BOWTIE_VERSION_COMMAND_STR))
           return False
    return check_command_version(BOWTIE_VERSION_COMMAND, checker, 'bowtie',
               '>= ' + MINIMUM_BOWTIE_VERSION_STR)
