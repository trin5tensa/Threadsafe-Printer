"""threadsafe_printer.py"""
import asyncio
import queue
import threading
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass
from types import TracebackType
from typing import Type


@dataclass
class SafePrint(AbstractContextManager):
    _time_0 = time.perf_counter()
    _print_q = queue.Queue()
    _print_thread: threading.Thread | None = None
    
    def __enter__(self):
        """ Run the safeprint consumer method in a print thread.
        
        Returns:
            Thw safeprint producer method. (a.k.a. the runtime context)
        """
        self._print_thread = threading.Thread(target=self._safeprint_consumer, name='Print Thread')
        self._print_thread.start()
        return self._safeprint
    
    def __exit__(self, __exc_type: Type[BaseException] | None, __exc_value: BaseException | None,
                 __traceback: TracebackType | None) -> bool | None:
        """ Close the print and join the print thread.
        
        Args:
            None or the exception raised during the execution of the safeprint producer method.
            __exc_type:
            __exc_value:
            __traceback:

        Returns:
            False to indicate that any exception raised has not been handled in this method.
        """
        self._print_q.put(None)
        self._print_thread.join()
        return False
    
    def _safeprint(self, msg: str, timestamp: bool = True, reset: bool = False):
        """Put a string into the print queue.
        
        'None' is a special msg. It is not printed but will close the queue and this context manager.
        
        The exclusive thread and a threadsafe print queue ensure race free printing.
        This is the producer in the print queue's producer/consumer pattern.
        It runs in the same thread as the calling function
        
        Args:
            msg: The message to be printed.
            timestamp: Print a timestamp (Default = True).
            reset: Reset the time to zero (Default = False).
        """
        if reset:
            self._time_0 = time.perf_counter()
        if timestamp:
            self._print_q.put(f'{self._timestamp()} --- {msg}')
        else:
            self._print_q.put(msg)
   
    def _safeprint_consumer(self):
        """Get strings from the print queue and print them on stdout.
    
        The print statement is not threadsafe, so it must run in its own thread.
        This is the consumer in the print queue's producer/consumer pattern.
        """
        print(f'{self._timestamp()}: The Safeprinter is open for output.')
        while True:
            msg = self._print_q.get()
            
            # Exit function when any producer function places 'None' into the queue otherwise print falsy strings.
            if msg is not None:
                print(msg)
            else:
                break
        print(f'{self._timestamp()}: The Safeprinter has closed.')
    
    def _timestamp(self) -> str:
        """Create a timestamp with useful status information.
    
        This is a support function for the print queue producers. It runs in the same thread as the calling function.
        Consequently, the returned data does not cross between threads.
    
        Returns:
            timestamp
        """
        secs = time.perf_counter() - self._time_0
        try:
            asyncio.get_running_loop()
        except RuntimeError as exc:
            if exc.args[0] == 'no running event loop':
                loop_name = 'no asyncio loop'
            else:
                raise
        else:
            loop_name = 'an asyncio loop'
        return f'{secs:.3f}s In {threading.current_thread().name} of {threading.active_count()} with {loop_name}'
