#!/usr/bin/env python

from time import time
from django.conf import settings
import simplejson as json

from logger import get_logger

import subprocess
import copy
import os
import threading
import re
from webui.scheduler.log import get_redis_logger

os.environ['PYTHONIOENCODING'] = 'utf-8'

LOG_CACHE_MAX_SIZE = 20

PARAM_PATTERN = re.compile('WFOUT\s*<([^>]+)>\s*:\s*<([^>]*)>')

BASH_VAR_PATTERN = re.compile('\$\w')

_logger = get_logger('workflow')


class Workflow(object):
    """Workflow Manager Class"""
    logger = _logger
    _logger_name = None
    extra_vars = {
        'virtual_env_path': settings.VIRTUAL_ENV_PATH,
        'python': 'DJANGO_CALLER=script DJANGO_CONF={} '
                  'PYTHONPATH=${{PYTHONPATH}}:$ROOT python'
                  ''.format(settings.DJANGO_CONF),
        'ROOT': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    }

    def __init__(self, config_file, input_params=None, logger_name=None,
                 store_output=False):
        """Workflow init and configuration loading."""
        if not input_params:
            input_params = {}
        self.store_output = store_output

        if logger_name:
            self._logger_name = logger_name
            self.logger = get_redis_logger(logger_name)

        # make sure the input params are all strings
        for key, value in input_params.items():
            input_params[key] = unicode(value)

        self.status_log = []
        self._config_file = os.path.abspath(config_file)
        with open(config_file) as f:
            self.config = json.load(f)
        self._verify_input_params(self.config, input_params)
        self.config['vars'].update(input_params)
        self.config['vars'].update(self.extra_vars)
        self.logger.debug('Loaded configuration %s', self.config)

    def describe(self):
        """Describes the workflow module"""
        out = 'Module:' + self.config['module'] + '\n'
        out += 'Actions:\n'
        for action in self.config['actions']:
            if action:
                out += '\t' + action['action'] + '\n'
        return out

    def run_module(self, action_name=None, single=False):
        """Run a workflow module"""

        lock = threading.Lock()
        with lock:
            wf_output = []
            wf_out_params = {}
            self._print_and_log(
                'Activated module %s ' % self.config['module'], wf_output)
            if action_name:
                self._print_and_log(
                    'Running fragment sequence from [{0}]'.format(action_name),
                    wf_output
                )
            else:
                self._print_and_log('Running sequence', wf_output)
            wf_out_params = self._merge_maps(
                wf_out_params, self._exec_code(self.config['begin']))
            try:
                found = action_name is None
                for action in self.config['actions']:
                    if not action:
                        if not found:
                            continue
                        else:
                            if not action_name:
                                break
                    if not found and action_name \
                            and action['action'] != action_name:
                        continue
                    else:
                        found = True

                    command = action['command']
                    if isinstance(command, basestring):
                        command_out = self.process_command(
                            action['action'], command)
                        wf_out_params = self._merge_maps(
                            wf_out_params, command_out['process_out_params'])
                        self._print_and_log(command_out['stdout'] +
                                            command_out['stderr'], wf_output)
                    elif isinstance(command, dict):
                        sub_module_out = self._run_sub_module(
                            command['module'], command['params'])
                        wf_out_params = self._merge_maps(
                            wf_out_params, sub_module_out['wf_output_params'])
                        self._print_and_log(
                            sub_module_out['wf_output'], wf_output)
                    else:
                        raise Exception('Unsupported command: ' + command)

                    if single:
                        break
                    if 'next' in action:
                        next_action = action['next']
                        self._print_and_log(
                            'Executing next action ' + next_action, wf_output)
                        out_params = self.run_module(next_action)
                        wf_output.append(out_params['wf_output'])
            except Exception as e:
                self.logger.exception(
                    u'Exception while running command: [%s]', command)
                wf_out_params = self._merge_maps(
                    wf_out_params, self._exec_code(self.config['error']))
                raise e
            finally:
                wf_out_params.update(self._exec_code(self.config['end']))
            return {'wf_output': wf_output, 'wf_output_params': wf_out_params}

    def expand_string(self, string, variables=None):
        """Expands a string containing variables"""
        if not variables:
            variables = self.config['vars']

        processed = {}
        while True:
            pre = string
            for v in variables:
                string = string.replace('$' + v, variables[v])

            # expansion has been completed.
            if string != pre:
                if string in processed:
                    raise Exception('Expansion loop detected: ' + string)
                processed[string] = None
            else:
                break

        if BASH_VAR_PATTERN.search(string):
            raise Exception(
                'Unexpanded variable(s) found in [{0}]'.format(string)
            )
        return string

    def get_vars(self):
        """Returns the defined variables"""
        return copy.deepcopy(self.config['vars'])

    def get_expanded_vars(self):
        """Returns the defined variables expanded"""
        for key, value in self.get_vars().iteritems():
            yield (key, self.expand_string(value))

    def process_command(self, action, command):
        """Processes a command"""
        expanded_command = self.expand_string(command)
        self._set_status_processing(action, expanded_command)
        stdout = [] if self.store_output else None
        stderr = [] if self.store_output else None
        process_out_params = {}

        self.logger.info('Processing command:[%s]', expanded_command)
        proc = subprocess.Popen(
            expanded_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out_stream = StreamConsumer(
            proc.stdout, 'OUT', self.logger, stdout, process_out_params)
        err_stream = StreamConsumer(proc.stderr, 'ERR', self.logger, stderr)
        out_stream.start()
        err_stream.start()
        try:
            proc.wait()
            out_stream.join()
            err_stream.join()
        except:
            self.logger.exception('Error while executing command')
        finally:
            self._set_status_done(proc.returncode, stdout, stderr)
        self.logger.info('EXIT CODE %d', proc.returncode)
        self.logger.info('STDOUT: %r', stdout)
        self.logger.info('STDERR: %r', stderr)
        if proc.returncode != 0:
            raise Exception(
                (
                    u'Command "{0}"\nFailed with exit code [{1}].\nOUT\n' + ('-' * 20) + '\n{2}\n' + (
                        '-' * 20) + '\nERR\n' + ('-' * 20) + '\n{3}\n' + ('-' * 20) + '\n'
                ).format(expanded_command, proc.returncode, '\n'.join(stdout) if stdout is not None else '',
                         '\n'.join(stderr) if stderr is not None else ''))
        return {
            'stdout': '' if stdout is None else '\n'.join(stdout),
            'stderr': '' if stderr is None else '\n'.join(stderr),
            'process_out_params': process_out_params
        }

    def _print_and_log(self, msg, log=None):
        self.logger.info(msg)
        if log is not None:
            log.append(msg)

    def _verify_input_params(self, config, params):
        if not 'input_params' in config:
            return
        input_params = config['input_params']
        for input_param in input_params:
            if not input_param in params:
                raise Exception("input param '{0}' must be specified.".format(
                    input_param))

    def _exec_code(self, code):
        """Executes arbitrary code"""
        func = "def __dyna_func():\n\t" + code
        _context = {}
        _locals = {}
        for var, val in self.get_expanded_vars():
            _locals['_' + var] = val
        exec func in _locals, _context
        out = _context['__dyna_func']()
        return out if out else {}

    def _set_status_processing(self, action, command):
        """Sets the processing status as begun"""
        self._processing_action = action
        self._processing_command = command
        self._processing_start_time = time()

    def _set_status_done(self, exit_status, out, err):
        """Sets the processing status as terminated"""
        elapsed_time = time() - self._processing_start_time
        if len(self.status_log) >= LOG_CACHE_MAX_SIZE:
            self.status_log.pop()
        self.status_log.append(
            {
                'action': self._processing_action,
                'command': self._processing_command,
                'elapsed': elapsed_time,
                'exit_status': exit_status,
                'out': out,
                'err': err
            }
        )

    def _run_sub_module(self, module_name, params):
        """Runs a nested workflow."""
        try:
            self.logger.info('Running sub module "%s" with params "%s".',
                             module_name, repr(params))

            # TODO: properties should be copied transparently
            return Workflow(
                os.path.dirname(self._config_file) + '/' +
                module_name + '-configuration.json', params,
                logger_name=self._logger_name,
                store_output=self.store_output
            ).run_module()
        except Exception, e:
            self.logger.exception("Error while running sub module %s",
                                  module_name)
            raise Exception("Error while running sub module.", e)

    def _merge_maps(self, m1, m2):
        """
        Merges two maps which values are lists and returns the merged map.
        """
        result = m1.copy()
        result.update(m2)
        for k in m1.iterkeys():
            if k in m2:
                result[k] = list(set(m1[k] + m2[k]))
        return result


class StreamConsumer(threading.Thread):
    """Consumes and parses a process stream"""

    def __init__(self, stream, stream_name, logger, buff,
                 process_out_params=None):
        threading.Thread.__init__(self)
        self.stream = stream
        self.stream_name = stream_name
        self.logger = logger
        self.buff = buff
        self.process_out_params = process_out_params

    def run(self):
        try:
            if self.stream:
                while True:
                    line = self.stream.readline().decode('utf8')
                    if not line:
                        break

                    if self.process_out_params is not None:
                        match = PARAM_PATTERN.match(line)
                        if match is not None:
                            key = match.group(1)
                            value = match.group(2)
                            value_list = self.process_out_params.get(
                                key, None)
                            if value_list is None:
                                value_list = []
                                self.process_out_params[key] = value_list
                            value_list.append(value)
                    emitted = "[" + self.stream_name + "] " + line.rstrip()
                    self.logger.debug(emitted)
                    if self.buff is not None:
                        self.buff.append(emitted)
        except:
            self.logger.exception('Exception reading workflow %s',
                                  self.stream_name)
