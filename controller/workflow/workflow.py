#!/usr/bin/env python

from time import time
from logger import get_logger

import json
import subprocess
import copy
import sys, traceback
import os
import fcntl
import signal
import threading
import re

os.environ['PYTHONIOENCODING'] = 'utf-8'

LOG_CACHE_MAX_SIZE = 20

PARAM_PATTERN = re.compile('WFOUT\s*<([^>]+)>\s*:\s*<([^>]*)>')

BASH_VAR_PATTERN = re.compile('.*\$\w.*')

_logger = get_logger('workflow')

class Workflow:

	"""Workflow Manager Class"""

	def __init__(self, config_file, input_params={}):
		"""Workflow init and configuration loading."""
		self.status_log = []
		self._store_out = None
		self._store_err = None
		self._config_file = os.path.abspath(config_file)
		self.config = json.load( open(config_file) )
		self._verify_input_params(self.config, input_params)
		self.config['vars'].update(input_params)
		self.root_dir = os.path.dirname( os.path.abspath(__file__) ) + '/../'
		self.config['vars']['ROOT'] = self.root_dir
		_logger.debug('Loaded configuration %s', self.config)

	@property
	def store_out(self):
		return self._store_out

	@store_out.setter
	def store_out(self, f):
		self._store_out = f

	@property
	def store_err(self):
		return self._store_err

	@store_err.setter
	def store_err(self, f):
		self._store_err = f

	def describe(self):
		"""Describes the workflow module"""
		out  = 'Module:' + self.config['module'] + '\n';
		out += 'Actions:\n'
		for action in self.config['actions']: 
			if action: out += '\t' + action['action'] + '\n'
		return out

	def run_module(self, action_name=None, single=False):
		"""Run a workflow module"""
		lock = threading.Lock()
		with lock:
			wf_output = []
			wf_out_params = {}
			self._print_and_log('Activated module %s ' % self.config['module'], wf_output)
			if action_name: 
				self._print_and_log('Running fragment sequence from [{0}]'.format(action_name), wf_output)
			else:
				self._print_and_log('Running sequence', wf_output)
			wf_out_params = self._merge_maps( wf_out_params, self._exec_code( self.config['begin'] ) )
			try :
				found = action_name == None
				for action in self.config['actions']:
					if not action: continue
					if not found and ( action_name and not action['action'] == action_name ): 
						continue 
					else:
						found = True

					command = action['command']
					if type(command) == str or type(command) == unicode:
						command_out = self.process_command(action['action'], command)
						wf_out_params = self._merge_maps( wf_out_params, command_out['process_out_params'] )
						self._print_and_log( command_out['stdout'] + command_out['stderr'], wf_output )
					elif(type(command) == dict):
						sub_module_out = self._run_sub_module(command['module'], command['params'])
						wf_out_params = self._merge_maps( wf_out_params, sub_module_out['wf_output_params'])
						self._print_and_log( sub_module_out['wf_output'], wf_output )
					else:
						raise Exception('Unsupported command: ' + command)

					if single: break
					if action.has_key('next'):
						next_action =  action['next']
						self._print_and_log( 'Executing next action ' + next_action, wf_output )
						self.run_module(next_action)
			except Exception as e:
				traceback.print_exc(file=sys.stderr)
				_logger.error( u'Exception while running command: [%s]', command)
				_logger.error(e)
				wf_out_params = self._merge_maps(wf_out_params, self._exec_code( self.config['error'] ) )
				raise e
			finally:
				wf_out_params.update( self._exec_code( self.config['end'] ) ) 
			return { 'wf_output' : wf_output, 'wf_output_params' : wf_out_params }

	def expand_string(self, string, variables=None):
		"""Expands a string containing variables"""
		if(not variables): variables = self.config['vars']
		processed = {}
		while True:
			pre = string
			for v in variables:
				string = string.replace('$' + v, variables[v])
			if string != pre: # expansion has been completed.
				if processed.has_key(string) : raise Exception('Expansion loop detected: ' + string)
				processed[string] = None
			else:
				break
		if BASH_VAR_PATTERN.match(string): raise Exception('Unexpanded variable(s) found in [{0}]'.format(string));
		return string

	def get_vars(self):
		"""Returns the defined variables"""
		return copy.deepcopy(self.config['vars'])

	def get_expanded_vars(self):
		"""Returns the defined variables expanded"""
		_vars = self.get_vars()
		for v in _vars:
			yield (v, self.expand_string( _vars[v] ) )

	def get_status_log(self):
		"""Returns the internal status log"""
		return copy.deepcopy(self.status_log)

	def process_command(self, action, command):
		"""Processes a command"""
		expanded_command = self.expand_string(command)
		self._set_status_processing(action, expanded_command)
		stdout = [] if self.store_out else None
		stderr = [] if self.store_err else None
		try:
			_logger.info( 'Processing command:[%s]', expanded_command )
			print 'COMMAND', expanded_command
			proc = subprocess.Popen(expanded_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			process_out_params = {}
			out_stream = StreamConsumer( proc.stdout, 'OUT', stdout, process_out_params )
			err_stream = StreamConsumer( proc.stderr, 'ERR', stderr )
			out_stream.start()
			err_stream.start()
			proc.wait()
			out_stream.join()
			err_stream.join()
		except Exception as e:
			traceback.print_exc(file=sys.stderr)
			_logger.error('Error while executing command. %s', e)
		finally:
			self._set_status_done(proc.returncode, stdout, stderr)
		print 'EXIT CODE', proc.returncode
		print 'SYSOUT'   , stdout
		print 'SYSERR'   , stderr
		if proc.returncode != 0 :
			raise Exception( 
			(
				u'Command "{0}"\nFailed with exit code [{1}].\nOUT\n' + ('-'*20) + '\n{2}\n' + ('-'*20) + '\nERR\n' + ('-'*20) + '\n{3}\n' + ('-'*20) + '\n'
			).format(expanded_command, proc.returncode, '\n'.join(stdout), '\n'.join(stderr)) )
		return {
			'stdout' : '' if stdout is None else '\n'.join(stdout),
			'stderr' : '' if stderr is None else '\n'.join(stderr),
			'process_out_params' : process_out_params 
		}

	def start_monitor(self):
		"""Starts all the declared trigger monitors"""
		def _dir_handler(signum, frame):
			_logger.info("Something happened; signal = %s", signum)
			_logger.debug('Configuration: %s', self.config )
		for trigger in self.config['triggers']:
			self._register_monitor( self.expand_string( trigger['dir'] ), _dir_handler )
		# signal.pause()

	def _print_and_log(self, msg, log):
		_logger.info(msg)
		log.append(msg)

	def _verify_input_params(self, config, params):
		if not 'input_params' in config:
			return
		input_params = config['input_params']
		for input_param in input_params:
			if not input_param in params:
				raise Exception( "input param '{0}' must be specified.".format(input_param) )

	def _register_monitor(self, dir, handler):
		"""Registers a handler to monitor a dir"""
		if sys.platform not in ("linux2",): raise Exception('Invalid platform, expected linux2')
		fd = os.open(dir, os.O_RDONLY)
		fcntl.fcntl(fd, fcntl.F_NOTIFY, fcntl.DN_ACCESS|fcntl.DN_MODIFY|fcntl.DN_CREATE)
		signal.signal(signal.SIGIO, handler)

	def _exec_code(self, code):
		"""Executes arbitrary code"""
		func = "def __dyna_func():\n\t" + code
		_context = {}
		_locals  = {}
		for var,val in self.get_expanded_vars():
			_locals['_' + var] = val
		exec func in _locals, _context
		out = _context['__dyna_func']()
		return out if out else {}

	def _set_status_processing(self, action, command):
		"""Sets the processing status as begun"""
		self._processing_action     = action
		self._processing_command    = command
		self._processing_start_time = time()

	def _set_status_done(self, exit_status, out, err):
		"""Sets the processing status as terminated"""
		elapsed_time = time() - self._processing_start_time;
		if len(self.status_log) >= LOG_CACHE_MAX_SIZE: self.status_log.pop()
		self.status_log.append( 
			{ 
			  'action'      : self._processing_action,
			  'command'     : self._processing_command, 
			  'elapsed'     : elapsed_time, 
			  'exit_status' : exit_status, 
			  'out'         : out, 
			  'err'         : err 
			} 
		)

	def _run_sub_module(self, module_name, params):
		"""Runs a nested workflow."""
		try:
			_logger.info( 'Running sub module "%s" with params "%s".', module_name, repr(params) )
			workflow = Workflow( os.path.dirname(self._config_file) + '/' + module_name + '-configuration.json', params )
			# TODO: properties should be copied transparently
			workflow.store_out = self.store_out
			workflow.store_err = self.store_err
			return workflow.run_module()
		except Exception as e:
			raise Exception("Error while running sub module.", e)

	def _merge_maps(self, m1, m2):
		"""Merges two maps which values are lists and returns the merged map."""
		result = m1.copy()
		result.update(m2)
		for k,v in m1.iteritems():
			if m2.has_key(k):
				result[k] = list( set( m1[k] + m2[k] ) )
		return result

class StreamConsumer(threading.Thread):
	"""Consumes and parses a process stream"""
	def __init__(self, stream, stream_name, buff=None, process_out_params=None):
		threading.Thread.__init__(self)
		self.stream = stream
		self.stream_name = stream_name
		self.buff = buff
		self.process_out_params = process_out_params

	def run(self):
		try:
			if self.stream:
				while True:
					line = self.stream.readline().decode('utf8')
					if line != '':
						if self.process_out_params is not None:
							match = PARAM_PATTERN.match(line)
							if match is not None:
								key   = match.group(1)
								value = match.group(2)
								value_list = self.process_out_params.get(key, None)
								if value_list is None:
									value_list = []
									self.process_out_params[key] = value_list
								value_list.append(value)
						emitted = "[" + self.stream_name + "] " + line.rstrip()
						_logger.debug(emitted)
						if self.buff is not None: self.buff.append(emitted)
					else: break
		except Exception as e:
			traceback.print_exc()

def _read_params_list(str):
	"""Reads the workflow parameter list."""
	params = json.loads(str)
	if not type(params) == dict:
		raise Exception('Expected a JSON map as param input: ' + str)
	return params

if __name__ == '__main__':
	if( len(sys.argv) < 2 ): raise Exception('Expected configuration.')
	if( len(sys.argv) == 3 ): 
		params = _read_params_list(sys.argv[2])
	else:
		params = {}
	workflow = Workflow(sys.argv[1], params)
	workflow.run_module()

   # TODO: start monitor
