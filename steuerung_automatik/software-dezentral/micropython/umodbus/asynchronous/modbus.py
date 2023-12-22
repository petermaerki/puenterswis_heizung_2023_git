#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Modbus register abstraction class

Used to add, remove, set and get values or states of a register or coil.
Additional helper properties and functions like getters for changed registers
are available as well.

This class is inherited by the Modbus client implementations
:py:class:`umodbus.serial.ModbusRTU` and :py:class:`umodbus.tcp.ModbusTCP`
"""

# system packages
from ..typing import List, Optional, Union

# custom packages
from .common import AsyncRequest
from ..modbus import Modbus


class AsyncModbus(Modbus):
    """Modbus register abstraction."""

    def __init__(self,
                 # in quotes because of circular import errors
                 itf: Union["AsyncTCPServer", "AsyncRTUServer"],  # noqa: F821
                 addr_list: Optional[List[int]] = None):
        super().__init__(itf, addr_list)
        self._itf.set_params(addr_list=addr_list, req_handler=self.process)

    async def process(self, request: Optional[AsyncRequest] = None) -> None:
        """@see Modbus.process"""

        result = super().process(request)
        if result is None:
            return
        # Result of get_request() if request is None, or either of the *tasks*:
        # - AsyncRequest.send_exception() (invalid function code)
        # - self._process_read_access() and self._process_write_access():
        #   - AsyncRequest.send_response()
        #   - AsyncRequest.send_exception()
        # - None: implies no data received
        request = await result
        if request is None:
            return

        # below code should only execute if no request was passed, i.e. if
        # process() was called manually - so that get_request() returns an
        # AsyncRequest
        sub_result = super().process(request)
        if sub_result is not None:
            await sub_result

    async def _process_read_access(self,
                                   request: AsyncRequest,
                                   reg_type: str) -> None:
        """@see Modbus._process_read_access"""

        task = super()._process_read_access(request, reg_type)
        #print("async process_read_access task = ", task)
        if task is not None:
            await task

    async def _process_write_access(self,
                                    request: AsyncRequest,
                                    reg_type: str) -> None:
        """@see Modbus._process_write_access"""

        task = super()._process_write_access(request, reg_type)
        #print("async process_write_access task = ", task)
        if task is not None:
            await task
