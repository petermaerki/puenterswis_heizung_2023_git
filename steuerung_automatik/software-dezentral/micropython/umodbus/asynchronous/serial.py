#!/usr/bin/env python3
#
# Copyright (c) 2019, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#

# system packages
from machine import Pin
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time

# custom packages
from .async_utils import hybrid_sleep
from .common import CommonAsyncModbusFunctions, AsyncRequest
from ..common import ModbusException
from .modbus import AsyncModbus
from ..serial import CommonRTUFunctions, RTUServer

# typing not natively supported on MicroPython
from ..typing import Callable, Coroutine
from ..typing import List, Tuple, Optional, Union, Any

US_TO_S = 1 / 1_000_000


class AsyncModbusRTU(AsyncModbus):
    """
    Asynchronous Modbus RTU server

    @see ModbusRTU
    """
    def __init__(self,
                 addr: int,
                 baudrate: int = 9600,
                 data_bits: int = 8,
                 stop_bits: int = 1,
                 parity: Optional[int] = None,
                 pins: Tuple[Union[int, Pin], Union[int, Pin]] = None,
                 ctrl_pin: int = None,
                 uart_id: int = 1):
        super().__init__(
            # set itf to AsyncRTUServer object, addr_list to [addr]
            AsyncRTUServer(uart_id=uart_id,
                           baudrate=baudrate,
                           data_bits=data_bits,
                           stop_bits=stop_bits,
                           parity=parity,
                           pins=pins,
                           ctrl_pin=ctrl_pin),
            [addr]
        )

    async def bind(self) -> None:
        """@see AsyncRTUServer.bind"""

        await self._itf.bind()

    async def serve_forever(self) -> None:
        """@see AsyncRTUServer.serve_forever"""

        await self._itf.serve_forever()

    def server_close(self) -> None:
        """@see AsyncRTUServer.server_close"""

        self._itf.server_close()


