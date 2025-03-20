import time
import subprocess
import os
import pty

class ReplProcess:
    def __init__(self):
        self.log('init called')
        self.command = ['python']
        self.paused_for_input = False
        self.shutting_down = False

        # Open pseudo-terminal pairs for communication
        self.code_master, self.code_slave = pty.openpty()
        self.input_master, self.input_slave = pty.openpty()
        self.output_master, self.output_slave = pty.openpty()
        self.error_master, self.error_slave = pty.openpty()

        # Spawn the subprocess with the pseudo-terminals
        self.process = subprocess.Popen(
            self.command, 
            pass_fds=[self.input_slave], 
            stdin=self.code_slave, 
            stdout=self.output_slave, 
            stderr=self.error_slave,  
            close_fds=True, 
            text=True
        )

        # Get file descriptors for stdin, stdout, and stderr
        self.stdin_fd = os.fdopen(self.code_master, 'w')
        self.input_fd = os.fdopen(self.input_master, 'w')
        self.stdout_fd = os.fdopen(self.output_master, 'r')
        self.stderr_fd = os.fdopen(self.error_master, 'r')

        self.count = 0
        self.log(f"__START__STREAM__ [{self.count}]")
        self.stdin_fd.write(
            """
#define important functions
import json as _json
def names():
    return _json.dumps([item for item in globals() if not item.startswith("_")], indent=None)

import sys as _sys
def _eprint(*args, **kwargs):
    print(*args, file=_sys.stderr, **kwargs)

def _oeprint(*args, **kwargs):
    print(*args, flush=True, **kwargs)
    _eprint(*args, flush=True, **kwargs)

#set input fd
import os as _os
"""
            + f"_input_fd=_os.fdopen({self.input_slave}, 'r')"
            + """
def input(prompt):
    global _input_fd
    print(prompt.strip())
    _oeprint("__PAUSE"+"_FOR"+"_INPUT__")
    return _input_fd.readline().rstrip("\\n") 

def exit(*args, **kwargs):
    _oeprint("__SHUT"+"DOWN__")
    _sys.exit(*args, **kwargs)

"""
        )
        self.stdin_fd.write(f'_oeprint("__END"+"_OF"+"_STREAM__ [{self.count}]") #__SILENT__\n')
        self.stdin_fd.flush()

        # Wait for the initialization to complete
        time.sleep(0.1)
        result = self._read_output()
        result = result + self._read_error()
        print("Ready.")

    def get_names(self):
        self.count += 1
        self.log(f"__START__STREAM__ [{self.count}]")
        self.stdin_fd.write(f'print(names()) #__SILENT__\n')
        self.stdin_fd.write(f'_oeprint("__END"+"_OF"+"_STREAM__ [{self.count}]") #__SILENT__\n')
        self.stdin_fd.flush()
        output, errors = self._read_output(), self._read_error()
        return output.strip(), errors

    def uninit(self):
        self.log(f"uninit() called")
        self.shutting_down = True
        # Tell process to shut itself down
        self.stdin_fd.write(f'exit()\n')
        self.stdin_fd.flush()
        self._read_output()

        # Close the file descriptors
        self.stdin_fd.close()
        self.stdout_fd.close()
        self.stderr_fd.close()
        self.input_fd.close()

        # Wait for the process to complete
        self.process.communicate()

    def send_code(self, code):
        self.count += 1
        self.log(f"__START__STREAM__ [{self.count}]")
        self.stdin_fd.write(code.replace("\\n", "\n") + '\n')
        self.stdin_fd.write(f'\n_oeprint("__END"+"_OF"+"_STREAM__ [{self.count}]") #__SILENT__\n')
        self.stdin_fd.flush()
        return self._read_output().strip(), self._read_error().strip()

    def send_input(self, message):
        self.log(message)
        self.input_fd.write(message + "\n")
        self.input_fd.flush()
        return self._read_output().strip(), self._read_error().strip()

    def _read_stream(self, fd):
        output = fd.readline()
        self.log(output, end="")
        result = ""
        while True:
            if  "__END_OF_STREAM__" in output:
                break
            if "__PAUSE_FOR_INPUT__" in output:
                self.paused_for_input = True
                break
            elif "__SHUTDOWN__" in output:
                self.shutting_down = True
                break
            elif "__SILENT__" in output:
                pass
            elif output.strip() != ">>>":
                result += output
            output = fd.readline()
            self.log(output, end="")
        return result
    
    def _read_output(self):
        return self._read_stream(self.stdout_fd)
    
    def _read_error(self):
        return self._read_stream(self.stderr_fd)
    
    def log(self, *args, **kwargs):
        """Log messages to a file."""
        with open("stream.log", "a") as log_file:
            print(*args, file=log_file, **kwargs)

# Example usage
if __name__ == "__main__":
    repl = ReplProcess()
    try:
        while not repl.shutting_down:
            if repl.paused_for_input:
                message = input("Input required: ")
                repl.paused_for_input = False
                out, err = repl.send_input(message)
                print(out, err)
            else:
                code = input("Code required:")
                out, err = repl.send_code(code)
                print(out, err)
    except KeyboardInterrupt:
        repl.uninit()
    print("Successfully shut down")