class CommonAsyncRTUFunctions(CommonRTUFunctions):
    """
    A mixin for functions common to both the async client and server.
    """

    async def get_request(self,
                          unit_addr_list: Optional[List[int]] = None,
                          timeout: Optional[int] = None) -> \
            Optional[AsyncRequest]:
        """@see RTUServer.get_request"""

        req = await self._uart_read_frame(timeout=timeout)
        req_no_crc = self._parse_request(req=req,
                                         unit_addr_list=unit_addr_list)
        try:
            if req_no_crc is not None:
                return AsyncRequest(interface=self, data=req_no_crc)
        except ModbusException as e:
            await self.send_exception_response(slave_addr=req[0],
                                               function_code=e.function_code,
                                               exception_code=e.exception_code)

    async def _uart_read_frame(self,
                               timeout: Optional[int] = None) -> bytearray:
        """@see RTUServer._uart_read_frame"""
        t1char_ms = max(1, self._t1char//1000)
        # A rtu message is at least 10 chars. We wait for 8 chars and then start reading.
        t8char_ms = max(1, 8*self._t1char//1000)

        # Wait here till the next frame starts
        while not self._uart.any():
            await asyncio.sleep_ms(t8char_ms)

        received_bytes = bytearray()

        last_read_us = time.ticks_us()
        while True:
            # check amount of available characters
            charactes_ready = self._uart.any()
            if charactes_ready:
                # WiPy only
                # r = self._uart.readall()
                r = self._uart.read(charactes_ready)

                if r is not None:
                    # append the new read stuff to the buffer
                    last_read_us = time.ticks_us()
                    received_bytes.extend(r)
                    continue

            silence_us = time.ticks_diff(time.ticks_us(), last_read_us)
            if silence_us > self._inter_frame_delay:
                # The Modbus Specification: The frame is complete after
                # silence of 1.5 times a character.
                # Here we use 'self._inter_frame_delay' which on the save side.
                return received_bytes

            await asyncio.sleep_ms(t1char_ms)


    async def _send(self,
                    modbus_pdu: bytes,
                    slave_addr: int) -> None:
        """@see CommonRTUFunctions._send"""

        await super()._send(modbus_pdu=modbus_pdu,
                            slave_addr=slave_addr)

    async def _post_send(self, sleep_time_us: float) -> None:
        """
        The async variant of CommonRTUFunctions._post_send; used
        to achieve async sleep behaviour while sharing code with
        the synchronous send method.

        @see CommonRTUFunctions._post_send
        """

        await hybrid_sleep(sleep_time_us)
        if self._ctrlPin:
            self._ctrlPin.off()


class AsyncRTUServer(CommonAsyncRTUFunctions, RTUServer):
    """Asynchronous Modbus Serial host"""

    def __init__(self,
                 uart_id: int = 1,
                 baudrate: int = 9600,
                 data_bits: int = 8,
                 stop_bits: int = 1,
                 parity=None,
                 pins: Tuple[Union[int, Pin], Union[int, Pin]] = None,
                 ctrl_pin: int = None):
        """
        Setup asynchronous Serial/RTU Modbus

        @see RTUServer
        """
        super().__init__(uart_id=uart_id,
                         baudrate=baudrate,
                         data_bits=data_bits,
                         stop_bits=stop_bits,
                         parity=parity,
                         pins=pins,
                         ctrl_pin=ctrl_pin)

        self._task = None
        self.event = asyncio.Event()
        self.req_handler: Callable[[Optional[AsyncRequest]],
                                   Coroutine[Any, Any, bool]] = None

    async def bind(self) -> None:
        """
        Starts serving the asynchronous server on the specified host and port
        specified in the constructor.
        """

        self._task = asyncio.create_task(self._uart_bind())

    async def _uart_bind(self) -> None:
        """Starts processing requests continuously. Must be run as a task."""

        if self.req_handler is None:
            raise ValueError("No req_handler detected. "
                             "This may be because this class object was "
                             "instantiated manually, and not as part of "
                             "a Modbus server.")
        while not self.event.is_set():
            # form request and pass to process in infinite loop
            await self.req_handler()

    async def serve_forever(self) -> None:
        """Waits for the server to close."""

        if self._task is None:
            raise ValueError("Error: must call bind() first")
        await self._task

    def server_close(self) -> None:
        """Stops a running server, i.e. stops reading from UART."""

        self.event.set()

    async def send_response(self,
                            slave_addr: int,
                            function_code: int,
                            request_register_addr: int,
                            request_register_qty: int,
                            request_data: list,
                            values: Optional[list] = None,
                            signed: bool = True,
                            request: Optional[AsyncRequest] = None) -> None:
        """
        Asynchronous equivalent to Serial.send_response
        @see RTUServer.send_response for common (leading) parameters

        :param      request:     Ignored; kept for compatibility
                                 with AsyncRequest
        :type       request:     AsyncRequest, optional
        """

        #print("async RTU: calling send_response()")
        task = super().send_response(slave_addr=slave_addr,
                                     function_code=function_code,
                                     request_register_addr=request_register_addr,  # noqa: E501
                                     request_register_qty=request_register_qty,
                                     request_data=request_data,
                                     values=values,
                                     signed=signed)
        #print("async RTU: send_response() called, task is:", task)
        if task is not None:
            await task

    async def send_exception_response(self,
                                      slave_addr: int,
                                      function_code: int,
                                      exception_code: int,
                                      request: Optional[AsyncRequest] = None) \
            -> None:
        """
        Asynchronous equivalent to Serial.send_exception_response
        @see RTUServer.send_exception_response for common (leading) parameters

        :param      request:     Ignored; kept for compatibility
                                 with AsyncRequest
        :type       request:     AsyncRequest, optional
        """

        #print("async RTU: calling send_exception_response()")
        task = super().send_exception_response(slave_addr=slave_addr,
                                               function_code=function_code,
                                               exception_code=exception_code)
        #print("async RTU: called send_exception_response(), task is:", task)
        if task is not None:
            await task

    def set_params(self,
                   addr_list: Optional[List[int]],
                   req_handler: Callable[[Optional[AsyncRequest]],
                                         Coroutine[Any, Any, bool]]) -> None:
        """
        Used to set parameters such as the unit address list
        and the processing handler.

        :param      addr_list:      The unit address list, currently ignored
        :type       addr_list:      List[int], optional
        :param      req_handler:    A callback that is responsible for parsing
                                    individual requests from a Modbus client
        :type       req_handler:    (Optional[AsyncRequest]) ->
                                        (() -> bool, async)
        """

        self.req_handler = req_handler


class AsyncSerial(CommonAsyncModbusFunctions, CommonAsyncRTUFunctions):
    """Asynchronous Modbus Serial client"""

    def __init__(self,
                 uart_id: int = 1,
                 baudrate: int = 9600,
                 data_bits: int = 8,
                 stop_bits: int = 1,
                 parity=None,
                 pins: Tuple[Union[int, Pin], Union[int, Pin]] = None,
                 ctrl_pin: int = None,
                 read_timeout: int = None,
                 **extra_args):
        """
        Setup asynchronous Serial/RTU Modbus

        @see Serial
        """
        super().__init__(uart_id=uart_id,
                         baudrate=baudrate,
                         data_bits=data_bits,
                         stop_bits=stop_bits,
                         parity=parity,
                         pins=pins,
                         ctrl_pin=ctrl_pin,
                         read_timeout=read_timeout,
                         **extra_args)

        self._uart_reader = asyncio.StreamReader(self._uart)
        self._uart_writer = asyncio.StreamWriter(self._uart, {})

    async def _uart_read(self) -> bytearray:
        """@see Serial._uart_read"""

        response = bytearray()
        # number of repetitions = <wait_time_in_ms> // <sleep_per_repetition>
        repetitions = self._uart_read_timeout // self._inter_frame_delay

        for _ in range(1, repetitions):
            if self._uart.any():
                # WiPy only
                # response.extend(await self._uart_reader.readall())
                response.extend(await self._uart_reader.read())

                # variable length function codes may require multiple reads
                if self._exit_read(response):
                    break

            # wait for the maximum time between two frames
            await hybrid_sleep(self._inter_frame_delay)

        return response

    async def _send_receive(self,
                            slave_addr: int,
                            modbus_pdu: bytes,
                            count: bool) -> bytes:
        """@see Serial._send_receive"""

        # flush the Rx FIFO
        await self._uart_reader.read()
        await self._send(modbus_pdu=modbus_pdu, slave_addr=slave_addr)

        response = await self._uart_read()
        return self._validate_resp_hdr(response=response,
                                       slave_addr=slave_addr,
                                       function_code=modbus_pdu[0],
                                       count=count)
